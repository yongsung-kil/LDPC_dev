"""RowStack 흐름: uncor 모으기, 찾은 매트릭스 먼저 시험, 탐색 규칙 2판의 row, parent, round 구조, 보고.

설계: 5_DAO/_pm/tasks/20261021_uncor별_row누적_탐색/ (1판 설계 4.6, 4.7, 4.10절과 탐색 규칙 2판 3절).
실행: mpiexec -n N python RowStack_Main.py (설정은 RowStack_Config.CONFIG). mpiexec 없이 python으로 직접 돌리면 rank 1개다.
모든 rank가 같은 제어 흐름을 돌고, 선별은 root가 gather로 모아 bcast한다. 파일은 root만 쓴다 (rank 로그와 시험한
매트릭스 파일은 rank마다 자기 것만 쓴다). 평가기(evaluate(rows, seed, max_iter), empty_result(seed))와 병렬 통신은
주입받으므로 rank 1개 가짜 평가기로 검사한다.

로그의 자리 표기 (뜻은 RowStack_Report.format_legend가 log.txt와 rank 로그 머리에 적는다):
  Row r/R          r번째 row를 붙이는 단계 (R = MAX_ROWS)
  parent p/P       직전 row까지 확정된 매트릭스(부모) P개 가운데 p번째. row 1의 부모는 받은 프레임 하나다
  round k/K        같은 부모에 rank마다 후보 n개씩 시험하는 묶음. 개선이 없으면 최대 K번 반복한다
  gen #i, mut #i   이 rank가 이 round에서 i번째로 시험한 후보 (gen은 새 row 추가, mut은 값 변이)
로그 구역 (DAO의 Write_Log_Separator 꼴을 따른다. 구역 머리줄 앞에 빈 줄, 머리줄에만 시각):
  ==================== [Uncor i/N  seed s @ 시각] ====================    uncor 배너 (log.txt와 rank 로그)
  ---------- [Row r/R  iterations I] ----------                           row 머리줄 (log.txt)
  ---------- [Row r/R  gen  parent p/P  round k/K]  ... ----------        round 머리줄 (rank 로그)
  ---------- [Result  seed s @ 시각] ----------                            uncor 결과 (log.txt)
"""
import os
import shutil
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

import RowStack_Config
from RowStack_Config import CONFIG, RowStackConfig
from RowStack_Evaluate import CandidateResult, UncorDecoder, candidate_sort_key, is_improvement
from RowStack_Matrix import (MatrixTemplate, StackedRow, generate_random_row_values, mutate_matrix_values,
                             new_row_csw_threshold, save_stacked_matrix)
from RowStack_Parallel import MpiParallel, round_robin_share
from RowStack_Report import (HISTORY_COLUMNS, SUMMARY_COLUMNS, CsvAppender, FileLogger, RootLogger, clock,
                             format_legend, format_settings_header, kv, section_line, write_found_matrices)
from RowStack_Uncor import failing_seeds, read_uncor_files, uncor_info_from_config, uncor_info_mismatch, write_uncor_files
from src import channel as chan
from src.decoder import BaseDecoder
from src.llr_matrix import LLRMatrix
from src.pcm import QCCode

KIND_CODE = {"gen": 1, "mut": 2}
COLLECTED_UNCORS_DIR_NAME = "collected_uncors"
PER_UNCOR_DIR_NAME = "per_uncor"
NO_THRESHOLD_NOTE = "no reachable CSW threshold"
NO_IMPROVEMENT_NOTE = "no improving candidate"
MAX_ROWS_NOTE = "max rows reached"
RECEIVED_FRAME_ORIGIN = "(received frame)"
DESCRIBE_WIDTH = 66               # 후보 결과 토막을 이 너비로 맞춰 뒤의 시간과 파일 이름 열이 서게 한다


@dataclass
class FoundMatrix:
    rows: list                      # StackedRow 목록
    matrix_file: str                # 세션 폴더 기준 상대 경로
    origin_seed: int                # 처음 고친 seed
    fixed_seeds: list = field(default_factory=list)


