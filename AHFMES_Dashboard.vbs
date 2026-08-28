Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Launch AHFMES-ARE Web Server silently in the background (0 = hide window)
WshShell.Run "cmd /c set PYTHONPATH=. && python -m are.web_ui --port 8080", 0, False

' Pause 1.5 seconds to allow the server to bind the port and start
WScript.Sleep 1500

' Open the interactive dashboard in default web browser
WshShell.Run "http://127.0.0.1:8080"
