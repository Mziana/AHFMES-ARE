# DELEGASI 019 — Engineering AI: Coding WEB_UI (Localhost Control Center & Conversational Chat Copilot)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@8323bbb` (289 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_019 — CODING WEB_UI — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 8323bbb (MT5_BRIDGE CLOSED, 289 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/WEB_UI/CONTRACTS/SLICE_1_CONTRACT_WEB_UI.md

═══════════════════════════════════════════════════════
BAGIAN A — are/web_ui.py (WEB SERVER & REST API BACKEND)
═══════════════════════════════════════════════════════
Buat `are/web_ui.py` (stdlib only: http.server, json, os, time, threading, urllib, typing):
- Kelas `AREAPIHandler(http.server.BaseHTTPRequestHandler)`:
  - Menyajikan `GET /`: file `are/web/index.html`.
  - Endpoint REST API:
    1. `GET /api/status`: Mengembalikan json `{ "champion": {...}, "safety": {...}, "stream_stats": {...}, "server_time": ... }`.
    2. `POST /api/run-cycle`: Membaca json `{ "symbol": "BTCUSD" }`, memanggil `P001ProgramRunner.run_program()`, mengembalikan ringkasan riset & champion baru.
    3. `POST /api/kill-switch`: Membaca json `{ "active": true/false }`, mengubah status `CapitalSafetyKernel.limits.kill_switch_active`.
    4. `POST /api/step-tick`: Membaca json `{ "symbol": "BTCUSD", "price": ..., "imbalance": ..., ... }`, memproses tick via `OperationalBrain.process_tick()`, mengembalikan hasil aksi & keputusan CSK.
    5. `GET /api/champion-history`: Mengembalikan list event dari stream `champion_registry`.
    6. `POST /api/chat`: AI Copilot handler yang memproses pesan `{ "message": "..." }` dan merespons secara kontekstual:
       - Menjelaskan status champion aktif, batas risiko CSK, statistik tick, atau memicu aksi langsung (misal: "jalankan riset", "aktifkan kill switch").
       - Menjawab dalam Bahasa Indonesia yang informatif dan ramah kuantitatif.
- Fungsi `run_server(db_path: str = "are_interactive.db", host: str = "127.0.0.1", port: int = 8080) -> None`.
- Main entry point: `python -m are.web_ui --db are_interactive.db --port 8080`.

═══════════════════════════════════════════════════════
BAGIAN B — are/web/index.html (GLASSMORPHISM SINGLE PAGE APP)
═══════════════════════════════════════════════════════
Buat direktori `are/web/` dan file `are/web/index.html`:
- Frontend lengkap mandiri (HTML5 + Embedded Modern CSS + JavaScript):
  - **Desain**: *Dark Quant / Cyberpunk aesthetic* dengan Glassmorphism (semi-transparan, glowing accents, font monospaced & sleek sans-serif).
  - **Header**: Logo "AHFMES-ARE Control Center", status badge, dan toggle button Kill-Switch.
  - **Grid Layout**:
    1. *Active Champion Card*: Info Champion ID, Candidate ID, Tanggal Aktivasi, Status.
    2. *Capital Safety Firewall Card*: Max Drawdown, Volatility Cutoff, Rate Limit, Kill-Switch Status.
    3. *Operational Stats Card*: Total Ticks, Veto Ratio, Hash Chain Integrity.
    4. *Action Hub Panel*: Tombol aksi:
       - 🚀 `Run Autonomous Research Cycle`
       - ⚡ `Inject Market Shock / Tick`
       - 🛑 `Emergency Kill Switch`
       - 🔄 `Refresh Status`
    5. *Live Chart Panel*: Grafik harga & sinyal (menggunakan Chart.js via CDN `https://cdn.jsdelivr.net/npm/chart.js`).
    6. *ARE Conversational Copilot (Chat Panel)*:
       - Kotak obrolan dengan bubble pesan user & AI.
       - Input text & tombol kirim (Enter to send).
       - Menampilkan respons cerdas dan tombol aksi cepat (*Quick Prompts*).

═══════════════════════════════════════════════════════
BAGIAN C — run_ui.bat (1-CLICK WINDOWS LAUNCHER)
═══════════════════════════════════════════════════════
Buat `run_ui.bat` di root direktori:
```cmd
@echo off
title AHFMES-ARE Control Center
echo ======================================================================
echo   Launching AHFMES-ARE Control Center & Conversational Copilot...
echo ======================================================================
set PYTHONPATH=.
start "" http://localhost:8080
python -m are.web_ui --db are_interactive.db --port 8080
pause
```

═══════════════════════════════════════════════════════
BAGIAN D — PENGUJIAN UNIT & INTEGRASI (tests/are/)
═══════════════════════════════════════════════════════
Buat `tests/are/test_web_ui.py`:
- Menguji seluruh endpoint API (`/api/status`, `/api/run-cycle`, `/api/kill-switch`, `/api/step-tick`, `/api/champion-history`, `/api/chat`).
- Menguji serving file `index.html`.

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-701 s/d ACC-710 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (289 baseline + test baru WEB_UI).
  Zero external backend dependencies (Python Standard Library only untuk server & API).
  Zero test regression (seluruh 289 test lama lulus 100%).
  Working tree clean.

PROSES
1. Buat `are/web/index.html`, `are/web_ui.py`, `run_ui.bat`.
2. Buat `tests/are/test_web_ui.py`.
3. Jalankan `python -m pytest tests/ -q` -> pastikan seluruh 289+ test PASS.
4. Commit di main: "feat(ui): implement Localhost Control Center & Interactive Chat Copilot (DELEGASI_019)"
5. Laporkan hasilnya ke Lead Architect.
```
