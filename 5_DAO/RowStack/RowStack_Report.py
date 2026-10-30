"""history.csv, summary.csv, found_matrices.csv와 root 로그 (설계 문서 4.7절). root만 쓴다."""
import csv
import os
import time
from typing import Optional

HISTORY_COLUMNS = ["seed", "attempt", "row", "kind", "parent", "round", "threshold", "takeover_iteration",
                   "iterations", "parent_min_err", "num_improved", "best_rank", "best_candidate", "min_err",
                   "min_err_iteration", "csw_at_min_err", "decoding", "corrected_iteration", "elapsed_sec", "note"]
# round 하나가 한 줄. kind: gen, mut, pool. row: 붙이는 row 번호(1부터), parent: 부모 매트릭스 번호(1부터),
# round: 같은 부모에 대한 반복 번호(1부터). iterations: 복호 예산. parent_min_err: 부모의 최소 잔여 에러.
# num_improved: 모든 rank에서 부모보다 나아진 후보 수. best_rank와 best_candidate: 그 가운데 최고를 낸 rank와
# 그 rank 안의 후보 번호. decoding: success 또는 fail
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
SECTION_HEAVY = "=" * 20          # DAO의 Write_Log_Separator와 같은 꼴: ==== [제목 @ 시각] ====
SECTION_LIGHT = "-" * 10


def clock() -> str:
    """구역 머리줄과 round 줄에 붙이는 시각 (날짜는 설정 머리글에 있다)."""
    return time.strftime("%H:%M:%S")


def section_line(title: str, heavy: bool = True, with_time: bool = True) -> str:
    """구역 머리줄. heavy는 ====, 아니면 ----. with_time이면 제목 뒤에 @ 시각."""
    mark = SECTION_HEAVY if heavy else SECTION_LIGHT
    stamp = f" @ {clock()}" if with_time else ""
    return f"{mark} [{title}{stamp}] {mark}"


def kv(label: str, value, width: int = 15) -> str:
    """'  이름 : 값' 꼴의 항목 줄."""
    return f"  {label:<{width}}: {value}"


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
        ("NUM_PARENTS_TO_KEEP", config.NUM_PARENTS_TO_KEEP),
        ("CANDIDATES_PER_RANK_PER_ROUND", config.CANDIDATES_PER_RANK_PER_ROUND),
        ("MAX_GEN_ROUNDS_PER_ROW", config.MAX_GEN_ROUNDS_PER_ROW),
        ("MUTANTS_PER_RANK_PER_ROUND", f"{config.MUTANTS_PER_RANK_PER_ROUND} "
                                       f"(elements {config.MUTATION_NUM_ELEMENTS}, range ±{config.MUTATION_RANGE})"),
        ("MAX_MUT_ROUNDS_PER_ROW", config.MAX_MUT_ROUNDS_PER_ROW),
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


def format_legend() -> str:
    """로그의 자리 표기가 뜻하는 것. log.txt와 rank 로그의 설정 머리글 다음에 둔다."""
    lines = [
        "[legend]",
        "  Row r/R         : building the r-th row of the matrix (R = MAX_ROWS)",
        "  parent p/P      : p-th of the P matrices kept from the previous row (P <= NUM_PARENTS_TO_KEEP);",
        "                    at row 1 the only parent is the received frame itself (no row yet)",
        "  round k/K       : one set of candidates per rank on that parent; repeated up to K times while none improves on it",
        "  gen / mut       : gen appends one new random row to the parent, mut changes a few CH/TH values anywhere in the parent",
        "  gen #i, mut #i  : i-th candidate a rank tests in the round (CANDIDATES_PER_RANK_PER_ROUND, MUTANTS_PER_RANK_PER_ROUND)",
        "  rank1 #3        : the candidate that rank 1 tested as its 3rd",
        "  improved        : better than the parent (decoding success first, then smaller min_err; equal is not an improvement)",
        "  kept            : matrices kept after a row (best NUM_PARENTS_TO_KEEP of all improved candidates); parents of the next row",
        SEPARATOR_LIGHT,
    ]
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
    """root의 로그: stdout과 파일(path가 있을 때)에 함께 쓴다. 시각은 줄 끝에 붙여 들여쓰기와 열이 맞게 한다."""

    def __init__(self, path: Optional[str]):
        super().__init__(path, to_stdout=True, timestamp_at_end=True)
