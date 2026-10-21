"""history.csv, summary.csv, found_matrices.csv와 root 로그 (설계 문서 4.7절). root만 쓴다."""
import csv
import os
import time
from typing import Optional

HISTORY_COLUMNS = ["seed", "attempt", "stage", "kind", "threshold", "takeover_iteration", "best_rank",
                   "min_err", "min_err_iteration", "csw_at_min_err", "success", "success_iteration",
                   "replaced", "elapsed_sec", "note"]          # kind: gen, mut, pool
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


class RootLogger:
    """시각을 앞에 붙여 stdout과 파일(path가 있을 때)에 한 줄씩 쓴다."""

    def __init__(self, path: Optional[str]):
        self.path = path
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def line(self, text: str) -> None:
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {text}"
        print(line, flush=True)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
