# SLICE 1 CONTRACT — WEB_UI (Localhost Control Center & Interactive Chat Copilot)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **WEB_UI Slice-1**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@8323bbb` (289 tests pass, Manifest V41)

---

## 1. Lingkup Komponen WEB_UI Slice-1

### A. Web Server & REST API (`are/web_ui.py`)
- Server HTTP berbasis `http.server.ThreadingHTTPServer` (stdlib only):
  1. `GET /`: Menyajikan Single Page Application `are/web/index.html`.
  2. `GET /api/status`: Mengembalikan status sistem (Active Champion, CSK limits, Total operational ticks, Veto count, Hash integrity).
  3. `POST /api/run-cycle`: Memicu `P001ProgramRunner.run_program()` untuk riset alpha mandiri.
  4. `POST /api/kill-switch`: Mengaktifkan/menonaktifkan kill-switch CSK secara instan.
  5. `POST /api/step-tick`: Memproses simulasi/live operational tick dengan ekstraksi fitur & evaluasi Brain.
  6. `GET /api/champion-history`: Daftar riwayat suksesi champion dari `ChampionRegistry`.
  7. `POST /api/chat`: AI Conversational Copilot yang memproses pesan bahasa alami dan merespons dengan data analitik sistem serta mengeksekusi aksi relevan.

### B. Glassmorphism SPA Frontend (`are/web/index.html`)
- Desain antarmuka futuristik (*Dark Quant / Cyberpunk aesthetic*):
  1. Multi-panel cards: Active Champion, CSK Risk Firewall, Stream Health.
  2. Action Hub: Tombol eksekusi *Run Research Cycle*, *Inject Market Scenario*, *Toggle Kill Switch*.
  3. Real-Time Price & Indicator Chart (Chart.js via CDN).
  4. Panel Chat Interaktif: Percakapan real-time dengan ARE Copilot.

### C. 1-Click Windows Launcher (`run_ui.bat`)
- Batch script sederhana yang mengaktifkan server di port `8080` dan membuka browser default.

---

## 2. Kriteria Penerimaan Formal (ACC-701 s/d ACC-710)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-701** | `are/web_ui.py` menyajikan REST API lengkap dan melayani file SPA secara thread-safe | `test_web_ui.py` |
| **ACC-702** | `GET /api/status` mengembalikan status Champion, CSK, dan EventStore hash chain valid | API test |
| **ACC-703** | `POST /api/run-cycle` berhasil memicu siklus riset otonom baru dan mempromosikan champion | API test |
| **ACC-704** | `POST /api/kill-switch` mengubah state CSK kill-switch secara instan | API test |
| **ACC-705** | `POST /api/chat` memproses pertanyaan bahasa alami dan merespons analitik sistem yang relevan | API test |
| **ACC-706** | `are/web/index.html` menyajikan visual dashboard lengkap, grafik, dan panel chat interaktif | Inspection |
| **ACC-707** | `run_ui.bat` tersedia di root untuk peluncuran 1-klik di Windows | Inspection |
| **ACC-708** | Zero external backend dependencies (Python Standard Library only) | Code audit |
| **ACC-709** | Seluruh test suite (289 baseline + test baru WEB_UI) 100% PASS | `python -m pytest tests/` |
| **ACC-710** | Repositori bersih tanpa file sementara (`working tree clean`) | `git status` |

---

## 3. Batasan & Larangan Keras
- **DILARANG** menambahkan framework backend pihak ketiga (Flask, FastAPI, Django).
- **WAJIB** melayani semua endpoint API secara deterministik, thread-safe, dan fail-closed.
