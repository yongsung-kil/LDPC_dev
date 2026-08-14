"""
원격 디렉토리 동기화 스크립트
- paramiko SFTP로 원격 → 로컬 동기화
- 변경된 파일만 선택적 다운로드
- 동기화 시간 기록 (sync_log.txt)
- 주기적 자동 실행
"""

import paramiko
import os
import stat
import time
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

# ============================================================
# 하드코딩 설정
# ============================================================
SYNC_INTERVAL_SECONDS = 1800  # 동기화 주기 (초) - 30분 = 1800초
LOG_MAX_LINES = 10000         # 로그 파일당 최대 라인 수

# ============================================================
# 설정
# ============================================================
CONFIG = {
    "host": "your-server.com",
    "port": 22,
    "username": "your-username",

    # 인증: 둘 중 하나 선택
    "key_path": r"C:\Users\you\.ssh\id_rsa",  # SSH 키 경로
    "password": None,                           # 또는 비밀번호

    # 경로
    "remote_path": "/home/user/project",        # 원격 프로젝트 디렉토리
    "local_path": r"C:\local\project",          # 로컬 저장 디렉토리

    # 동기화 옵션
    "exclude_patterns": [".git", "__pycache__", "*.pyc", ".DS_Store"],  # 제외 패턴
    "log_file_base": "sync_log",                # 로그 파일 기본명 (sync_log_0.txt, sync_log_1.txt, ...)
}

# ============================================================
# 로깅 설정
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def should_exclude(name: str, exclude_patterns: list[str]) -> bool:
    """제외 패턴에 해당하는지 확인"""
    from fnmatch import fnmatch
    return any(fnmatch(name, pattern) for pattern in exclude_patterns)


def get_remote_files(sftp, remote_path: str, exclude_patterns: list[str]) -> dict:
    """원격 디렉토리의 모든 파일 목록과 메타정보 수집"""
    file_map = {}

    def _scan(current_remote: str, relative_base: str = ""):
        logger.info(f"  스캔 중: {current_remote}")  # 진행 상황 출력
        try:
            entries = sftp.listdir_attr(current_remote)
        except PermissionError:
            logger.warning(f"권한 없음 (스킵): {current_remote}")
            return
        except Exception as e:
            logger.error(f"스캔 실패 (스킵): {current_remote} - {e}")
            return

        for entry in entries:
            if should_exclude(entry.filename, exclude_patterns):
                continue

            remote_full = f"{current_remote}/{entry.filename}"
            relative = f"{relative_base}/{entry.filename}" if relative_base else entry.filename

            if stat.S_ISDIR(entry.st_mode):
                _scan(remote_full, relative)
            else:
                file_map[relative] = {
                    "remote_path": remote_full,
                    "size": entry.st_size,
                    "mtime": entry.st_mtime,
                }
                if len(file_map) % 100 == 0:  # 100개마다 출력
                    logger.info(f"    → 파일 {len(file_map)}개 발견...")

    _scan(remote_path)
    return file_map


def delete_old_sync_folders(base_path: Path, current_folder: str):
    """이전 server_sync_* 폴더들 삭제 (현재 폴더 제외)"""
    deleted_count = 0
    for folder in base_path.glob("server_sync_*"):
        if folder.is_dir() and folder.name != current_folder:
            try:
                shutil.rmtree(folder)
                logger.info(f"  삭제됨: {folder.name}")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"  삭제 실패: {folder.name} - {e}")

    if deleted_count > 0:
        logger.info(f"총 {deleted_count}개 이전 폴더 삭제 완료")
    else:
        logger.info("삭제할 이전 폴더 없음")