@dataclass
class MatrixCandidate:
    """매트릭스 후보: 지금까지 고정된 row들과 그 성능, 어디서 왔는지."""
    rows: list
    result: CandidateResult
    origin: str                     # 예: "row 2 gen parent 1 round 1 rank0 #15", 빈 매트릭스는 RECEIVED_FRAME_ORIGIN

    def key(self) -> tuple:
        return candidate_sort_key(self.result)


@dataclass
class SearchOutcome:
    result: str                     # "success" 또는 "fail"
    rows: list                      # 성공이면 고치는 row들, 실패면 마지막에 남은(kept) 매트릭스 가운데 순위가 가장 앞선 것의 row들
    final: Optional[CandidateResult]
    fail_reason: str                # "", MAX_ROWS_NOTE, NO_THRESHOLD_NOTE, NO_IMPROVEMENT_NOTE


def describe_result(result: CandidateResult) -> str:
    """후보 결과 한 토막: min_err, 그 iteration과 CSW, 복호 성공 여부 (성공이면 고친 iteration도)."""
    text = (f"min_err {result.min_err} at iteration {result.min_err_iteration} (csw {result.csw_at_min_err}), "
            f"decoding {'success' if result.success else 'fail'}")
    if result.success:
        text += f", corrected at iteration {result.success_iteration}"
    return text


def describe_candidate(candidate: MatrixCandidate) -> str:
    if not candidate.rows:
        return f"{RECEIVED_FRAME_ORIGIN} min_err {candidate.result.min_err} (csw {candidate.result.initial_csw})"
    return f"rows {len(candidate.rows)} from {candidate.origin}: {describe_result(candidate.result)}"


