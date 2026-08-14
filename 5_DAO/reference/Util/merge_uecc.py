import os
INPUT_FILE_NAME_PREFIX = "abc"
OUTPUT_FILE_NAME = "merged_output.txt"
base_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(base_dir, OUTPUT_FILE_NAME)

def main():
    # 1. 현재 실행된 .py 파일의 위치

    # 2. 하위 폴더 전체 순회
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            # abc로 시작하고 .txt 인 파일만 대상
            if file.startswith(INPUT_FILE_NAME_PREFIX) and file.lower().endswith(".txt"):
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    with open(out_path, "a", encoding="utf-8") as out:
                        out.write(f"\n\n===== {file_path} =====\n")
                        out.write(content)

                except Exception as e:
                    print(f"[ERROR] {file_path}: {e}")

if __name__ == "__main__":
    main()
