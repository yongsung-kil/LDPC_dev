@echo off
setlocal
echo 🚀 Installing minimal dependencies for DAO project...

python -m pip install --upgrade pip
pip install numpy mpi4py

echo ✅ Installation complete!
pause
endlocal