class RowStackSession:
    """uncor 하나를 다루는 흐름. root만 history.csv와 로그를 쓴다."""

    def __init__(self, config: RowStackConfig, parallel, evaluator, template: MatrixTemplate,
                 session_dir: Optional[str], logger: Optional[RootLogger],
                 result_logger: Optional[FileLogger] = None, rank_logger: Optional[FileLogger] = None,
                 tested_matrix_dir: Optional[str] = None, total_uncors: int = 1):
        """evaluator는 evaluate(rows, seed, max_iter)와 empty_result(seed)를 가진 객체다.
        logger는 root의 상세 로그(log.txt), result_logger는 root의 중요 결과(result.txt),
        rank_logger는 이 rank의 후보별 상세(rank_logs/rank_N.txt), tested_matrix_dir는 이 rank가 시험한 후보 매트릭스
        파일을 두는 폴더(tested_matrices/rank_N)다. 없으면 그 기록은 생략한다. total_uncors는 진행도 표시용이다."""
        self.config = config
        self.parallel = parallel
        self.evaluator = evaluator
        self.template = template
        self.session_dir = session_dir
        self.logger = logger
        self.result_logger = result_logger
        self.rank_logger = rank_logger
        self.tested_matrix_dir = tested_matrix_dir
        self.total_uncors = total_uncors
        self.started = time.perf_counter()
        if tested_matrix_dir:
            os.makedirs(tested_matrix_dir, exist_ok=True)
        self.is_root = parallel.rank == 0
        self.history = None
        if self.is_root and session_dir:
            self.history = CsvAppender(os.path.join(session_dir, "history.csv"), HISTORY_COLUMNS)

    # ----- 기록 -----
    def _log(self, text: str) -> None:
        """log.txt (root만). 줄 그대로 쓴다. 시각은 구역 머리줄과 round 줄에 넣는다."""
        if self.is_root and self.logger is not None:
            self.logger.raw(text)

    def _result(self, text: str) -> None:
        if self.is_root and self.result_logger is not None:
            self.result_logger.raw(text)

    def _rank_log(self, text: str) -> None:
        if self.rank_logger is not None:
            self.rank_logger.raw(text)

    def _record(self, row: dict) -> None:
        if self.history is not None:
            self.history.append(row)

    def _elapsed_minutes(self) -> float:
        return (time.perf_counter() - self.started) / 60

    def begin_uncor(self, uncor_idx: int, seed: int) -> None:
        """uncor 배너를 log.txt와 rank 로그에 쓴다."""
        frame = self.evaluator.empty_result(seed)
        title = section_line(f"Uncor {uncor_idx + 1}/{self.total_uncors}  seed {seed}", heavy=True)
        detail = kv("received frame", f"{frame.min_err} error bits, csw {frame.initial_csw}")
        for write in (self._log, self._rank_log):
            write("")
            write(title)
            write(detail)

    # ----- 공용 -----
    def candidate_rng(self, uncor_idx: int, attempt: int, row_no: int, kind: str, parent_no: int,
                      round_no: int) -> np.random.Generator:
        """후보 난수의 뿌리: (RANDOM_SEED, rank, uncor 번호, attempt, row 번호, gen/mut, parent 번호, round 번호)."""
        return np.random.default_rng([self.config.RANDOM_SEED, self.parallel.rank, uncor_idx, attempt, row_no,
                                      KIND_CODE[kind], parent_no, round_no])

    def iteration_budget(self, num_rows: int) -> int:
        return self.config.iteration_budget(num_rows)

    # ----- round -----
    def _run_round(self, parent: MatrixCandidate, parent_no: int, num_parents: int, kind: str, threshold: int,
                   takeover: Optional[int], budget: int, uncor_idx: int, attempt: int, row_no: int, seed: int,
                   round_no: int, max_rounds: int, keep: int) -> list:
        """round 하나: rank마다 후보를 만들어 시험하고, 부모보다 나아진 후보를 모든 rank에서 모아 순위 상위 keep개를
        돌려준다 (MatrixCandidate 목록, 없으면 빈 목록). history.csv에 round 한 줄을 적는다."""
        started = time.perf_counter()
        config = self.config
        count = config.CANDIDATES_PER_RANK_PER_ROUND if kind == "gen" else config.MUTANTS_PER_RANK_PER_ROUND
        rng = self.candidate_rng(uncor_idx, attempt, row_no, kind, parent_no, round_no)
        position = f"{kind:<3}  parent {parent_no}/{num_parents}  round {round_no}/{max_rounds}"
        row_label = f"Row {row_no}/{config.MAX_ROWS}"
        if config.MAX_MATRIX_ATTEMPTS_PER_UNCOR > 1:
            row_label = f"Attempt {attempt}/{config.MAX_MATRIX_ATTEMPTS_PER_UNCOR}  " + row_label
        self._rank_log("")
        self._rank_log(f"---------- [{row_label}  {position}]  threshold {threshold}, iterations {budget}  @ {clock()} ----------")
        self._rank_log(f"  parent : {describe_candidate(parent)}")
        self._log(f"  [{position}]  threshold {threshold}  @ {clock()}")
        local = []   # (순위 키, 후보 번호, rows, result)
        for index in range(1, count + 1):
            candidate_started = time.perf_counter()
            if kind == "gen":
                rows = parent.rows + [StackedRow(generate_random_row_values(self.template, rng), threshold)]
            else:
                rows = mutate_matrix_values(parent.rows, self.template, rng, config.MUTATION_NUM_ELEMENTS,
                                            config.MUTATION_RANGE)
            result = self.evaluator.evaluate(rows, seed, budget)
            file_note = ""
            if self.tested_matrix_dir:
                file_name = (f"LLR_MATRIX_{self.template.mode}_seed{seed}_attempt{attempt}_row{row_no}"
                             f"_parent{parent_no}_round{round_no}_{kind}{index}.txt")
                save_stacked_matrix(self.template, rows, os.path.join(self.tested_matrix_dir, file_name), max_iter=budget)
                file_note = f"   file={file_name}"
            improved = is_improvement(result, parent.result)
            text = describe_result(result) + ("   improved" if improved else "")
            self._rank_log(f"  {kind} #{index:<2}: {text:<{DESCRIBE_WIDTH + 11}} ({time.perf_counter() - candidate_started:.1f}s){file_note}")
            if improved:
                local.append((candidate_sort_key(result), index, rows, result))
        local.sort(key=lambda item: (item[0], item[1]))
        # rank마다 개선된 변형 수와 그 가운데 상위 keep개만 보낸다 (전체 상위 keep개를 고르는 데 그 이상은 필요 없다)
        payload = (len(local), [(key, self.parallel.rank, index, rows, result) for key, index, rows, result in local[:keep]])
        gathered = self.parallel.gather_to_root(payload)
        decision = None
        if self.is_root:
            merged = sorted((item for _, part in gathered for item in part), key=lambda item: (item[0], item[1], item[2]))
            chosen = [MatrixCandidate(rows, result,
                                      f"row {row_no} {kind} parent {parent_no} round {round_no} rank{rank} #{index}")
                      for key, rank, index, rows, result in merged[:keep]]
            decision = (chosen, sum(count_ for count_, _ in gathered),
                        [(rank, index) for key, rank, index, rows, result in merged[:1]])
        chosen, num_improved, best_ids = self.parallel.bcast_from_root(decision)
        elapsed = time.perf_counter() - started
        total_tried = count * self.parallel.size

        record = {"seed": seed, "attempt": attempt, "row": row_no, "kind": kind, "parent": parent_no, "round": round_no,
                  "threshold": threshold, "takeover_iteration": takeover, "iterations": budget,
                  "parent_min_err": parent.result.min_err, "num_improved": num_improved, "elapsed_sec": elapsed}
        if chosen:
            best = chosen[0]
            best_rank, best_index = best_ids[0]
            record.update({"best_rank": best_rank, "best_candidate": best_index, "min_err": best.result.min_err,
                           "min_err_iteration": best.result.min_err_iteration, "csw_at_min_err": best.result.csw_at_min_err,
                           "decoding": "success" if best.result.success else "fail",
                           "corrected_iteration": best.result.success_iteration})
            self._log(f"      improved {num_improved}/{total_tried}   best rank{best_rank} #{best_index}: "
                      f"{describe_result(best.result)}   ({elapsed:.1f}s)")
            self._rank_log(f"  => this rank {len(local)}/{count} improved | all ranks {num_improved} improved | "
                           f"best rank{best_rank} #{best_index}: {describe_result(best.result)}")
        else:
            self._log(f"      improved 0/{total_tried}   parent min_err {parent.result.min_err} kept   ({elapsed:.1f}s)")
            self._rank_log(f"  => this rank 0/{count} improved | all ranks 0 improved | parent kept")
        self._record(record)
        return chosen

    def _run_rounds(self, parent: MatrixCandidate, parent_no: int, num_parents: int, kind: str,
                    threshold: int, takeover: Optional[int], budget: int, uncor_idx: int, attempt: int, row_no: int,
                    seed: int, max_rounds: int, keep: int) -> list:
        """같은 부모에 대해 개선된 후보가 나올 때까지 round를 최대 max_rounds번 돈다."""
        for round_no in range(1, max_rounds + 1):
            chosen = self._run_round(parent, parent_no, num_parents, kind, threshold, takeover, budget, uncor_idx,
                                     attempt, row_no, seed, round_no, max_rounds, keep)
            if chosen:
                return chosen
        return []

    # ----- 탐색 -----
    def search_matrix_for_uncor(self, uncor_idx: int, seed: int) -> SearchOutcome:
        """row마다: 부모(parent)마다 gen round를 돌려 개선된 후보를 모으고 상위 keep개를 남긴(kept) 뒤, 남긴 것마다
        mut round를 돈다. 남긴 것은 다음 row의 부모가 된다."""
        config = self.config
        keep = config.NUM_PARENTS_TO_KEEP
        last_best, fail_reason = None, MAX_ROWS_NOTE
        for attempt in range(1, config.MAX_MATRIX_ATTEMPTS_PER_UNCOR + 1):
            parents = [MatrixCandidate([], self.evaluator.empty_result(seed), RECEIVED_FRAME_ORIGIN)]
            early_reason = None
            attempt_label = f"Attempt {attempt}/{config.MAX_MATRIX_ATTEMPTS_PER_UNCOR}  " if config.MAX_MATRIX_ATTEMPTS_PER_UNCOR > 1 else ""
            for row_no in range(1, config.MAX_ROWS + 1):
                budget = self.iteration_budget(row_no)
                self._log("")
                self._log(section_line(f"{attempt_label}Row {row_no}/{config.MAX_ROWS}  iterations {budget}",
                                       heavy=False, with_time=False))
                pool, threshold_failures = [], 0
                num_parents = len(parents)
                for parent_no, parent in enumerate(parents, start=1):
                    if row_no == 1:
                        threshold, takeover = -1, None
                    else:
                        prev_threshold = None if parent.rows[-1].csw == -1 else parent.rows[-1].csw
                        found = new_row_csw_threshold(parent.result.csw_per_iter, prev_threshold,
                                                      parent.result.initial_csw, config.CSW_MARGIN_ABOVE_MIN, budget)
                        if found is None:
                            threshold_failures += 1
                            min_csw = int(np.min(parent.result.csw_per_iter)) if len(parent.result.csw_per_iter) else None
                            self._record({"seed": seed, "attempt": attempt, "row": row_no, "kind": "gen",
                                          "parent": parent_no, "round": 0, "iterations": budget,
                                          "parent_min_err": parent.result.min_err, "note": NO_THRESHOLD_NOTE})
                            self._log(f"  [gen  parent {parent_no}/{num_parents}]  {NO_THRESHOLD_NOTE}")
                            self._log(f"      parent min_err {parent.result.min_err}, min csw {min_csw}, "
                                      f"previous threshold {parent.rows[-1].csw}, initial csw {parent.result.initial_csw}")
                            self._rank_log("")
                            self._rank_log(f"  (row {row_no} parent {parent_no}: {NO_THRESHOLD_NOTE})")
                            continue
                        threshold, takeover = found
                    pool.extend(self._run_rounds(parent, parent_no, num_parents, "gen", threshold, takeover, budget,
                                                 uncor_idx, attempt, row_no, seed, config.MAX_GEN_ROUNDS_PER_ROW, keep))
                if not pool:
                    early_reason = NO_THRESHOLD_NOTE if threshold_failures == len(parents) else NO_IMPROVEMENT_NOTE
                    self._log(f"  [attempt {attempt} ends]  {early_reason} at row {row_no}")
                    break
                kept = sorted(pool, key=lambda candidate: candidate.key())[:keep]

                if config.MUTANTS_PER_RANK_PER_ROUND > 0:
                    for parent_no, candidate in enumerate(kept, start=1):
                        improved = self._run_rounds(candidate, parent_no, len(kept), "mut", candidate.rows[-1].csw,
                                                    None, self.iteration_budget(len(candidate.rows)), uncor_idx, attempt,
                                                    row_no, seed, config.MAX_MUT_ROUNDS_PER_ROW, 1)
                        if improved:
                            kept[parent_no - 1] = improved[0]

                successes = [candidate for candidate in kept if candidate.result.success]
                next_note = f"  parents for row {row_no + 1}" if not successes and row_no < config.MAX_ROWS else ""
                self._log(f"  [kept {len(kept)}]{next_note}")
                for number, candidate in enumerate(kept, start=1):
                    self._log(f"      [{number}] {describe_candidate(candidate)}")
                parents = kept
                if successes:
                    best = min(successes, key=lambda candidate: candidate.key())
                    return SearchOutcome("success", best.rows, best.result, "")
            with_rows = [candidate for candidate in parents if candidate.rows]
            if with_rows:
                last_best = min(with_rows, key=lambda candidate: candidate.key())
            fail_reason = early_reason if early_reason is not None else MAX_ROWS_NOTE
        if last_best is None:
            return SearchOutcome("fail", [], None, fail_reason)
        return SearchOutcome("fail", last_best.rows, last_best.result, fail_reason)

    # ----- 찾은 매트릭스 먼저 시험 -----
    def try_found_matrices(self, found: list, seed: int) -> Optional[int]:
        """고친 uncor 수가 많은 순(같으면 먼저 찾은 순)으로 나눠 시험하고, 고친 것 가운데 가장 앞선 것의 found index."""
        if not found:
            return None
        order = sorted(range(len(found)), key=lambda i: (-len(found[i].fixed_seeds), i))
        local_hits = []
        for position in round_robin_share(len(order), self.parallel.rank, self.parallel.size):
            rows = found[order[position]].rows
            if self.evaluator.evaluate(rows, seed, self.iteration_budget(len(rows))).success:
                local_hits.append(position)
        gathered = self.parallel.gather_to_root(min(local_hits) if local_hits else None)
        chosen = None
        if self.is_root:
            positions = [position for position in gathered if position is not None]
            chosen = min(positions) if positions else None
        chosen = self.parallel.bcast_from_root(chosen)
        return None if chosen is None else order[chosen]

    # ----- uncor 하나 -----
    def _matrix_relative_path(self, seed: int) -> str:
        return os.path.join(PER_UNCOR_DIR_NAME, f"seed_{seed}", f"LLR_MATRIX_{self.template.mode}_uncor_{seed}.txt")

    def _finish_uncor(self, uncor_idx: int, seed: int, verdict: str, fields: list, short_detail: str, elapsed: float) -> None:
        """uncor 결과를 log.txt(구역)와 result.txt(한 줄)에 쓴다."""
        progress = f"progress {uncor_idx + 1}/{self.total_uncors} uncors, {self._elapsed_minutes():.1f} min"
        self._log("")
        self._log(section_line(f"Result  seed {seed}", heavy=False))
        self._log(kv("result", verdict, width=9))
        for label, value in fields:
            self._log(kv(label, value, width=9))
        self._log(kv("time", f"{elapsed:.0f}s   {progress}", width=9))
        self._result(f"  [{uncor_idx + 1}/{self.total_uncors}] seed {seed:<7} {verdict:<8} {short_detail:<{DESCRIBE_WIDTH}} "
                     f"{elapsed:>5.0f}s  @ {clock()}")

    def run_one_uncor(self, uncor_idx: int, seed: int, found: list) -> dict:
        """summary.csv 한 줄 dict. 성공이면 매트릭스를 저장하고 found에 더하며, 재사용이면 그 항목의 fixed_seeds에 더한다."""
        started = time.perf_counter()
        if self.config.TRY_FOUND_MATRICES_FIRST:
            if not found:
                self._log(kv("found matrices", "none yet"))
            else:
                index = self.try_found_matrices(found, seed)
                if index is not None:
                    found[index].fixed_seeds.append(seed)
                    elapsed = time.perf_counter() - started
                    self._record({"seed": seed, "attempt": 0, "row": 0, "kind": "pool", "decoding": "success",
                                  "elapsed_sec": elapsed, "note": f"reused {found[index].matrix_file}"})
                    self._log(kv("found matrices", f"{len(found)} tried, {found[index].matrix_file} fixes it"))
                    self._finish_uncor(uncor_idx, seed, "REUSED",
                                       [("matrix", found[index].matrix_file),
                                        ("fixes", f"{len(found[index].fixed_seeds)} seeds")],
                                       f"{found[index].matrix_file} (fixes {len(found[index].fixed_seeds)} seeds)", elapsed)
                    return {"seed": seed, "result": "reused", "num_rows": len(found[index].rows), "final_min_err": 0,
                            "matrix_file": found[index].matrix_file, "elapsed_sec": elapsed, "fail_reason": ""}
                self._record({"seed": seed, "attempt": 0, "row": 0, "kind": "pool", "decoding": "fail",
                              "elapsed_sec": time.perf_counter() - started, "note": f"no found matrix fixes ({len(found)} tried)"})
                self._log(kv("found matrices", f"{len(found)} tried, none fixes it"))

        outcome = self.search_matrix_for_uncor(uncor_idx, seed)
        matrix_file = ""
        if outcome.rows:
            matrix_file = self._matrix_relative_path(seed)
            if self.is_root and self.session_dir:
                path = os.path.join(self.session_dir, matrix_file)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                save_stacked_matrix(self.template, outcome.rows, path, max_iter=self.iteration_budget(len(outcome.rows)))
        if outcome.result == "success":
            found.append(FoundMatrix(rows=list(outcome.rows), matrix_file=matrix_file, origin_seed=seed, fixed_seeds=[seed]))
        final_min_err = outcome.final.min_err if outcome.final is not None else None
        elapsed = time.perf_counter() - started
        if outcome.result == "success":
            budget = self.iteration_budget(len(outcome.rows))
            self._finish_uncor(uncor_idx, seed, "SUCCESS",
                               [("rows", len(outcome.rows)),
                                ("corrected", f"at iteration {outcome.final.success_iteration} of {budget}"),
                                ("matrix", matrix_file)],
                               f"rows {len(outcome.rows)}  corrected at iteration {outcome.final.success_iteration}", elapsed)
        else:
            self._finish_uncor(uncor_idx, seed, "FAIL",
                               [("reason", outcome.fail_reason), ("rows", len(outcome.rows)), ("min_err", final_min_err),
                                ("matrix", matrix_file or "(none)")],
                               f"rows {len(outcome.rows)}  min_err {final_min_err}  {outcome.fail_reason}", elapsed)
        return {"seed": seed, "result": outcome.result, "num_rows": len(outcome.rows), "final_min_err": final_min_err,
                "matrix_file": matrix_file, "elapsed_sec": elapsed, "fail_reason": outcome.fail_reason}


