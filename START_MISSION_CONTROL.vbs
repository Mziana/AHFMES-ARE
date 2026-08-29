Set WshShell = CreateObject("WScript.Shell")

' 1. Menjalankan Python Core Engine di background (0 = sembunyikan window)
WshShell.Run "cmd /c cd /d D:\Hermes\AHFMES-ARE && set PYTHONPATH=. && python -m are.web_ui --db are_interactive.db --port 8080", 0, False

' 2. Menjalankan Next.js Mission Control UI dalam Mode Produksi Cepat (0 = sembunyikan window)
WshShell.Run "cmd /c cd /d D:\Hermes\AHFMES-ARE\UI && npm run serve", 0, False

' 3. Menunggu 2.5 detik agar server siap
WScript.Sleep 2500

' 4. Membuka browser default langsung ke Mission Control
WshShell.Run "http://127.0.0.1:4028"
