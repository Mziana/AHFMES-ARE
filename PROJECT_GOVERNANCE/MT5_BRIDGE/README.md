# MT5_BRIDGE — MetaTrader 5 Feed Adapter, Execution Gateway & Demo Runner

Status: **WAVE INITIALIZED / IMPLEMENTATION AUTHORIZED**  
Kategori: **MT5_BRIDGE (Live Market Feed & Execution Gateway)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@6a3763d` (281 tests pass, Manifest V41)

---

## Ringkasan Gelombang MT5_BRIDGE

Gelombang **MT5_BRIDGE** menghubungkan engine otonom AHFMES-ARE dengan terminal MetaTrader 5 (MT5):

1. **Market Feed Adapter (`are/mt5_feed.py`):**
   - Menghubungkan ke terminal MT5 (`initialize()`, `login()`, `shutdown()`).
   - Melakukan polling tick dan bar rates secara streaming.
   - Menginjeksi feed live ke `MarketFeatureExtractor` dan `EvidenceLedger`.
   - Menyediakan `MT5MockFeed` deterministik untuk pengujian mandiri tanpa terminal fisik.
2. **Safety-Gated Execution Gateway (`are/mt5_gateway.py`):**
   - Gateway eksekusi order terkunci di balik `CapitalSafetyKernel`.
   - Mengatur perhitungan ukuran lot dinamis berdasarkan equity dan batas risiko.
   - Menyediakan eksekusi order (`BUY`/`SELL`) dan fungsi *Emergency Close All* (`EMERGENCY_FLAT`).
   - Menyediakan `MT5MockGateway` untuk pengujian deterministik.
3. **Live Demo Runner (`are/mt5_runner.py`):**
   - Runner orkestrator yang menghubungkan feed live, evaluasi sinyal Champion, filter CSK, eksekusi order MT5, dan pencatatan telemetri ke `EventStore`.

---

## Subfolder (Mirror Standar Tata Kelola)

| Folder | Isi (MT5_BRIDGE) | Status |
|---|---|:---:|
| `GRAND_DESIGN/` | Desain arsitektur gateway MT5 & risk firewall | `.gitkeep` |
| `AUTHORITY_AND_WORKFLOW/` | Charter MT5 & Delegasi eksekusi | Charter T4 Ratified, DELEGASI_018 |
| `CONTRACTS/` | Kontrak formal Slice-1 MT5_BRIDGE | SLICE_1_CONTRACT_MT5.md (FROZEN) |
| `MACHINE/` | Sumber mesin kanonikal MT5 | `.gitkeep` |
| `MANIFEST/` | Manifest normatif MT5 | Manifest V41 Binding |
| `COUNCIL_PROTOCOL/` | Protokol audit MT5 | `.gitkeep` |
| `QUARANTINE/` | Kebijakan karantina gateway | `.gitkeep` |
| `R9_CORRECTIONS/` | Koreksi dampak | `.gitkeep` |
| `EXTERNAL_AUDIT/` | Handoff & audit eksternal MT5 | `.gitkeep` |
| `QUALIFICATION/` | Bukti kualifikasi internal MT5 | `.gitkeep` |
| `DIARY/` | Diary harian MT5 | 2026-08-28-MT5-OPENING-JURNAL.md |

---

## Titik Baca Cepat (Fase Eksekusi Slice-1 MT5_BRIDGE, Baseline `@6a3763d`)

1. **Entry point otoritas:** `../CURRENT_AUTHORITY_INDEX.md` $\rightarrow$ `MT5_BRIDGE = IMPLEMENTATION AUTHORIZED`
2. **Kontrak Slice-1 (ACTIVE):** `CONTRACTS/SLICE_1_CONTRACT_MT5.md` (ACC-601..610 FROZEN)
3. **Charter Otoritas:** `AUTHORITY_AND_WORKFLOW/IMPLEMENTATION_AUTHORITY_CHARTER_MT5.md` (RATIFIED T4)
4. **Delegasi Aktif:** `AUTHORITY_AND_WORKFLOW/DELEGASI_018_CODING_SLICE1_MT5.md`
5. **Jurnal harian MT5:** `DIARY/2026-08-28-MT5-OPENING-JURNAL.md`
6. **Indeks Progres Global:** `../../PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`
