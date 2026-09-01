@echo off
title AHFMES-ARE Launcher v3.0
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
echo           AHFMES-ARE  -  UNIFIED LAUNCHER  v3.0
echo        Autonomous Research Engine Control Center
echo  ============================================================
echo.
echo   [1]  START ARE     (Engine + UI + Live Trading + Chat)
echo   [2]  STATUS        (Check what's running)
echo   [3]  STOP          (Kill all ARE services)
echo.
echo   [0]  Exit
echo.
echo  -------------------------------------------------------------
set /p choice="  Select mode: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto STATUS
if "%choice%"=="3" goto STOP_ALL
if "%choice%"=="0" goto EXIT

echo.
echo  [!] Invalid option. Press any key to try again...
pause >nul
goto MENU

:: ============================================================
::  MODE 1: START EVERYTHING
:: ============================================================
:START_ALL
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // STARTING ALL SERVICES
echo  ============================================================
echo.

:: [1] Start MT5 Server
echo  [1/5] Starting MT5 Server (port 18888)...
start "MT5-Server" /min cmd /c "cd /d "%ROOT%" && python -m are.mt5_server --port 18888"
timeout /t 2 >nul

:: [2] Start Python Engine
echo  [2/5] Starting Python ARE Engine (port %PYTHON_PORT%)...
start "ARE-Engine" /min cmd /c "cd /d "%ROOT%" && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port %PYTHON_PORT%"
timeout /t 2 >nul

:: [3] Start Live Trading Brain
echo  [3/5] Starting Live Trading Brain (7 timeframes)...
start "ARE-LiveBrain" /min cmd /c "cd /d "%ROOT%" && set PYTHONPATH=. && python arelauncher.py"
timeout /t 2 >nul

:: [4] Start Next.js UI + Chat
echo  [4/5] Starting Next.js UI + Chat (port %NEXTJS_PORT%)...
if exist "%ROOT%UI\.next" rd /s /q "%ROOT%UI\.next" 2>nul
start "ARE-UI" /min cmd /c "cd /d "%ROOT%UI" && npm run serve"
timeout /t 3 >nul

:: [5] Open Browser
echo  [5/5] Opening Mission Control Dashboard...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:%NEXTJS_PORT%"

echo.
echo  ============================================================
echo   AHFMES-ARE IS LIVE!
echo  -------------------------------------------------------------
echo   Web UI Dashboard  : http://127.0.0.1:%NEXTJS_PORT%
echo   Python Engine API : http://127.0.0.1:%PYTHON_PORT%
echo   MT5 Server        : http://127.0.0.1:18888
echo   Live Trading      : ACTIVE (7 timeframes, tick by tick)
echo   AI Chat           : Available in Web UI
echo  -------------------------------------------------------------
echo   Tip: This window can be closed (services run in background).
echo         To stop: run ARELauncher.bat and choose [3]
echo  ============================================================
echo.
pause
goto MENU

:: ============================================================
::  MODE 2: STATUS CHECK
:: ============================================================
:STATUS
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // STATUS
echo  ============================================================
echo.

echo  Checking MT5 Server (port 18888)...
curl -s http://127.0.0.1:18888/health >nul 2>&1 && echo   [OK] MT5 Server running || echo   [!!] MT5 Server NOT running

echo  Checking Engine (port %PYTHON_PORT%)...
curl -s http://127.0.0.1:%PYTHON_PORT%/api/status >nul 2>&1 && echo   [OK] Engine running || echo   [!!] Engine NOT running

echo  Checking UI (port %NEXTJS_PORT%)...
curl -s http://127.0.0.1:%NEXTJS_PORT% >nul 2>&1 && echo   [OK] UI running || echo   [!!] UI NOT running

echo  Checking Live Trading Brain...
tasklist /fi "WINDOWTITLE eq ARE-LiveBrain*" 2>nul | findstr /i "cmd.exe" >nul 2>&1 && echo   [OK] Live Trading running || echo   [!!] Live Trading NOT running

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
::  MODE 3: STOP ALL
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

echo  Stopping Engine...
taskkill /f /fi "WINDOWTITLE eq ARE-Engine*" >nul 2>&1

echo  Stopping Live Trading Brain...
taskkill /f /fi "WINDOWTITLE eq ARE-LiveBrain*" >nul 2>&1

echo  Stopping Next.js UI...
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
::  EXIT
:: ============================================================
:EXIT
echo.
echo  Goodbye! AHFMES-ARE services continue running in background.
echo  To stop them, run ARELauncher.bat and choose [3].
echo.
exit /b 0
