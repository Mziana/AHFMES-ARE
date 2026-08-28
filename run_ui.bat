@echo off
title AHFMES-ARE Control Center
echo ======================================================================
echo   Launching AHFMES-ARE Control Center & Conversational Copilot...
echo ======================================================================
set PYTHONPATH=.
start "" http://localhost:8080
python -m are.web_ui --db are_interactive.db --port 8080
pause