def collect_uncors(config: RowStackConfig, parallel, code, decoder, logger: Optional[RootLogger],
                   failing_seeds_fn: Callable = failing_seeds) -> tuple:
    """기존 매트릭스로 seed를 세며 복호해 실패 seed K개를 모은다. (오름차순 seed 목록, 돌린 프레임 수)를 모든 rank에 돌려준다."""
    is_root = parallel.rank == 0
    batch_size = config.COLLECT_FRAMES_PER_BATCH
    local_failures, next_seed, frames_decoded, stop = [], parallel.rank, 0, False
    while not stop:
        seeds = [next_seed + k * parallel.size for k in range(batch_size)]
        local_failures.extend(failing_seeds_fn(code, decoder, config.CHANNEL_TYPE, config.CHANNEL_POINT, seeds,
                                               batch_size, config.channel_extra()))
        next_seed += batch_size * parallel.size
        counts = parallel.gather_to_root((len(local_failures), batch_size))
        if is_root:
            total_failures = sum(count for count, _ in counts)
            frames_decoded += sum(frames for _, frames in counts)
            stop = total_failures >= config.NUM_UNCORS_TO_COLLECT or frames_decoded >= config.COLLECT_MAX_FRAMES
            if logger is not None:
                logger.raw(kv("collecting", f"{total_failures} failures / {frames_decoded} frames  @ {clock()}"))
        stop = parallel.bcast_from_root(stop if is_root else None)
    gathered = parallel.gather_to_root(local_failures)
    result = None
    if is_root:
        merged = sorted({int(seed) for part in gathered for seed in part})[:config.NUM_UNCORS_TO_COLLECT]
        result = (merged, frames_decoded)
    return parallel.bcast_from_root(result)


