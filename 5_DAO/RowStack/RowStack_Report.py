"""history.csv, summary.csv, found_matrices.csv와 root 로그 (설계 문서 4.7절). root만 쓴다."""
import csv
import os
import time
from typing import Optional

HISTORY_COLUMNS = ["seed", "attempt", "stage", "kind", "candidate", "block", "threshold", "takeover_iteration",
                   "iterations", "parent_min_err", "num_improved", "best_rank", "best_index", "min_err",
                   "min_err_iteration", "csw_at_min_err", "decoding", "corrected_iteration", "elapsed_sec", "note"]
# 블록 하나가 한 줄. kind: gen, mut, pool. candidate: 매트릭스 후보 번호(0부터), block: 반복 번호(1부터).
# iterations: 복호 예산. parent_min_err: 부모의 최소 잔여 에러. num_improved: 모든 rank에서 개선된 변형 수.
# best_rank와 best_index: 개선된 변형 가운데 최고를 낸 rank와 그 rank 안의 후보 번호. decoding: success 또는 fail
SUMMARY_COLUMNS = ["seed", "result", "num_rows", "final_min_err", "matrix_file", "elapsed_sec", "fail_reason"]
FOUND_COLUMNS = ["matrix_file", "origin_seed", "num_fixed", "fixed_seeds"]   # fixed_seeds는 공백으로 이은 seed


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


class CsvAppender:
    """columns 순서로 한 줄씩 덧붙인다. 파일이 없거나 비어 있으면 머리글을 먼저 쓴다."""

    def __init__(self, path: str, columns: list):
        self.path = path
        self.columns = list(columns)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(self.columns)

    def append(self, row: dict) -> None:
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([_cell(row.get(column)) for column in self.columns])


def write_found_matrices(path: str, found: list) -> None:
    """찾은 매트릭스 목록 전체를 다시 쓴다. 원소는 .matrix_file, .origin_seed, .fixed_seeds를 가진다."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FOUND_COLUMNS)
        for item in found:
            writer.writerow([item.matrix_file, item.origin_seed, len(item.fixed_seeds),
                             " ".join(str(seed) for seed in item.fixed_seeds)])


SEPARATOR_HEAVY = "=" * 72
SEPARATOR_LIGHT = "-" * 72


def format_settings_header(config, session_dir: str, mode: str, num_ranks: int, uncor_source: str) -> str:
    """로그 맨 위에 두는 설정 머리글. 설정 이름은 RowStack_Config의 이름 그대로 적는다."""
    channel = f"{config.CHANNEL_TYPE}, point {config.CHANNEL_POINT}"
    if config.CHANNEL_TYPE == "strong_error":
        channel += f", SCR {config.STRONG_SCR}, SER {config.STRONG_SER}"
    rows = [
        ("[input]", None),
        ("H_MATRIX_FILE", config.H_MATRIX_FILE),
        ("INITIAL_LLR_MATRIX_FILE", f"{config.INITIAL_LLR_MATRIX_FILE} ({mode})"),
        ("CHANNEL_TYPE / CHANNEL_POINT", channel),
        ("[uncor collection]", None),
        ("NUM_UNCORS_TO_COLLECT", config.NUM_UNCORS_TO_COLLECT),
        ("COLLECT_MAX_FRAMES", f"{config.COLLECT_MAX_FRAMES} (batch {config.COLLECT_FRAMES_PER_BATCH})"),
        ("UNCOR_SEED_DIR", uncor_source),
        ("[search]", None),
        ("MAX_ROWS", config.MAX_ROWS),
        ("NUM_MATRICES_TO_KEEP", config.NUM_MATRICES_TO_KEEP),
        ("CANDIDATES_PER_RANK_PER_BLOCK", config.CANDIDATES_PER_RANK_PER_BLOCK),
        ("MAX_GEN_BLOCKS_PER_ROW", config.MAX_GEN_BLOCKS_PER_ROW),
        ("MUTANTS_PER_RANK_PER_BLOCK", f"{config.MUTANTS_PER_RANK_PER_BLOCK} "
                                       f"(elements {config.MUTATION_NUM_ELEMENTS}, range ±{config.MUTATION_RANGE})"),
        ("MAX_MUT_BLOCKS_PER_ROW", config.MAX_MUT_BLOCKS_PER_ROW),
        ("INIT_DECODING_ITERATION", config.INIT_DECODING_ITERATION),
        ("STEP_ITERATION_PER_ROW", config.STEP_ITERATION_PER_ROW),
        ("MAX_DECODING_ITERATION", config.MAX_DECODING_ITERATION),
        ("CSW_MARGIN_ABOVE_MIN", config.CSW_MARGIN_ABOVE_MIN),
        ("MAX_MATRIX_ATTEMPTS_PER_UNCOR", config.MAX_MATRIX_ATTEMPTS_PER_UNCOR),
        ("TRY_FOUND_MATRICES_FIRST", config.TRY_FOUND_MATRICES_FIRST),
        ("RANDOM_SEED", config.RANDOM_SEED),
        ("[run]", None),
        ("ranks", num_ranks),
        ("session_dir", session_dir),
    ]
    lines = [SEPARATOR_HEAVY, f"RowStack  {time.strftime('%Y-%m-%d %H:%M:%S')}", SEPARATOR_HEAVY]
    for name, value in rows:
        if value is None:
            lines.append(name)
        else:
            lines.append(f"  {name:<32}: {value}")
    lines.append(SEPARATOR_LIGHT)
    return "\n".join(lines)


class FileLogger:
    """파일(path가 있을 때)에 한 줄씩 쓴다. line은 시각을 붙이고(기본은 앞, timestamp_at_end면 뒤) raw는 글자 그대로 쓴다."""

    def __init__(self, path: Optional[str], to_stdout: bool = False, timestamp_at_end: bool = False):
        self.path = path
        self.to_stdout = to_stdout
        self.timestamp_at_end = timestamp_at_end
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def _write(self, text: str) -> None:
        if self.to_stdout:
            print(text, flush=True)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(text + "\n")

    def line(self, text: str) -> None:
        stamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self._write(f"{text}  {stamp}" if self.timestamp_at_end else f"{stamp}  {text}")

    def raw(self, text: str) -> None:
        self._write(text)


class RootLogger(FileLogger):
    """root의 로그: stdout과 파일(path가 있을 때)에 함께 쓴다."""

    def __init__(self, path: Optional[str]):
        super().__init__(path, to_stdout=True)
