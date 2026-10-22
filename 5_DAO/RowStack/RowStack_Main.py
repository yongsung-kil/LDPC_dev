"""RowStack 흐름: uncor 모으기, 찾은 매트릭스 먼저 시험, stage별 row 쌓기, 보고 (설계 문서 4.1, 4.3, 4.4, 4.6, 4.10절).

실행: mpiexec -n N python RowStack_Main.py (설정은 RowStack_Config.CONFIG).
모든 rank가 같은 제어 흐름을 돌고, 결정은 root가 gather로 모아 bcast한다. 파일은 root만 쓴다.
평가 함수(evaluate_fn(rows, seed) -> CandidateResult)와 병렬 통신은 주입받으므로 rank 1개 가짜 평가기로 검사한다.
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
from RowStack_Evaluate import CandidateResult, UncorDecoder, candidate_sort_key
from RowStack_Matrix import (MatrixTemplate, StackedRow, generate_random_row_values, mutate_row_values,
                             new_row_csw_threshold, save_stacked_matrix, takeover_iteration)
from RowStack_Parallel import MpiParallel, SerialParallel, round_robin_share
from RowStack_Report import (HISTORY_COLUMNS, SEPARATOR_LIGHT, SUMMARY_COLUMNS, CsvAppender, FileLogger, RootLogger,
                             format_settings_header, write_found_matrices)
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


@dataclass
class FoundMatrix:
    rows: list                      # StackedRow 목록
    matrix_file: str                # 세션 폴더 기준 상대 경로
    origin_seed: int                # 처음 고친 seed
    fixed_seeds: list = field(default_factory=list)


@dataclass
class SearchOutcome:
    result: str                     # "success" 또는 "fail"
    rows: list                      # 성공이면 고치는 row들, 실패면 마지막 attempt의 마지막 stage row들
    final: Optional[CandidateResult]
    fail_reason: str                # "", MAX_ROWS_NOTE, NO_THRESHOLD_NOTE


class RowStackSession:
    """uncor 하나를 다루는 흐름. root만 history.csv와 로그를 쓴다."""

    def __init__(self, config: RowStackConfig, parallel, evaluate_fn: Callable, template: MatrixTemplate,
                 session_dir: Optional[str], logger: Optional[RootLogger],
                 result_logger: Optional[FileLogger] = None, rank_logger: Optional[FileLogger] = None):
        """logger는 root의 상세 로그(log.txt), result_logger는 root의 중요 결과(result.txt),
        rank_logger는 이 rank의 후보별 상세(rank_logs/rank_N.txt)다. 없으면 그 기록은 생략한다."""
        self.config = config
        self.parallel = parallel
        self.evaluate = evaluate_fn
        self.template = template
        self.session_dir = session_dir
        self.logger = logger
        self.result_logger = result_logger
        self.rank_logger = rank_logger
        self.is_root = parallel.rank == 0
        self.history = None
        if self.is_root and session_dir:
            self.history = CsvAppender(os.path.join(session_dir, "history.csv"), HISTORY_COLUMNS)

    # ----- 공용 -----
    def _log(self, text: str) -> None:
        if self.is_root and self.logger is not None:
            self.logger.line(text)

    def _result(self, text: str) -> None:
        """중요 결과: 상세 로그와 결과 로그 둘 다에 쓴다 (root만)."""
        self._log(text)
        if self.is_root and self.result_logger is not None:
            self.result_logger.line(text)

    def _rank_log(self, text: str) -> None:
        if self.rank_logger is not None:
            self.rank_logger.line(text)

    def candidate_rng(self, uncor_idx: int, attempt: int, stage: int, kind: str) -> np.random.Generator:
        return np.random.default_rng([self.config.RANDOM_SEED, self.parallel.rank, uncor_idx, attempt, stage,
                                      KIND_CODE[kind]])

    def best_over_ranks(self, local_best):
        """local_best는 (순위 키, payload) 또는 None. root가 (키, rank) 최소를 골라 (rank, payload)를 bcast한다."""
        gathered = self.parallel.gather_to_root(local_best)
        chosen = None
        if self.is_root:
            ranked = [(entry[0], rank, entry[1]) for rank, entry in enumerate(gathered) if entry is not None]
            if ranked:
                key, rank, payload = min(ranked, key=lambda item: (item[0], item[1]))
                chosen = (rank, payload)
        return self.parallel.bcast_from_root(chosen)

    def _record(self, row: dict) -> None:
        if self.history is not None:
            self.history.append(row)

    def _evaluate_block(self, prefix: list, threshold: int, uncor_idx: int, attempt: int, stage: int, kind: str,
                        seed: int, count: int, base_values=None):
        """rank마다 후보 count개를 만들어 시험하고 전체 최고 (rank, payload)를 돌려준다. payload는 values와 result."""
        rng = self.candidate_rng(uncor_idx, attempt, stage, kind)
        local_best = None
        for index in range(1, count + 1):
            started = time.perf_counter()
            if kind == "gen":
                values = generate_random_row_values(self.template, rng)
            else:
                values = mutate_row_values(base_values, self.template, rng, self.config.MUTATION_NUM_ELEMENTS,
                                           self.config.MUTATION_RANGE)
            result = self.evaluate(prefix + [StackedRow(values, threshold)], seed)
            key = candidate_sort_key(result)
            if local_best is None or key < local_best[0]:
                local_best = (key, {"values": values, "result": result})
            self._rank_log(f"seed {seed} a{attempt} s{stage} {kind} #{index}: min_err={result.min_err} it={result.min_err_iteration} "
                           f"csw={result.csw_at_min_err} success={result.success} T={threshold} "
                           f"({time.perf_counter() - started:.1f}s)")
        return self.best_over_ranks(local_best)

    @staticmethod
    def _history_fields(result: CandidateResult) -> dict:
        return {"min_err": result.min_err, "min_err_iteration": result.min_err_iteration,
                "csw_at_min_err": result.csw_at_min_err, "success": result.success,
                "success_iteration": result.success_iteration}

    # ----- 탐색 -----
    def search_matrix_for_uncor(self, uncor_idx: int, seed: int) -> SearchOutcome:
        config = self.config
        last_rows, last_result, fail_reason = [], None, MAX_ROWS_NOTE
        for attempt in range(1, config.MAX_MATRIX_ATTEMPTS_PER_UNCOR + 1):
            rows, prefix_result = [], None
            early_reason = None
            for stage in range(1, config.MAX_ROWS + 1):
                started = time.perf_counter()
                if stage == 1:
                    threshold, source_iteration, takeover = -1, None, None
                else:
                    prev_threshold = None if rows[-1].csw == -1 else rows[-1].csw
                    found_threshold = new_row_csw_threshold(prefix_result.err_per_iter, prefix_result.csw_per_iter,
                                                            prev_threshold, config.MAX_ITERATION_OF_STACKED_GROUP,
                                                            prefix_result.initial_csw)
                    if found_threshold is None:
                        self._record({"seed": seed, "attempt": attempt, "stage": stage, "kind": "gen",
                                      "elapsed_sec": time.perf_counter() - started, "note": NO_THRESHOLD_NOTE})
                        self._log(f"seed {seed} attempt {attempt} stage {stage}: {NO_THRESHOLD_NOTE}")
                        early_reason = NO_THRESHOLD_NOTE
                        break
                    threshold, source_iteration = found_threshold
                    takeover = takeover_iteration(prefix_result.csw_per_iter, threshold, prefix_result.initial_csw)

                rank, payload = self._evaluate_block(rows, threshold, uncor_idx, attempt, stage, "gen", seed,
                                                     config.CANDIDATES_PER_RANK_PER_STAGE)
                best_result = payload["result"]
                if prefix_result is not None and candidate_sort_key(best_result) > candidate_sort_key(prefix_result):
                    # 새 row를 붙인 최고 후보가 prefix 단독보다 나쁘면 고정하지 않는다 (prefix 단독이 더 나은 매트릭스다)
                    self._record({"seed": seed, "attempt": attempt, "stage": stage, "kind": "gen", "threshold": threshold,
                                  "source_iteration": source_iteration, "takeover_iteration": takeover, "best_rank": rank,
                                  **self._history_fields(best_result), "elapsed_sec": time.perf_counter() - started,
                                  "note": NO_IMPROVEMENT_NOTE})
                    self._log(f"seed {seed} attempt {attempt} stage {stage} gen: T={threshold} best min_err={best_result.min_err} "
                              f"is worse than prefix {prefix_result.min_err}: {NO_IMPROVEMENT_NOTE}")
                    early_reason = NO_IMPROVEMENT_NOTE
                    break
                rows.append(StackedRow(payload["values"], threshold))
                prefix_result = best_result
                self._record({"seed": seed, "attempt": attempt, "stage": stage, "kind": "gen", "threshold": threshold,
                              "source_iteration": source_iteration, "takeover_iteration": takeover, "best_rank": rank,
                              **self._history_fields(prefix_result), "elapsed_sec": time.perf_counter() - started})
                self._log(f"seed {seed} attempt {attempt} stage {stage} gen: T={threshold} min_err={prefix_result.min_err} "
                          f"at it {prefix_result.min_err_iteration} (csw {prefix_result.csw_at_min_err}) "
                          f"success={prefix_result.success} rank={rank}")
                if prefix_result.success:
                    return SearchOutcome("success", rows, prefix_result, "")

                if config.MUTANTS_PER_RANK_PER_FIXED_ROW > 0:
                    started = time.perf_counter()
                    rank_m, payload_m = self._evaluate_block(rows[:-1], threshold, uncor_idx, attempt, stage, "mut", seed,
                                                             config.MUTANTS_PER_RANK_PER_FIXED_ROW,
                                                             base_values=rows[-1].values)
                    mutant_result = payload_m["result"]
                    replaced = candidate_sort_key(mutant_result) < candidate_sort_key(prefix_result)
                    if replaced:
                        rows[-1] = StackedRow(payload_m["values"], threshold)
                        prefix_result = mutant_result
                    self._record({"seed": seed, "attempt": attempt, "stage": stage, "kind": "mut", "threshold": threshold,
                                  "source_iteration": source_iteration, "takeover_iteration": takeover, "best_rank": rank_m,
                                  **self._history_fields(mutant_result), "replaced": replaced,
                                  "elapsed_sec": time.perf_counter() - started})
                    self._log(f"seed {seed} attempt {attempt} stage {stage} mut: min_err={mutant_result.min_err} "
                              f"replaced={replaced} success={mutant_result.success} rank={rank_m}")
                    if prefix_result.success:
                        return SearchOutcome("success", rows, prefix_result, "")
            last_rows, last_result = rows, prefix_result
            fail_reason = early_reason if early_reason is not None else MAX_ROWS_NOTE
        return SearchOutcome("fail", last_rows, last_result, fail_reason)

    # ----- 찾은 매트릭스 먼저 시험 -----
    def try_found_matrices(self, found: list, seed: int) -> Optional[int]:
        """고친 uncor 수가 많은 순(같으면 먼저 찾은 순)으로 나눠 시험하고, 고친 것 가운데 가장 앞선 것의 found index."""
        if not found:
            return None
        order = sorted(range(len(found)), key=lambda i: (-len(found[i].fixed_seeds), i))
        local_hits = [position for position in round_robin_share(len(order), self.parallel.rank, self.parallel.size)
                      if self.evaluate(found[order[position]].rows, seed).success]
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

    def run_one_uncor(self, uncor_idx: int, seed: int, found: list) -> dict:
        """summary.csv 한 줄 dict. 성공이면 매트릭스를 저장하고 found에 더하며, 재사용이면 그 항목의 fixed_seeds에 더한다."""
        started = time.perf_counter()
        if self.config.TRY_FOUND_MATRICES_FIRST and found:
            index = self.try_found_matrices(found, seed)
            if index is not None:
                found[index].fixed_seeds.append(seed)
                self._record({"seed": seed, "attempt": 0, "stage": 0, "kind": "pool", "success": True,
                              "elapsed_sec": time.perf_counter() - started, "note": f"reused {found[index].matrix_file}"})
                elapsed = time.perf_counter() - started
                self._result(f"seed {seed}: REUSED {found[index].matrix_file} (fixes {len(found[index].fixed_seeds)} seeds) "
                             f"({elapsed:.1f}s)")
                return {"seed": seed, "result": "reused", "num_rows": len(found[index].rows), "final_min_err": 0,
                        "matrix_file": found[index].matrix_file, "elapsed_sec": elapsed, "fail_reason": ""}
            self._record({"seed": seed, "attempt": 0, "stage": 0, "kind": "pool", "success": False,
                          "elapsed_sec": time.perf_counter() - started, "note": f"no found matrix fixes ({len(found)} tried)"})
            self._log(f"seed {seed}: none of {len(found)} found matrices fixes it")

        outcome = self.search_matrix_for_uncor(uncor_idx, seed)
        matrix_file = ""
        if outcome.rows:
            matrix_file = self._matrix_relative_path(seed)
            if self.is_root and self.session_dir:
                path = os.path.join(self.session_dir, matrix_file)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                save_stacked_matrix(self.template, outcome.rows, path)
        if outcome.result == "success":
            found.append(FoundMatrix(rows=list(outcome.rows), matrix_file=matrix_file, origin_seed=seed, fixed_seeds=[seed]))
        final_min_err = outcome.final.min_err if outcome.final is not None else None
        elapsed = time.perf_counter() - started
        if outcome.result == "success":
            self._result(f"seed {seed}: SUCCESS rows={len(outcome.rows)} success_it={outcome.final.success_iteration} "
                         f"file={matrix_file} ({elapsed:.1f}s)")
        else:
            self._result(f"seed {seed}: FAIL rows={len(outcome.rows)} min_err={final_min_err} reason={outcome.fail_reason} "
                         f"({elapsed:.1f}s)")
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
                logger.line(f"collect: {total_failures} failures / {frames_decoded} frames")
        stop = parallel.bcast_from_root(stop if is_root else None)
    gathered = parallel.gather_to_root(local_failures)
    result = None
    if is_root:
        merged = sorted({int(seed) for part in gathered for seed in part})[:config.NUM_UNCORS_TO_COLLECT]
        result = (merged, frames_decoded)
    return parallel.bcast_from_root(result)


def run(config: RowStackConfig, parallel) -> Optional[str]:
    """설계 4.1절 전체. 세션 폴더 경로를 돌려준다."""
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
            logger.line(text)

    def result(text):
        log(text)
        if result_logger is not None:
            result_logger.line(text)

    code = QCCode.load(config.h_matrix_path())
    initial = LLRMatrix.load(config.initial_llr_matrix_path())
    mode = initial.mode
    if mode not in chan.CHANNEL_MODES[config.CHANNEL_TYPE]:
        raise SystemExit(f"채널 {config.CHANNEL_TYPE}은 모드 {mode}를 지원하지 않음 (지원: {chan.CHANNEL_MODES[config.CHANNEL_TYPE]})")
    template = MatrixTemplate.from_base_llr_matrix(initial, config.MAX_ITERATION_OF_STACKED_GROUP)
    info = uncor_info_from_config(config, mode)
    header = format_settings_header(config, session_dir, mode, parallel.size,
                                    config.UNCOR_SEED_DIR or "(none, collect now)")
    if is_root:
        logger.raw(header)
        result_logger.raw(header)
    rank_logger.raw(f"rank {parallel.rank}/{parallel.size}  session {session_dir}")

    if config.UNCOR_SEED_DIR:
        seeds, file_info = read_uncor_files(config.UNCOR_SEED_DIR)
        mismatch = uncor_info_mismatch(file_info, info)
        if mismatch:
            result(f"uncor seed 파일의 설정이 다릅니다: {mismatch}")
            raise SystemExit(f"uncor seed 파일의 설정이 다릅니다: {mismatch}")
        frames_decoded = int(file_info.get("frames_decoded", 0))
        result(f"uncor seeds loaded from {config.UNCOR_SEED_DIR}: {len(seeds)}")
    else:
        decoder = BaseDecoder(code, llr_matrix=initial)
        seeds, frames_decoded = collect_uncors(config, parallel, code, decoder, logger)
        result(f"collected {len(seeds)} uncors from {frames_decoded} frames ({time.perf_counter() - run_started:.0f}s)")
    if is_root:
        write_uncor_files(os.path.join(session_dir, COLLECTED_UNCORS_DIR_NAME), seeds, info,
                          config.initial_llr_matrix_path(), frames_decoded)
    if not seeds:
        result("no uncor collected")
        return session_dir

    evaluator = UncorDecoder(code, template, config.CHANNEL_TYPE, config.CHANNEL_POINT, config.channel_extra())
    session = RowStackSession(config, parallel, evaluator.evaluate, template, session_dir if is_root else None, logger,
                              result_logger=result_logger, rank_logger=rank_logger)
    summary = CsvAppender(os.path.join(session_dir, "summary.csv"), SUMMARY_COLUMNS) if is_root else None
    found = []
    counts = {"success": 0, "reused": 0, "fail": 0}
    for uncor_idx, seed in enumerate(seeds):
        if logger is not None:
            logger.raw(SEPARATOR_LIGHT)
        log(f"uncor {uncor_idx + 1}/{len(seeds)} seed {seed} (initial csw {evaluator.initial_csw(seed)})")
        row = session.run_one_uncor(uncor_idx, seed, found)
        counts[row["result"]] += 1
        if is_root:
            summary.append(row)
            write_found_matrices(os.path.join(session_dir, "found_matrices.csv"), found)
    if logger is not None:
        logger.raw(SEPARATOR_LIGHT)
    total_minutes = (time.perf_counter() - run_started) / 60
    result(f"done: {len(seeds)} uncors (success {counts['success']}, reused {counts['reused']}, fail {counts['fail']}), "
           f"{len(found)} matrices found, {total_minutes:.1f} min")
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
