@echo off
title AHFMES-ARE Control Center (1-Click Start)
echo ======================================================================
echo   Menjalankan AHFMES-ARE Control Center & Membuka Browser...
echo ======================================================================
set PYTHONPATH=.
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8080"
python -m are.web_ui --db are_interactive.db --port 8080
