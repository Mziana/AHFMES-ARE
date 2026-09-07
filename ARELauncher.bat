@echo off
title AHFMES-ARE Launcher v4.0
color 0A

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "NEXTJS_PORT=4028"
set "BRIDGE_PORT=18888"
set "LOG_DIR=%ROOT%data\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

rem P0-01: bridge auth token (dibaca sekali untuk semua mode)
set "BRIDGE_TOKEN_VALUE="
if exist "%ROOT%data\bridge_token.txt" set /p BRIDGE_TOKEN_VALUE=<"%ROOT%data\bridge_token.txt"

rem E-3: pin interpreter bridge ke python dgn MetaTrader5 (sama dgn run_bridge.bat).
rem Shell `python` (WindowsApps shim) tidak dijamin punya MetaTrader5.
set "MT5_PY=C:\Users\Fajar\AppData\Local\Python\pythoncore-3.14-64\python.exe"

:MENU
cls
echo.
echo  ============================================================
echo           AHFMES-ARE  -  LAUNCHER v4.0
echo        Autonomous Research Engine Control Center
echo  ============================================================
echo.
echo   [1]  START ALL     (Bridge + UI + Bot Micro)
echo   [2]  START BOT     (Start bot micro only)
echo   [3]  STOP ALL      (Kill all ARE services)
echo   [4]  STATUS        (Check what's running)
echo.
echo   [0]  Exit (services keep running)
echo.
echo  -------------------------------------------------------------
set /p choice="  Select mode: "

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto START_BOT
if "%choice%"=="3" goto STOP_ALL
if "%choice%"=="4" goto STATUS
if "%choice%"=="0" goto EXIT
echo  [!] Invalid option.
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

:: [1] MT5 Bridge
echo  [1/4] Checking MT5 Bridge (port %BRIDGE_PORT%)...
curl -s --max-time 3 -H "X-Bridge-Token: %BRIDGE_TOKEN_VALUE%" http://127.0.0.1:%BRIDGE_PORT%/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] MT5 Bridge already running
    goto BRIDGE_OK
)
echo   Starting MT5 Bridge...
start "ARE-Bridge" /min cmd /c "cd /d %ROOT% && set ARE_BRIDGE_TOKEN=%BRIDGE_TOKEN_VALUE% && %MT5_PY% -m are.mt5_server --port %BRIDGE_PORT% > %LOG_DIR%\bridge.log 2>&1"
echo   Waiting for Bridge...
timeout /t 5 /nobreak >nul
curl -s --max-time 3 -H "X-Bridge-Token: %BRIDGE_TOKEN_VALUE%" http://127.0.0.1:%BRIDGE_PORT%/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] MT5 Bridge started
) else (
    echo   [!!] Bridge may need more time - check STATUS later
)
:BRIDGE_OK

:: [2] UI
echo.
echo  [2/4] Checking Next.js UI (port %NEXTJS_PORT%)...
curl -s --max-time 3 http://127.0.0.1:%NEXTJS_PORT% >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] UI already running
    goto UI_OK
)
echo   Starting Next.js UI...
start "ARE-UI" /min cmd /c "cd /d %ROOT%UI && npm run dev > %LOG_DIR%\ui.log 2>&1"
echo   Waiting for UI to compile...
:WAIT_UI
timeout /t 3 /nobreak >nul
curl -s --max-time 3 http://127.0.0.1:%NEXTJS_PORT% >nul 2>&1
if %errorlevel% neq 0 goto WAIT_UI
echo   [OK] UI started
:UI_OK

:: [3] Account check
echo.
echo  [3/4] Checking account...
curl -s --max-time 5 -H "X-Bridge-Token: %BRIDGE_TOKEN_VALUE%" http://127.0.0.1:%BRIDGE_PORT%/account 2>nul | python -c "import json,sys; d=json.load(sys.stdin); print('   Balance: $%.2f | Positions: %d' % (d.get('balance',0), d.get('position_count',0)))" 2>nul

:: [4] Bot Micro
echo.
echo  [4/4] Starting Bot Micro via API...
curl -s --max-time 10 -X POST http://127.0.0.1:%NEXTJS_PORT%/api/are/bot/start -H "Content-Type: application/json" -d "{\"style\":\"micro\"}" > "%LOG_DIR%\bot_start.json" 2>&1
findstr /c:"pid" "%LOG_DIR%\bot_start.json" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Bot Micro started
) else (
    echo   [!!] Check bot_start.json for details
)

