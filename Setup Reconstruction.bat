@echo off
cd /d "%~dp0"
set "MUSIC_UV=uv"
if exist "..\uv\uv.exe" set "MUSIC_UV=..\uv\uv.exe"
"%MUSIC_UV%" pip install --python ".venv\Scripts\python.exe" basic-pitch==0.4.0 --no-deps
if errorlevel 1 exit /b 1
"%MUSIC_UV%" pip install --python ".venv\Scripts\python.exe" pretty-midi mir-eval tinysoundfont librosa onnxruntime resampy
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m acestep.reconstruction_setup
pause
