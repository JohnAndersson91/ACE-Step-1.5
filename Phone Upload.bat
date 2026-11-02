@echo off
cd /d "%~dp0"
set MUSIC_SECURE_PHONE=true
".venv\Scripts\python.exe" -m acestep.phone_recordings
pause
