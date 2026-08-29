@echo off
title AHFMES-ARE Mission Control (Production Mode)
color 0A
echo ======================================================================
echo   AHFMES-ARE MISSION CONTROL // PRODUCTION 1-CLICK LAUNCHER
echo ======================================================================
echo.

echo [1/4] Menyiapkan AI Copilot (Ollama LLM)...
start "Ollama AI Engine" /min cmd /c "ollama serve"
timeout /t 2 >nul
start "Ollama Model Preloader" /min cmd /c "ollama run llama3.2:3b"

echo [2/4] Menjalankan Python Core Engine (Port 8080)...
set PYTHONPATH=.
start "AHFMES Python Engine" /min cmd /c "python -m are.web_ui --db are_interactive.db --port 8080"

echo [3/4] Menjalankan Next.js UI dalam Mode Produksi Cepat (Port 4028)...
start "AHFMES Next.js UI" /min cmd /c "cd /d "%~dp0UI" && npm run serve"

echo [4/4] Membuka Mission Control Dashboard di Browser...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:4028"

echo.
echo ======================================================================
echo   MISSION CONTROL AKTIF (FAST PRODUCTION MODE)!
echo   - Web UI Desktop ^& HP : http://127.0.0.1:4028
echo   - Python Engine API   : http://127.0.0.1:8080
echo   - Ollama AI Copilot   : http://localhost:11434
echo ======================================================================
echo Jendela ini bisa ditutup (layanan tetap berjalan di background).
timeout /t 4 >nul
