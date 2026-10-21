@echo off
rem RowStack: uncor 하나씩 row를 쌓아 고치는 LLR matrix 탐색기. 설정은 RowStack_Config.py의 CONFIG
mpiexec -n 4 python "%~dp0RowStack_Main.py" %*
