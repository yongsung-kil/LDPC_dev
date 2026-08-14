@echo off
setlocal enabledelayedexpansion

:: ✅ 1. 현재 날짜와 시간 포맷 정리
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do (
    set yyyy=%%a
    set mm=%%b
    set dd=%%c
)

for /f "tokens=1-3 delims=:." %%a in ("%time%") do (
    set hh=%%a
    set nn=%%b
    set ss=%%c
)

:: 0~9시일 경우 0 제거 (예:  9 → 09)
if 1%!hh! LSS 110 set hh=0!hh!
if 1%!nn! LSS 110 set nn=0!nn!
if 1%!ss! LSS 110 set ss=0!ss!

:: ✅ 2. 폴더 이름 만들기 (예: git_20251104_110809)
set folder_name=git_%yyyy%%mm%%dd%_%hh%%nn%%ss%

:: ✅ 3. 폴더 생성 및 이동
mkdir "%folder_name%"
cd /d "%folder_name%"

:: ✅ 4. 저장소 클론 (주소만 수정)
set repo_url=https://bitbucket.org/yourname/yourrepo.git
echo 🚀 Cloning repository: %repo_url%
git clone %repo_url%

:: ✅ 5. 완료 메시지
echo ✅ Clone completed in folder: %cd%
pause
endlocal
