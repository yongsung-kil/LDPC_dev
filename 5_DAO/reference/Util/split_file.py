import os
import sys

def split_file(file_path, lines_per_split):
    """
    텍스트 파일을 N개 라인씩 나누어 폴더별로 저장

    Args:
        file_path: 원본 파일의 절대 경로 (.txt)
        lines_per_split: 각 파일에 포함할 라인 수
    """
    # 파일 존재 확인
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
        return

    # 파일 읽기
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[ERROR] 파일 읽기 실패: {e}")
        return

    total_lines = len(lines)
    print(f"총 라인 수: {total_lines}")

    # 필요한 폴더 개수 계산
    num_folders = (total_lines + lines_per_split - 1) // lines_per_split
    print(f"생성할 폴더 수: {num_folders}")

    # 원본 파일 정보
    base_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)

    # 각 폴더에 파일 분할 저장
    for folder_idx in range(1, num_folders + 1):
        # 폴더 생성
        folder_path = os.path.join(base_dir, str(folder_idx))
        os.makedirs(folder_path, exist_ok=True)

        # 해당 폴더에 저장할 라인 범위
        start_idx = (folder_idx - 1) * lines_per_split
        end_idx = min(start_idx + lines_per_split, total_lines)

        # 파일 저장
        output_file_path = os.path.join(folder_path, file_name)
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.writelines(lines[start_idx:end_idx])
            print(f"[{folder_idx}/{num_folders}] 생성 완료: {output_file_path} ({end_idx - start_idx} 라인)")
        except Exception as e:
            print(f"[ERROR] 파일 저장 실패 ({folder_idx}): {e}")

    print(f"\n완료! 원본 파일은 그대로 유지됩니다: {file_path}")

def main():
    if len(sys.argv) < 3:
        print("사용법: python split_file.py <파일경로> <라인수>")
        print("예시: python split_file.py C:\\data\\input.txt 1000")
        return

    file_path = sys.argv[1]
    try:
        lines_per_split = int(sys.argv[2])
        if lines_per_split <= 0:
            raise ValueError("라인 수는 1 이상이어야 합니다.")
    except ValueError as e:
        print(f"[ERROR] 잘못된 라인 수: {e}")
        return

    split_file(file_path, lines_per_split)

if __name__ == "__main__":
    main()