def _seed_list_text(seeds: list, limit: int = 12) -> str:
    shown = ", ".join(str(seed) for seed in seeds[:limit])
    return shown + (f", ... ({len(seeds)} total)" if len(seeds) > limit else "")


def run(config: RowStackConfig, parallel) -> Optional[str]:
    """1판 설계 4.1절의 바깥 흐름. 세션 폴더 경로를 돌려준다."""
    config.validate()
    is_root = parallel.rank == 0
    session_dir = None
    if is_root:
        session_dir = os.path.join(config.OUTPUT_ROOT, time.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(session_dir, exist_ok=True)
        shutil.copy2(RowStack_Config.__file__, os.path.join(session_dir, "config_used.py"))
    session_dir = parallel.bcast_from_root(session_dir)
    run_started = time.perf_counter()
    logger = RootLogger(os.path.join(session_dir, "log.txt")) if is_root else None
    result_logger = FileLogger(os.path.join(session_dir, "result.txt")) if is_root else None
    rank_logger = FileLogger(os.path.join(session_dir, "rank_logs", f"rank_{parallel.rank}.txt"))

    def log(text):
        if logger is not None:
            logger.raw(text)

    def both(text):
        log(text)
        if result_logger is not None:
            result_logger.raw(text)

    code = QCCode.load(config.h_matrix_path())
    initial = LLRMatrix.load(config.initial_llr_matrix_path())
    mode = initial.mode
    if mode not in chan.CHANNEL_MODES[config.CHANNEL_TYPE]:
        raise SystemExit(f"채널 {config.CHANNEL_TYPE}은 모드 {mode}를 지원하지 않음 (지원: {chan.CHANNEL_MODES[config.CHANNEL_TYPE]})")
    template = MatrixTemplate.from_base_llr_matrix(initial, config.MAX_DECODING_ITERATION)
    info = uncor_info_from_config(config, mode)
    header = format_settings_header(config, session_dir, mode, parallel.size,
                                    config.UNCOR_SEED_DIR or "(none, collect now)")
    both(header)
    legend = format_legend()
    log(legend)
    rank_logger.raw(f"rank {parallel.rank}/{parallel.size}  session {session_dir}")
    rank_logger.raw(legend)

    both("")
    both(section_line("Collect uncors", heavy=True))
    if config.UNCOR_SEED_DIR:
        seeds, file_info = read_uncor_files(config.UNCOR_SEED_DIR)
        mismatch = uncor_info_mismatch(file_info, info)
        if mismatch:
            both(kv("error", f"uncor seed 파일의 설정이 다릅니다: {mismatch}"))
            raise SystemExit(f"uncor seed 파일의 설정이 다릅니다: {mismatch}")
        frames_decoded = int(file_info.get("frames_decoded", 0))
        both(kv("loaded from", config.UNCOR_SEED_DIR))
    else:
        decoder = BaseDecoder(code, llr_matrix=initial)
        seeds, frames_decoded = collect_uncors(config, parallel, code, decoder, logger)
    both(kv("frames decoded", frames_decoded))
    both(kv("uncors found", f"{len(seeds)}  (seeds {_seed_list_text(seeds)})" if seeds else "0"))
    both(kv("time", f"{time.perf_counter() - run_started:.0f}s"))
    if is_root:
        write_uncor_files(os.path.join(session_dir, COLLECTED_UNCORS_DIR_NAME), seeds, info,
                          config.initial_llr_matrix_path(), frames_decoded)
    if not seeds:
        both(kv("note", "no uncor collected"))
        both("")
        both(section_line("RowStack End", heavy=True))
        return session_dir

    if result_logger is not None:
        result_logger.raw("")
        result_logger.raw(section_line("Results", heavy=True, with_time=False))

    evaluator = UncorDecoder(code, template, config.CHANNEL_TYPE, config.CHANNEL_POINT, config.channel_extra())
    tested_matrix_dir = None
    if config.SAVE_TESTED_MATRICES:
        tested_matrix_dir = os.path.join(session_dir, "tested_matrices", f"rank_{parallel.rank}")
    session = RowStackSession(config, parallel, evaluator, template, session_dir if is_root else None, logger,
                              result_logger=result_logger, rank_logger=rank_logger, tested_matrix_dir=tested_matrix_dir,
                              total_uncors=len(seeds))
    summary = CsvAppender(os.path.join(session_dir, "summary.csv"), SUMMARY_COLUMNS) if is_root else None
    found = []
    counts = {"success": 0, "reused": 0, "fail": 0}
    for uncor_idx, seed in enumerate(seeds):
        session.begin_uncor(uncor_idx, seed)
        row = session.run_one_uncor(uncor_idx, seed, found)
        counts[row["result"]] += 1
        if is_root:
            summary.append(row)
            write_found_matrices(os.path.join(session_dir, "found_matrices.csv"), found)
    total_minutes = (time.perf_counter() - run_started) / 60
    both("")
    both(section_line("RowStack End", heavy=True))
    both(kv("uncors", f"{len(seeds)}  (success {counts['success']}, reused {counts['reused']}, fail {counts['fail']})"))
    both(kv("matrices found", len(found)))
    both(kv("time", f"{total_minutes:.1f} min"))
    return session_dir


def run_or_abort(config: RowStackConfig, parallel, comm, run_fn: Callable = run):
    """run_fn(config, parallel)을 돌린다. 어떤 예외든(SystemExit 포함) traceback을 stderr에 찍고 comm.Abort(1)로
    모든 rank를 멈춘다. 한 rank만 죽으면 나머지가 다음 집단 통신에서 영원히 기다리므로, 예외는 전체 중단으로 바꾼다."""
    try:
        return run_fn(config, parallel)
    except BaseException:
        traceback.print_exc()
        sys.stderr.flush()
        comm.Abort(1)


def main() -> None:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    run_or_abort(CONFIG, MpiParallel(comm), comm)


if __name__ == "__main__":
    main()
