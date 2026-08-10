@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64 >nul 2>&1
cd /d %~dp0
echo === Building LDPC Simulator ===
cl /EHsc /W3 /O2 /Fe:ldpc_sim.exe GT.cpp TV_Dec.cpp TV_Dec_Inter.cpp TV_Enc.cpp channel.cpp common.cpp corner.cpp decoder.cpp ecc_top.cpp encoder.cpp full_CRC.cpp input.cpp local_opt.cpp main.cpp mpi.cpp partial_CRC.cpp random.cpp
echo === Build complete (exit code: %ERRORLEVEL%) ===
