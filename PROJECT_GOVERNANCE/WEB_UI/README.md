# WEB_UI — Localhost Control Center & Interactive Chat Copilot

Status: **WAVE INITIALIZED / IMPLEMENTATION AUTHORIZED**  
Kategori: **WEB_UI (Interactive Dashboard & Conversational Copilot)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@8323bbb` (289 tests pass, Manifest V41)

---

## Ringkasan Gelombang WEB_UI

Gelombang **WEB_UI** membangun antarmuka pengguna visual dan pusat kendali interaktif untuk AHFMES-ARE:

1. **Localhost Web Server & REST API (`are/web_ui.py`):**
   - Server web berbasis Python Standard Library (`http.server` & `ThreadingHTTPServer`).
   - Endpoint API untuk status sistem, pemicu siklus riset, pengubah status kill-switch, simulasi tick, riwayat champion, dan chatbot AI Copilot.
2. **Cyberpunk/Quant Dark Theme SPA (`are/web/index.html`):**
   - Single Page Application modern dengan Glassmorphism CSS, responsif, dan interaktif.
   - Grafik harga live, orderbook depth, panel Champion aktif, dan status firewall risiko CSK.
3. **ARE Conversational Chat Copilot:**
   - Panel obrolan interaktif terintegrasi yang terhubung ke database dan engine internal AHFMES-ARE untuk berinteraksi dalam Bahasa Indonesia.
4. **1-Click Windows Launcher (`run_ui.bat`):**
   - Peluncur 1-klik untuk menjalankan server dan langsung membuka dashboard di browser.

---

## Subfolder (Mirror Standar Tata Kelola)

| Folder | Isi (WEB_UI) | Status |
|---|---|:---:|
| `GRAND_DESIGN/` | Desain arsitektur UI & protokol chat | `.gitkeep` |
| `AUTHORITY_AND_WORKFLOW/` | Charter WEB_UI & Delegasi eksekusi | Charter T4 Ratified, DELEGASI_019 |
| `CONTRACTS/` | Kontrak formal Slice-1 WEB_UI | SLICE_1_CONTRACT_WEB_UI.md (CERTIFIED) |
| `MACHINE/` | Sumber mesin kanonikal WEB_UI | `.gitkeep` |
| `MANIFEST/` | Manifest normatif WEB_UI | Manifest V41 Binding |
| `COUNCIL_PROTOCOL/` | Protokol audit WEB_UI | `.gitkeep` |
| `QUARANTINE/` | Kebijakan karantina UI | `.gitkeep` |
| `R9_CORRECTIONS/` | Koreksi dampak | `.gitkeep` |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal WEB_UI | AHFMES_WEB_UI_CANDIDATE_HANDOFF.md |
| `QUALIFICATION/` | Bukti kualifikasi internal WEB_UI | AHFMES_WEB_UI_SLICE1_AUDIT_REPORT.md (10/10 PASS) |
| `DIARY/` | Diary harian WEB_UI | 2026-08-28-WEB_UI-OPENING-JURNAL.md, 2026-08-28-WEB_UI-CLOSING-JURNAL.md |

---

## Titik Baca Cepat (Fase Penutupan WEB_UI, Baseline `@9d0f5d3`)

1. **Entry point otoritas:** `../CURRENT_AUTHORITY_INDEX.md` $\rightarrow$ `WEB_UI CLOSED & CERTIFIED`
2. **Kontrak Slice-1 (CERTIFIED):** `CONTRACTS/SLICE_1_CONTRACT_WEB_UI.md` (ACC-701..710 PASS)
3. **Laporan Audit Akhir:** `QUALIFICATION/AHFMES_WEB_UI_SLICE1_AUDIT_REPORT.md` (295/295 tests pass)
4. **Handoff Dossier:** `EXTERNAL_AUDIT/AHFMES_WEB_UI_CANDIDATE_HANDOFF.md`
5. **Jurnal Penutupan:** `DIARY/2026-08-28-WEB_UI-CLOSING-JURNAL.md`
6. **Indeks Progres Global:** `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`
