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
| `CONTRACTS/` | Kontrak formal Slice-1 WEB_UI | SLICE_1_CONTRACT_WEB_UI.md (FROZEN) |
| `MACHINE/` | Sumber mesin kanonikal WEB_UI | `.gitkeep` |
| `MANIFEST/` | Manifest normatif WEB_UI | Manifest V41 Binding |
| `COUNCIL_PROTOCOL/` | Protokol audit WEB_UI | `.gitkeep` |
| `QUARANTINE/` | Kebijakan karantina UI | `.gitkeep` |
| `R9_CORRECTIONS/` | Koreksi dampak | `.gitkeep` |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal WEB_UI | `.gitkeep` |
| `QUALIFICATION/` | Bukti kualifikasi internal WEB_UI | `.gitkeep` |
| `DIARY/` | Diary harian WEB_UI | 2026-08-28-WEB_UI-OPENING-JURNAL.md |

---

## Titik Baca Cepat (Fase Eksekusi Slice-1 WEB_UI, Baseline `@8323bbb`)

1. **Entry point otoritas:** `../CURRENT_AUTHORITY_INDEX.md` $\rightarrow$ `WEB_UI = IMPLEMENTATION AUTHORIZED`
2. **Kontrak Slice-1 (ACTIVE):** `CONTRACTS/SLICE_1_CONTRACT_WEB_UI.md` (ACC-701..710 FROZEN)
3. **Charter Otoritas:** `AUTHORITY_AND_WORKFLOW/IMPLEMENTATION_AUTHORITY_CHARTER_WEB_UI.md` (RATIFIED T4)
4. **Delegasi Aktif:** `AUTHORITY_AND_WORKFLOW/DELEGASI_019_CODING_SLICE1_WEB_UI.md`
5. **Jurnal harian WEB_UI:** `DIARY/2026-08-28-WEB_UI-OPENING-JURNAL.md`
6. **Indeks Progres Global:** `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`
