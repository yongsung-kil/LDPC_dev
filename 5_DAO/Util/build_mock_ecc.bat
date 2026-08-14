@echo off
REM ============================================
REM Mock ECC Build Script (Windows)
REM PyInstaller를 사용하여 Mock_ECC.exe를 빌드합니다.
REM ============================================

echo [Build] Mock ECC Build Script
echo.

REM PyInstaller 설치 확인
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [Build] PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [Build] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

REM 현재 디렉토리로 이동
cd /d "%~dp0"

echo [Build] Building Mock_ECC.exe...
echo.

REM PyInstaller로 빌드 (단일 실행파일)
pyinstaller --onefile --name "Prime_ECC_3.0" Mock_ECC.py

if errorlevel 1 (
    echo.
    echo [Build] Build failed!
    pause
    exit /b 1
)

echo.
echo [Build] Build successful!
echo [Build] Output: dist\Prime_ECC_3.0.exe
echo.

REM 빌드된 파일을 Input/Ref_C/Prime_ECC_3.0/EXE/로 복사
set TARGET_DIR=..\Input\Ref_C\Prime_ECC_3.0\EXE
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

copy /Y "dist\Prime_ECC_3.0.exe" "%TARGET_DIR%\"
if errorlevel 1 (
    echo [Build] Warning: Could not copy to %TARGET_DIR%
) else (
    echo [Build] Copied to %TARGET_DIR%\Prime_ECC_3.0.exe
)

echo.
echo [Build] Done!
pause
