@echo off
cd /d "%~dp0"
rem Use the models already on this PC; do not fetch replacements at startup.
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "HF_HUB_DISABLE_TELEMETRY=1"
set "GRADIO_ANALYTICS_ENABLED=False"
start "" "http://127.0.0.1:7860"
".venv\Scripts\python.exe" -m acestep.acestep_v15_pipeline --server-name 127.0.0.1 --port 7860 --init_service true --init_llm false --config_path acestep-v15-turbo --offload_to_cpu true
pause