echo.
echo  ============================================================
echo   AHFMES-ARE IS LIVE!
echo  -------------------------------------------------------------
echo   UI  : http://127.0.0.1:%NEXTJS_PORT%
echo   Bridge : http://127.0.0.1:%BRIDGE_PORT%
echo   Bot Micro : RUNNING
echo  -------------------------------------------------------------
echo   This window can be closed. Services run independently.
echo   To stop: ARELauncher.bat ^> [3] STOP ALL
echo  ============================================================
pause
goto MENU

:: ============================================================
::  MODE 2: START BOT ONLY
:: ============================================================
:START_BOT
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // START BOT MICRO
echo  ============================================================
echo.
curl -s --max-time 3 -H "X-Bridge-Token: %BRIDGE_TOKEN_VALUE%" http://127.0.0.1:%BRIDGE_PORT%/health >nul 2>&1
if %errorlevel% neq 0 (
    echo   [!!] MT5 Bridge NOT running. Run [1] START ALL first.
    pause
    goto MENU
)
curl -s --max-time 3 http://127.0.0.1:%NEXTJS_PORT% >nul 2>&1
if %errorlevel% neq 0 (
    echo   [!!] UI NOT running. Run [1] START ALL first.
    pause
    goto MENU
)
echo   Starting Bot Micro via API...
curl -s --max-time 10 -X POST http://127.0.0.1:%NEXTJS_PORT%/api/are/bot/start -H "Content-Type: application/json" -d "{\"style\":\"micro\"}" 2>&1
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

echo  Stopping Bot Micro via API...
curl -s --max-time 5 -X POST http://127.0.0.1:%NEXTJS_PORT%/api/are/bot/stop -H "Content-Type: application/json" -d "{\"style\":\"micro\"}" >nul 2>&1

echo  Killing bot.py processes...
wmic process where "commandline like '%%bot.py%%'" call terminate >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ARE-Bot*" >nul 2>&1

echo  Stopping MT5 Bridge...
curl -s --max-time 3 -H "X-Bridge-Token: %BRIDGE_TOKEN_VALUE%" http://127.0.0.1:%BRIDGE_PORT%/shutdown >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%BRIDGE_PORT%" ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

echo  Stopping Next.js UI...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%NEXTJS_PORT%" ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

taskkill /f /fi "WINDOWTITLE eq ARE-*" >nul 2>&1

echo.
echo   All services stopped.
pause
goto MENU

:: ============================================================
::  MODE 4: STATUS
:: ============================================================
:STATUS
cls
echo.
echo  ============================================================
echo   AHFMES-ARE // STATUS
echo  ============================================================
echo.

echo  MT5 Bridge (port %BRIDGE_PORT%)...
curl -s --max-time 3 -H "X-Bridge-Token: %BRIDGE_TOKEN_VALUE%" http://127.0.0.1:%BRIDGE_PORT%/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Running
    curl -s --max-time 3 http://127.0.0.1:%BRIDGE_PORT%/account 2>nul | python -c "import json,sys; d=json.load(sys.stdin); print('   Balance: $%.2f | Positions: %d' % (d.get('balance',0), d.get('position_count',0)))" 2>nul
) else (
    echo   [!!] NOT running
)

echo.
echo  Next.js UI (port %NEXTJS_PORT%)...
curl -s --max-time 3 http://127.0.0.1:%NEXTJS_PORT% >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Running
) else (
    echo   [!!] NOT running
)

echo.
echo  Bot Micro...
curl -s --max-time 5 http://127.0.0.1:%NEXTJS_PORT%/api/are/bot/status?style=micro 2>nul | python -c "import json,sys; d=json.load(sys.stdin); print('   [%s] PID: %s | Trades: %s | P&L: $%s' % ('OK' if d.get('status')=='running' else 'OFF', d.get('pid','?'), d.get('trade_count',0), d.get('daily_pnl',0)))" 2>nul || echo   [!!] Not responding

echo.
pause
goto MENU

:EXIT
echo.
echo  Services keep running in background.
echo  To stop: ARELauncher.bat ^> [3] STOP ALL
echo.
exit /b 0
