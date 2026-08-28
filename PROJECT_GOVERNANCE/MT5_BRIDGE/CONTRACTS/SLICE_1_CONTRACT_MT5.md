# SLICE 1 CONTRACT — MT5_BRIDGE (Live Feed, Execution Gateway & Demo Runner)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **MT5_BRIDGE Slice-1**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@6a3763d` (281 tests pass, Manifest V41)

---

## 1. Lingkup Komponen MT5_BRIDGE Slice-1

### A. MetaTrader 5 Live Feed Adapter (`are/mt5_feed.py`)
- Mengelola koneksi data ke terminal MT5:
  1. `MT5FeedConfig`: konfigurasi terminal path, login, server, password, timeframe.
  2. `MT5MarketFeed`: metode `initialize()`, `get_latest_ticks()`, `get_latest_bars()`, `shutdown()`.
  3. `MT5MockFeed`: simulator feed pasar deterministik untuk pengujian offline tanpa terminal fisik.
  4. Integrasi langsung ke `MarketFeatureExtractor` dan `EvidenceLedger` (ACC-601, ACC-602).

### B. Safety-Gated Execution Gateway (`are/mt5_gateway.py`)
- Gateway eksekusi order terkunci di balik `CapitalSafetyKernel`:
  1. `MT5OrderRequest`: container data order (`symbol`, `volume`, `order_type`, `price`, `sl`, `tp`, `magic_number`).
  2. `MT5ExecutionGateway`:
     - Verifikasi CSK wajib (`CapitalSafetyKernel.evaluate_order_intent()`): menolak order jika `allowed == False`.
     - Perhitungan lot otomatis (*position clamping*): proporsional terhadap *equity* akun & parameter risiko.
     - `send_order()`: memicu eksekusi order ke MT5.
     - `close_all_positions()`: fungsi *Emergency Flat* otomatis menutup seluruh trade terbuka saat sinyal kill-switch aktif.
  3. `MT5MockGateway`: simulator pencatatan eksekusi trade untuk pengujian mandiri (ACC-603, ACC-604).

### C. Live Demo Runner (`are/mt5_runner.py`)
- `MT5LiveRunner`:
  1. Mengorkestrasikan *Live Feed Polling* $\rightarrow$ *Feature Extraction* $\rightarrow$ *Champion Signal Evaluation* $\rightarrow$ *CSK Safety Check* $\rightarrow$ *MT5 Gateway Execution*.
  2. Mencatat setiap operational tick dan hasil eksekusi trade ke `EventStore` (`operational_signals` stream) dan `EvidenceLedger` (ACC-605).

---

## 2. Kriteria Penerimaan Formal (ACC-601 s/d ACC-610)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-601** | `are/mt5_feed.py` menyediakan parsing tick/bar dan feed polling (live & mock mode) | `test_mt5_feed.py` |
| **ACC-602** | `MT5MarketFeed` terhubung mulus dengan `MarketFeatureExtractor` | Unit test integrasi |
| **ACC-603** | `are/mt5_gateway.py` menolak seluruh order jika `CapitalSafetyKernel` memberikan veto | `test_mt5_gateway.py` |
| **ACC-604** | `MT5ExecutionGateway` mengeksekusi `close_all_positions()` saat status `EMERGENCY_FLAT` | Test kill-switch |
| **ACC-605** | `are/mt5_runner.py` mengorkestrasikan alur live end-to-end secara deterministik & thread-safe | `test_mt5_runner.py` |
| **ACC-606** | Zero external hard-dependencies (fallback murni stdlib jika library `MetaTrader5` tidak terinstal) | Code audit |
| **ACC-607** | Seluruh test suite (281 baseline + test baru MT5_BRIDGE) 100% PASS | `python -m pytest tests/` |
| **ACC-608** | Repositori bersih tanpa file sementara (`working tree clean`) | `git status` |
| **ACC-609** | Dual-implementation `manifest_hash` & `blob_verifier` 100% PASS | `TOOLS/` verification |
| **ACC-610** | Gerbang modal live terkunci aman (*fail-closed firewall protection*) | Strict risk audit |

---

## 3. Batasan & Larangan Keras
- **DILARANG** melewati (*bypass*) `CapitalSafetyKernel` dalam kondisi apa pun saat mengirim order.
- **WAJIB** menyediakan fallback mock mode agar test suite dapat berjalan 100% di semua lingkungan.
