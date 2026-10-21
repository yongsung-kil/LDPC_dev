"""uncor seed 파일과 설정 대조, 실패 seed 추리기 (설계 문서 4.6절).

collected_uncors 폴더에는 uncor_seeds.txt(한 줄에 seed 하나), info.json(채널 설정과 파일 이름, 모은 수,
돌린 프레임 수), uncor를 모을 때 쓴 LLR matrix 파일 사본이 들어간다.
"""
import json
import os
import shutil
from typing import Optional

import RowStack_Config  # noqa: F401  (sys.path 등록)
from src.sim import decode_frame_seeds

UNCOR_SEEDS_FILE_NAME = "uncor_seeds.txt"
UNCOR_INFO_FILE_NAME = "info.json"


def uncor_info_from_config(config, mode: str) -> dict:
    """seed 파일을 다시 쓸 때 같아야 하는 설정 값."""
    return {"channel_type": config.CHANNEL_TYPE, "channel_point": config.CHANNEL_POINT,
            "strong_scr": config.STRONG_SCR, "strong_ser": config.STRONG_SER,
            "h_matrix_file": config.H_MATRIX_FILE, "initial_llr_matrix_file": config.INITIAL_LLR_MATRIX_FILE,
            "mode": mode}


def write_uncor_files(dir_path: str, seeds: list, info: dict, initial_llr_matrix_path: str,
                      frames_decoded: int = 0) -> None:
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, UNCOR_SEEDS_FILE_NAME), "w", encoding="utf-8") as f:
        for seed in seeds:
            f.write(f"{int(seed)}\n")
    full_info = dict(info)
    full_info["num_collected"] = len(seeds)
    full_info["frames_decoded"] = int(frames_decoded)
    with open(os.path.join(dir_path, UNCOR_INFO_FILE_NAME), "w", encoding="utf-8") as f:
        json.dump(full_info, f, ensure_ascii=False, indent=2)
    shutil.copy2(initial_llr_matrix_path, os.path.join(dir_path, os.path.basename(initial_llr_matrix_path)))


def read_uncor_files(dir_path: str) -> tuple:
    """(seed 목록, info dict)."""
    with open(os.path.join(dir_path, UNCOR_SEEDS_FILE_NAME), encoding="utf-8") as f:
        seeds = [int(line.strip()) for line in f if line.strip()]
    with open(os.path.join(dir_path, UNCOR_INFO_FILE_NAME), encoding="utf-8") as f:
        info = json.load(f)
    return seeds, info


def uncor_info_mismatch(info: dict, expected: dict) -> Optional[str]:
    """expected의 키마다 info와 대조해 다른 것을 문장으로 돌려준다. 모두 같으면 None."""
    differences = []
    for key, value in expected.items():
        if key not in info:
            differences.append(f"{key}: 파일에 없음 / 설정 {value}")
        elif info[key] != value:
            differences.append(f"{key}: 파일 {info[key]} / 설정 {value}")
    return ", ".join(differences) if differences else None


def failing_seeds(code, decoder, channel_type: str, point: float, seeds: list, frames_per_batch: int,
                  channel_extra: dict) -> list:
    """seed 목록을 복호해 실패한 seed만 돌려준다 (입력 순서 유지)."""
    if not seeds:
        return []
    out = decode_frame_seeds(code, decoder, channel_type, point, list(seeds),
                             frames_per_batch=frames_per_batch, **channel_extra)
    return [int(seed) for seed, ok in zip(out["seeds"], out["success"]) if not ok]
