@echo off
rem mpiexec -n 4 python "%~dp0SRC\DAO_Main.py" %*
mpiexec -n 4 python "%~dp0SRC\DAO_Main.py" 1 2 3 4