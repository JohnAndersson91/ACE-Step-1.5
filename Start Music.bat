@echo off
cd /d "%~dp0"
start "" "http://127.0.0.1:7860"
".venv\Scripts\python.exe" -m acestep.acestep_v15_pipeline --server-name 127.0.0.1 --port 7860 --init_service true --init_llm false --config_path acestep-v15-turbo --offload_to_cpu true
pause
