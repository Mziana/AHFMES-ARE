@echo off
cd /d "%~dp0"

rem E-3: pin interpreter ke python yang punya MetaTrader5.
rem Shell `python` (WindowsApps shim) TIDAK dijamin punya MetaTrader5/polars.
rem Fail-loud: bila path ini hilang, jangan fallback diam ke `python` bare.
rem Bila suatu hari dibuat venv proyek, ganti MT5_PY di file ini satu tempat.
set "MT5_PY=C:\Users\Fajar\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if not exist "%MT5_PY%" (
    echo [FATAL] Interpreter MetaTrader5 tidak ditemukan: "%MT5_PY%"
    echo Shell python shim WindowsApps tidak dijamin punya MetaTrader5.
    echo Buat venv proyek utk fix permanen, lalu ganti MT5_PY di file ini.
    exit /b 1
)

"%MT5_PY%" -m are.mt5_server --port 18888
