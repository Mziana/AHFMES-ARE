@echo off
title AHFMES-ARE Launcher v2.2
color 0A

set "ROOT=%~dp0"
if not exist "%ROOT%are\__init__.py" (
    echo  [ERROR] Cannot find are module. Make sure you are running from AHFMES-ARE folder.
    echo  Current ROOT: %ROOT%
    pause
    exit /b 1
)
set "PYTHON_PORT=8080"
set "NEXTJS_PORT=4028"

cd /d "%ROOT%"

:MENU
cls
echo.
echo  ============================================================
echo           AHFMES-ARE  -  UNIFIED LAUNCHER  v2.2
echo        Autonomous Research Engine Control Center
echo  ============================================================
echo.
echo   [1]  Full Stack      (Python Engine + Next.js UI + Browser)
echo   [2]  Engine Only     (Python ARE Engine on port %PYTHON_PORT%)
echo   [3]  UI Only         (Next.js Dashboard on port %NEXTJS_PORT%)
echo   [4]  Background Mode (Everything hidden, browser opens)
echo   [5]  Stop All        (Kill all ARE processes)
echo   [6]  Health Check    (Verify engine + UI are running)
echo   [7]  Live Trading    (Start autopilot brain - tick by tick)

echo.
echo   [0]  Exit
echo.
echo  -------------------------------------------------------------
set /p choice="  Select mode: "

if "%choice%"=="1" goto FULL_STACK
if "%choice%"=="2" goto ENGINE_ONLY
if "%choice%"=="3" goto UI_ONLY
if "%choice%"=="4" goto BACKGROUND
if "%choice%"=="5" goto STOP_ALL
if "%choice%"=="6" goto HEALTH_CHECK
if "%choice%"=="7" goto LIVE_TRADING

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
echo  ============================================================
echo   AHFMES-ARE // FULL STACK MODE
echo  ============================================================
echo.

:: [1] Start MT5 Server
echo  [1/4] Starting MT5 Server (port 18888)...
start "MT5-Server" /min cmd /c "cd /d "%ROOT%" && python -m are.mt5_server --port 18888"
timeout /t 2 >nul

:: [2] Start Python Engine
echo  [2/4] Starting Python ARE Engine (port %PYTHON_PORT%)...
start "ARE-Engine" /min cmd /c "cd /d "%ROOT%" && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port %PYTHON_PORT%"
timeout /t 2 >nul

:: [3] Clear .next cache + Start Next.js UI
echo  [3/4] Starting Next.js UI (port %NEXTJS_PORT%)...
if exist "%ROOT%UI\.next" rd /s /q "%ROOT%UI\.next" 2>nul
start "ARE-UI" /min cmd /c "cd /d "%ROOT%UI" && npm run serve"
timeout /t 3 >nul

:: [4] Open Browser
echo  [4/4] Opening Mission Control Dashboard...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:%NEXTJS_PORT%"

echo.
echo  ============================================================
echo   AHFMES-ARE IS LIVE!
echo  -------------------------------------------------------------
echo   Web UI Dashboard : http://127.0.0.1:%NEXTJS_PORT%
echo   Python Engine API: http://127.0.0.1:%PYTHON_PORT%
echo   MT5 Server       : http://127.0.0.1:18888
echo  -------------------------------------------------------------
echo   Tip: This window can be closed (services run in background).
echo         To stop: run ARELauncher.bat and choose [5] Stop All
echo  ============================================================
echo.
pause
goto MENU

:: ============================================================
::  MODE 2: ENGINE ONLY
:: ============================================================
:ENGINE_ONLY
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // ENGINE ONLY MODE
echo  ============================================================
echo.

echo  Starting Python ARE Engine (port %PYTHON_PORT%)...
start "ARE-Engine" cmd /c "cd /d "%ROOT%" && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port %PYTHON_PORT%"

echo.
echo   Engine running at http://127.0.0.1:%PYTHON_PORT%
echo.
pause
goto MENU

:: ============================================================
::  MODE 3: UI ONLY
:: ============================================================
:UI_ONLY
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // UI ONLY MODE
echo  ============================================================
echo.

if exist "%ROOT%UI\.next" rd /s /q "%ROOT%UI\.next" 2>nul
echo  Starting Next.js UI (port %NEXTJS_PORT%)...
start "ARE-UI" cmd /c "cd /d "%ROOT%UI" && npm run serve"
timeout /t 2 >nul
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:%NEXTJS_PORT%"

echo.
echo   UI running at http://127.0.0.1:%NEXTJS_PORT%
echo.
pause
goto MENU

:: ============================================================
::  MODE 4: BACKGROUND MODE
:: ============================================================
:BACKGROUND
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // BACKGROUND MODE
echo  ============================================================
echo.

echo  [1/4] Starting MT5 Server...
start "MT5-Server" /min cmd /c "cd /d "%ROOT%" && python -m are.mt5_server --port 18888"
timeout /t 1 >nul

echo  [2/4] Starting Engine...
start "ARE-Engine" /min cmd /c "cd /d "%ROOT%" && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port %PYTHON_PORT%"
timeout /t 1 >nul

echo  [3/4] Starting UI...
if exist "%ROOT%UI\.next" rd /s /q "%ROOT%UI\.next" 2>nul
start "ARE-UI" /min cmd /c "cd /d "%ROOT%UI" && npm run serve"
timeout /t 3 >nul

echo  [4/4] Opening browser...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:%NEXTJS_PORT%"

echo.
echo   All services started in background.
echo   Browser will open automatically.
echo.
pause
goto MENU

:: ============================================================
::  MODE 5: STOP ALL
:: ============================================================
:STOP_ALL
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // STOPPING ALL SERVICES
echo  ============================================================
echo.

echo  Stopping MT5 Server...
taskkill /f /fi "WINDOWTITLE eq MT5-Server*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ARE-Engine*" >nul 2>&1

echo  Stopping Next.js...
taskkill /f /fi "WINDOWTITLE eq ARE-UI*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%NEXTJS_PORT% ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

echo  Stopping Python Engine...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PYTHON_PORT% ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

echo.
echo   All services stopped.
echo.
pause
goto MENU

:: ============================================================
::  MODE 6: HEALTH CHECK
:: ============================================================


:: ============================================================

::  MODE 7: LIVE TRADING (Autopilot Brain)

:: ============================================================

:LIVE_TRADING

cls

echo.

echo  ============================================================

echo   AHFMES-ARE // LIVE TRADING ENGINE

echo  ============================================================

echo.

echo   Starting autopilot brain (7 timeframes, tick by tick)...

echo.

cd /d "%ROOT%"

set PYTHONPATH=.

python arelauncher.py

echo.

pause

goto MENU



:HEALTH_CHECK
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // HEALTH CHECK
echo  ============================================================
echo.

echo  Checking MT5 Server (port 18888)...
curl -s http://127.0.0.1:18888/health >nul 2>&1 && echo   [OK] MT5 Server running || echo   [!!] MT5 Server NOT running

echo  Checking Engine (port %PYTHON_PORT%)...
curl -s http://127.0.0.1:%PYTHON_PORT%/api/status >nul 2>&1 && echo   [OK] Engine running || echo   [!!] Engine NOT running

echo  Checking UI (port %NEXTJS_PORT%)...
curl -s http://127.0.0.1:%NEXTJS_PORT% >nul 2>&1 && echo   [OK] UI running || echo   [!!] UI NOT running

echo.
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
