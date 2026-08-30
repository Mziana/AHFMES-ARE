@echo off
title AHFMES-ARE Launcher v2.0
color 0A
setlocal EnableDelayedExpansion

:: ============================================================
::   AHFMES-ARE UNIFIED LAUNCHER
::   Replaces: START.bat, run_ui.bat, START_MISSION_CONTROL.bat,
::             AHFMES_Dashboard.vbs, START_TUNNEL.bat, START_UI.bat
:: ============================================================

set "ROOT=%~dp0"
set "PYTHON_PORT=8080"
set "NEXTJS_PORT=4028"

:: Detect project root (parent of this script)
cd /d "%ROOT%"

:MENU
cls
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║          AHFMES-ARE  ·  UNIFIED LAUNCHER  v2.0             ║
echo  ║       Autonomous Research Engine Control Center             ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo   [1]  Full Stack      (Python Engine + Next.js UI + Browser)
echo   [2]  Engine Only     (Python ARE Engine on port %PYTHON_PORT%)
echo   [3]  UI Only         (Next.js Dashboard on port %NEXTJS_PORT%)
echo   [4]  Background Mode (Everything hidden, browser opens)
echo   [5]  Stop All        (Kill all ARE processes)
echo   [6]  Health Check    (Verify engine + UI are running)
echo.
echo   [0]  Exit
echo.
echo  ─────────────────────────────────────────────────────────────
set /p choice="  Select mode: "

if "%choice%"=="1" goto FULL_STACK
if "%choice%"=="2" goto ENGINE_ONLY
if "%choice%"=="3" goto UI_ONLY
if "%choice%"=="4" goto BACKGROUND
if "%choice%"=="5" goto STOP_ALL
if "%choice%"=="6" goto HEALTH_CHECK
if "%choice%"=="0" goto EXIT
echo.
echo  [!] Invalid option. Press any key to try again...
pause >nul
goto MENU

:: ============================================================
::  MODE 1: FULL STACK
:: ============================================================
:FULL_STACK
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   AHFMES-ARE // FULL STACK MODE
echo  ════════════════════════════════════════════════════════════
echo.

:: [1] Start MT5 Server
echo  [1/4] Starting MT5 Server (port 18888)...
start "MT5-Server" /min cmd /c "cd /d "%ROOT%" && python -m are.mt5_server --port 18888"
timeout /t 2 >nul

:: [2] Start Python Engine
echo  [2/4] Starting Python ARE Engine (port %PYTHON_PORT%)...
set PYTHONPATH=%ROOT%
start "ARE-Engine" /min cmd /c "cd /d "%ROOT%" && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port %PYTHON_PORT%"
timeout /t 2 >nul

:: [3] Start Next.js UI
echo  [3/4] Starting Next.js UI (port %NEXTJS_PORT%)...
start "ARE-UI" /min cmd /c "cd /d "%ROOT%UI" && npm run serve"
timeout /t 3 >nul

:: [4] Open Browser
echo  [4/4] Opening Mission Control Dashboard...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:%NEXTJS_PORT%"

echo.
echo  ════════════════════════════════════════════════════════════
echo   AHFMES-ARE IS LIVE!
echo  ────────────────────────────────────────────────────────────
echo   Web UI Dashboard : http://127.0.0.1:%NEXTJS_PORT%
echo   Python Engine API: http://127.0.0.1:%PYTHON_PORT%
echo   MT5 Server       : http://127.0.0.1:18888
echo  ────────────────────────────────────────────────────────────
echo   Tip: This window can be closed (services run in background).
echo         To stop: run ARELauncher.bat and choose [5] Stop All
echo  ════════════════════════════════════════════════════════════
echo.
pause
goto MENU

:: ============================================================
::  MODE 2: ENGINE ONLY
:: ============================================================
:ENGINE_ONLY
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   AHFMES-ARE // ENGINE ONLY MODE
echo  ════════════════════════════════════════════════════════════
echo.
echo  Starting Python ARE Engine on port %PYTHON_PORT%...
echo  Press Ctrl+C to stop.
echo.

set PYTHONPATH=%ROOT%
cd /d "%ROOT%"
python -m are.web_ui --db are_interactive.db --port %PYTHON_PORT%
goto MENU

:: ============================================================
::  MODE 3: UI ONLY
:: ============================================================
:UI_ONLY
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   AHFMES-ARE // UI ONLY MODE
echo  ════════════════════════════════════════════════════════════
echo.
echo  Starting Next.js Dashboard on port %NEXTJS_PORT%...
echo  Note: Engine must be running separately for full functionality.
echo  Press Ctrl+C to stop.
echo.

cd /d "%ROOT%UI"
npm run dev
goto MENU

:: ============================================================
::  MODE 4: BACKGROUND (Silent)
:: ============================================================
:BACKGROUND
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   AHFMES-ARE // BACKGROUND MODE
echo  ════════════════════════════════════════════════════════════
echo.

echo  [1/3] Starting Python Engine (hidden)...
set PYTHONPATH=%ROOT%
start "" /min cmd /c "cd /d "%ROOT%" && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port %PYTHON_PORT%"
timeout /t 2 >nul

echo  [2/3] Starting Next.js UI (hidden)...
start "" /min cmd /c "cd /d "%ROOT%UI" && npm run serve"
timeout /t 3 >nul

echo  [3/3] Opening browser...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:%NEXTJS_PORT%"

echo.
echo   ✓ All services started in background.
echo   ✓ Dashboard: http://127.0.0.1:%NEXTJS_PORT%
echo.
timeout /t 2 >nul
goto MENU

:: ============================================================
::  STOP ALL
:: ============================================================
:STOP_ALL
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   AHFMES-ARE // STOPPING ALL SERVICES
echo  ════════════════════════════════════════════════════════════
echo.

echo  Stopping Python ARE Engine...
taskkill /FI "WINDOWTITLE eq ARE-Engine" /F >nul 2>&1
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *are.web_ui*" /F >nul 2>&1

echo  Stopping Next.js UI...
taskkill /FI "WINDOWTITLE eq ARE-UI" /F >nul 2>&1

echo.
echo   ✓ All ARE services stopped.
echo.
pause
goto MENU

:: ============================================================
::  HEALTH CHECK
:: ============================================================
:HEALTH_CHECK
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   AHFMES-ARE // HEALTH CHECK
echo  ════════════════════════════════════════════════════════════
echo.

:: Check Python Engine
echo  Checking Python Engine (port %PYTHON_PORT%)...
curl -s http://127.0.0.1:%PYTHON_PORT%/api/status >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Python Engine is ONLINE
) else (
    echo   [!!] Python Engine is OFFLINE
)

:: Check Next.js UI
echo  Checking Next.js UI (port %NEXTJS_PORT%)...
curl -s http://127.0.0.1:%NEXTJS_PORT% >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Next.js UI is ONLINE
) else (
    echo   [!!] Next.js UI is OFFLINE
)

:: Check DB file
echo  Checking database...
if exist "%ROOT%are_interactive.db" (
    echo   [OK] Database file exists
) else (
    echo   [!!] Database file not found
)

echo.
pause
goto MENU

:: ============================================================
::  EXIT
:: ============================================================
:EXIT
echo.
echo  Goodbye! AHFMES-ARE services continue running in background.
echo  To stop them, run ARELauncher.bat and choose [5] Stop All.
echo.
exit /b 0
