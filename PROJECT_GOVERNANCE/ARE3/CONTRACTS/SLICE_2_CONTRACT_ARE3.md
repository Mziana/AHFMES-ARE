# SLICE 2 CONTRACT — ARE-3 (Autonomous Science: Isolated Sandbox, Telemetry, Habitat & DB Encapsulation)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **ARE-3 Slice-2**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@b93b7e9` (226 tests pass, Manifest V41)

---

## 1. Lingkup Komponen Slice-2 ARE-3

### A. `CapabilitySandbox` & `SandboxExecutionResult` (`are/sandbox.py`)
- **A1:** Isolasi eksekusi kode riset/kandidat di lingkungan memori terkontrol.
- **A2:** Batas keamanan ketat: penolakan mutlak terhadap akses jaringan/socket (`SandboxSecurityViolation`), zero disk mutation di luar direktori memori temporer, zero akses ke broker API atau modul live trading (Hukum Otoritas Fundamental `THINK -> PROVE -> ACT`).
- **A3:** Penghentian eksekusi jika melebihi batas waktu (*timeout execution*) secara *fail-closed*.

### B. `TelemetryAggregator` & `ExperimentTrace` (`are/telemetry.py`)
- **B1:** Pengumpulan dan agregasi metrik eksekusi riset real-time (latensi, penggunaan memori, skor anomali, konsumsi holdout).
- **B2:** Pencatatan jejak eksperimen (*experiment trace*) secara *append-only* ke dalam `EventStore` pada stream `"research_telemetry"`.
- **B3:** Perhitungan statistik agregat (mean, p50, p95, index stabilitas) secara deterministik.

### C. `HabitatAdapter` & `MarketStateObservation` (`are/habitat.py`)
- **C1:** Jembatan koordinasi memori kondisi pasar multi-agent.
- **C2:** Normalisasi observasi pasar dengan validasi *Information-Time* (penolakan tegas terhadap data masa depan).
- **C3:** Klasifikasi keadaan pasar (*state awareness*) yang terhubung dengan Condition Atlas.

### D. Enkapsulasi Database `EventStore` (`are/storage.py` — Resolusi DEBT-03)
- **D1:** Penambahan metode publik pada `EventStore` (`fetch_all()`, `fetch_one()`, `table_exists()`, `count_events()`).
- **D2:** Refactor `are/evidence.py` dan `are/registry.py` untuk menghapus seluruh pemanggilan langsung ke metode privat `_get_conn()`.

---

## 2. Kriteria Penerimaan Formal (ACC-311 s/d ACC-320)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-311** | Sandbox memblokir percobaan akses jaringan/socket dan raise `SandboxSecurityViolation` | `test_are3_sandbox.py` |
| **ACC-312** | Sandbox membatasi durasi eksekusi dengan timeout fail-closed | `test_are3_sandbox.py` |
| **ACC-313** | Telemetry Aggregator mencatat trace ke `EventStore` pada stream `"research_telemetry"` | `test_are3_telemetry.py` |
| **ACC-314** | Telemetry Aggregator menghitung statistik agregat deterministik (mean, p95, stability) | `test_are3_telemetry.py` |
| **ACC-315** | Habitat Adapter menolak data jika timestamp melebihi cutoff waktu klaim (SC-03) | `test_are3_habitat.py` |
| **ACC-316** | Habitat Adapter mengklasifikasikan kondisi pasar ke dalam Condition Atlas rezim | `test_are3_habitat.py` |
| **ACC-317** | Enkapsulasi `EventStore` (Resolusi DEBT-03): zero bypass `_get_conn()` di `evidence.py` & `registry.py` | `test_are3_storage_api.py` |
| **ACC-318** | Test Integrasi E2E Slice-2 (Sandbox $\rightarrow$ Telemetry $\rightarrow$ Habitat $\rightarrow$ Validation $\rightarrow$ Governor) | `test_are3_e2e_slice2.py` |
| **ACC-319** | Zero external dependencies (murni Python Standard Library) | Code audit |
| **ACC-320** | Seluruh test suite (226 baseline + test baru ARE-3 Slice-2) 100% PASS | `python -m pytest tests/` |

---

## 3. Batasan & Larangan Keras
- **DILARANG** membuka socket, HTTP request, atau koneksi broker di dalam sandbox.
- **DILARANG** melemahkan SQLite trigger append-only atau authorizer fail-closed di `are/storage.py`.
- **DILARANG** menggunakan modul acak `random` tanpa seed deterministik.