def sync_directory(config: dict) -> dict:
    """
    원격 디렉토리를 로컬에 동기화
    Returns: 동기화 결과 요약 dict
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 타임스탬프 폴더 이름 생성
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    sync_folder_name = f"server_sync_{timestamp}"

    result = {
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "downloaded": [],
        "skipped": 0,
        "deleted": [],
        "errors": [],
        "end_time": None,
        "sync_folder": sync_folder_name,
    }

    try:
        # SSH 접속
        connect_kwargs = {
            "hostname": config["host"],
            "port": config["port"],
            "username": config["username"],
        }
        if config.get("key_path"):
            connect_kwargs["key_filename"] = config["key_path"]
        elif config.get("password"):
            connect_kwargs["password"] = config["password"]

        logger.info(f"서버 접속 중: {config['host']}...")
        ssh.connect(**connect_kwargs)
        sftp = ssh.open_sftp()
        logger.info("접속 성공")

        # 원격 파일 스캔
        logger.info(f"원격 스캔 중: {config['remote_path']}")
        remote_files = get_remote_files(sftp, config["remote_path"], config["exclude_patterns"])
        logger.info(f"원격 파일 {len(remote_files)}개 발견")

        # 타임스탬프 폴더 생성
        base_path = Path(config["local_path"])
        local_base = base_path / sync_folder_name
        local_base.mkdir(parents=True, exist_ok=True)
        logger.info(f"동기화 폴더: {local_base}")

        # 다운로드
        for relative, info in remote_files.items():
            local_file = local_base / relative
            local_file.parent.mkdir(parents=True, exist_ok=True)

            need_download = False
            reason = ""

            if not local_file.exists():
                need_download = True
                reason = "신규"
            else:
                local_mtime = local_file.stat().st_mtime
                local_size = local_file.stat().st_size
                if info["mtime"] > local_mtime:
                    need_download = True
                    reason = "수정됨"
                elif info["size"] != local_size:
                    need_download = True
                    reason = "크기 다름"

            if need_download:
                try:
                    sftp.get(info["remote_path"], str(local_file))
                    # 원격 파일의 수정 시간을 로컬에도 반영
                    os.utime(str(local_file), (info["mtime"], info["mtime"]))
                    result["downloaded"].append(f"[{reason}] {relative}")
                    logger.info(f"  ↓ [{reason}] {relative}")
                except Exception as e:
                    result["errors"].append(f"{relative}: {e}")
                    logger.error(f"  ✗ {relative}: {e}")
            else:
                result["skipped"] += 1

        # 로컬에만 있는 파일 감지 (삭제된 파일)
        for local_file in local_base.rglob("*"):
            if local_file.is_file():
                relative = str(local_file.relative_to(local_base)).replace("\\", "/")
                # 로그 파일과 제외 패턴은 건너뜀
                if relative.startswith(config["log_file_base"]):
                    continue
                if should_exclude(local_file.name, config["exclude_patterns"]):
                    continue
                if relative not in remote_files:
                    result["deleted"].append(relative)
                    logger.info(f"  ⚠ 원격에 없음: {relative}")

        sftp.close()

        # 동기화 성공 시 이전 server_sync_* 폴더 삭제
        if not result["errors"]:
            logger.info("동기화 성공 - 이전 폴더 정리 중...")
            delete_old_sync_folders(base_path, sync_folder_name)

    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"동기화 실패: {e}")
    finally:
        ssh.close()

    result["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result


def get_current_log_path(config: dict, sync_folder: str) -> Path:
    """현재 사용할 로그 파일 경로 반환 (라인 수 기반 로테이션)"""
    base_dir = Path(config["local_path"]) / sync_folder
    log_base = config["log_file_base"]
    log_idx = 0

    while True:
        log_path = base_dir / f"{log_base}_{log_idx}.txt"
        if not log_path.exists():
            return log_path
        # 라인 수 확인
        try:
            line_count = sum(1 for _ in log_path.open(encoding="utf-8"))
            if line_count < LOG_MAX_LINES:
                return log_path
        except Exception:
            return log_path
        log_idx += 1


def write_sync_log(config: dict, result: dict):
    """동기화 결과를 로컬 디렉토리의 로그 파일에 기록"""
    # 타임스탬프 폴더 내부에 로그 저장
    sync_folder = result.get("sync_folder", "server_sync")
    log_path = get_current_log_path(config, sync_folder)

    separator = "=" * 60
    lines = [
        separator,
        f" 동기화 완료: {result['end_time']}",
        separator,
        f" 시작: {result['start_time']}",
        f" 종료: {result['end_time']}",
        f" 원격: {config['host']}:{config['remote_path']}",
        f" 로컬: {config['local_path']}",
        "",
        f" 다운로드: {len(result['downloaded'])}개",
        f" 스킵 (변경없음): {result['skipped']}개",
        f" 원격 삭제 감지: {len(result['deleted'])}개",
        f" 에러: {len(result['errors'])}개",
    ]

    if result["downloaded"]:
        lines.append("")
        lines.append(" [다운로드 목록]")
        for f in result["downloaded"]:
            lines.append(f"   {f}")

    if result["deleted"]:
        lines.append("")
        lines.append(" [원격에서 삭제된 파일 (로컬에 남아있음)]")
        for f in result["deleted"]:
            lines.append(f"   {f}")

    if result["errors"]:
        lines.append("")
        lines.append(" [에러]")
        for e in result["errors"]:
            lines.append(f"   {e}")

    lines.append("")

    log_entry = "\n".join(lines)

    # 기존 로그 앞에 최신 기록 추가 (최신이 위에)
    existing = ""
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8")

    log_path.write_text(log_entry + existing, encoding="utf-8")
    logger.info(f"로그 저장: {log_path}")


def run_once(config: dict):
    """1회 동기화 실행"""
    logger.info("=" * 40)
    logger.info("동기화 시작")
    result = sync_directory(config)
    write_sync_log(config, result)

    logger.info(
        f"완료 — 다운로드: {len(result['downloaded'])}개, "
        f"스킵: {result['skipped']}개, "
        f"에러: {len(result['errors'])}개"
    )
    logger.info("=" * 40)
    return result


def run_periodic(config: dict, interval_sec: int = SYNC_INTERVAL_SECONDS):
    """주기적 동기화 실행"""
    interval_min = interval_sec / 60
    logger.info(f"주기적 동기화 모드 ({interval_sec}초 = {interval_min:.1f}분 간격)")
    logger.info("종료: Ctrl+C")
    logger.info("")

    while True:
        run_once(config)

        next_time = datetime.now().timestamp() + interval_sec
        next_str = datetime.fromtimestamp(next_time).strftime("%H:%M:%S")
        logger.info(f"다음 동기화: {next_str}")
        logger.info("")

        try:
            time.sleep(interval_sec)
        except KeyboardInterrupt:
            logger.info("사용자에 의해 종료됨")
            break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="원격 디렉토리 동기화")
    parser.add_argument("--once", action="store_true", help="1회만 실행")
    parser.add_argument("--host", help="서버 주소")
    parser.add_argument("--remote", help="원격 경로")
    parser.add_argument("--local", help="로컬 경로")
    parser.add_argument("--interval", type=int, help="동기화 주기 (초) - 기본값: SYNC_INTERVAL_SECONDS")
    args = parser.parse_args()

    # CLI 인자로 설정 덮어쓰기
    if args.host:
        CONFIG["host"] = args.host
    if args.remote:
        CONFIG["remote_path"] = args.remote
    if args.local:
        CONFIG["local_path"] = args.local

    # 동기화 주기 설정 (CLI 인자 > 하드코딩 기본값)
    sync_interval = args.interval if args.interval else SYNC_INTERVAL_SECONDS

    if args.once:
        run_once(CONFIG)
    else:
        run_periodic(CONFIG, sync_interval)
