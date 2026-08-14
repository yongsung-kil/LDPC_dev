#!/bin/bash
# ============================================
# Mock ECC Build Script (Linux/Mac)
# PyInstaller를 사용하여 Mock_ECC 실행파일을 빌드합니다.
# ============================================

set -e

echo "[Build] Mock ECC Build Script"
echo

# PyInstaller 설치 확인
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "[Build] PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

echo "[Build] Building Prime_ECC_3.0..."
echo

# PyInstaller로 빌드 (단일 실행파일)
pyinstaller --onefile --name "Prime_ECC_3.0" Mock_ECC.py

echo
echo "[Build] Build successful!"
echo "[Build] Output: dist/Prime_ECC_3.0"
echo

# 빌드된 파일을 Input/Ref_C/Prime_ECC_3.0/EXE/로 복사
TARGET_DIR="../Input/Ref_C/Prime_ECC_3.0/EXE"
mkdir -p "$TARGET_DIR"

cp -f "dist/Prime_ECC_3.0" "$TARGET_DIR/"
if [ $? -eq 0 ]; then
    echo "[Build] Copied to $TARGET_DIR/Prime_ECC_3.0"
else
    echo "[Build] Warning: Could not copy to $TARGET_DIR"
fi

echo
echo "[Build] Done!"
