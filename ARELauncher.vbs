Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get script directory
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' ============================================================
'   AHFMES-ARE SILENT LAUNCHER
'   Starts Engine + UI in background, opens browser
' ============================================================

' 1. Start Python ARE Engine (hidden)
WshShell.Run "cmd /c cd /d """ & scriptDir & """ && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port 8080", 0, False

' 2. Wait for engine to initialize
WScript.Sleep 2500

' 3. Start Next.js UI (hidden)
WshShell.Run "cmd /c cd /d """ & scriptDir & "\UI"" && npm run serve", 0, False

' 4. Wait for UI to build
WScript.Sleep 3000

' 5. Open browser to Mission Control
WshShell.Run "http://127.0.0.1:4028"
