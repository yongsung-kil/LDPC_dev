"""
각 Process 디렉토리마다 result 파일 존재 여부를 확인하는 스크립트
"""
import os
from pathlib import Path

def check_result_files():
    """
    지정된 DAO 디렉토리 하위의 Process_* 디렉토리에서 result 파일이 없는 프로세스를 찾습니다.
    """
    # ===== 여기에 DAO 디렉토리 절대 경로를 하드코딩하세요 =====
    dao_dir_path = r"" #예: r"d:\DAO\DAO_HD"  # 예: DAO_HD, DAO_2SD 등
    # =========================================================

    dao_dir = Path(dao_dir_path)

    if not dao_dir.exists() or not dao_dir.is_dir():
        print(f"❌ 오류: 디렉토리를 찾을 수 없습니다: {dao_dir_path}")
        return

    print("=" * 80)
    print(f"Result 파일 누락 확인: {dao_dir.name}")
    print("=" * 80)

    # Process_* 디렉토리 찾기 (Process_0, Process_1, ...)
    process_dirs = sorted([d for d in dao_dir.iterdir()
                          if d.is_dir() and d.name.startswith("Process_")])

    if not process_dirs:
        print(f"⚠️  Process_* 디렉토리를 찾을 수 없습니다.")
        return

    missing_result_processes = []

    for process_dir in process_dirs:
        # result로 시작하는 파일 찾기 (result.txt, result_ch0.txt 등)
        result_files = list(process_dir.glob("result*.txt"))

        if not result_files:
            missing_result_processes.append(process_dir.name)

    # 결과 출력: result 파일이 없는 프로세스만
    if missing_result_processes:
        print(f"\n❌ Result 파일이 없는 프로세스 ({len(missing_result_processes)}개):")
        for proc_name in missing_result_processes:
            print(f"    {proc_name}")
    else:
        print(f"\n✅ 모든 프로세스에 result 파일이 존재합니다.")

    # 요약
    total = len(process_dirs)
    missing = len(missing_result_processes)
    found = total - missing
    print(f"\n📊 요약: 전체 {total}개 프로세스 중 {found}개 완료, {missing}개 미완료")
    print("=" * 80)

if __name__ == "__main__":
    check_result_files()
    input("\n엔터를 누르면 종료합니다...")
