# DELEGASI 011 — Engineering AI: Coding Slice-2 ARE-3 (Sandbox, Telemetry, Habitat & DB Encapsulation)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@b93b7e9` (226 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_011 — CODING SLICE-2 ARE-3 — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = b93b7e9 (ARE-3 Slice-1 CLOSED, 226 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/ARE3/CONTRACTS/SLICE_2_CONTRACT_ARE3.md

═══════════════════════════════════════════════════════
BAGIAN A — ENKAPSULASI EVENTSTORE (Resolusi DEBT-03)
═══════════════════════════════════════════════════════

1. Buka file: `are/storage.py` (`EventStore`)
   - Tambahkan public query methods resmi pada kelas `EventStore` untuk kebutuhan read internal terenkapsulasi:
     * `fetch_all(query: str, params: tuple = ()) -> List[Tuple[Any, ...]]`
     * `fetch_one(query: str, params: tuple = ()) -> Optional[Tuple[Any, ...]]`
     * `table_exists(table_name: str) -> bool`
     * `count_events(stream_id: str) -> int`
   - Pastikan metode-metode ini tetap menggunakan koneksi yang dilindungi `_authorizer` fail-closed (menolak DROP TABLE, DROP TRIGGER, ATTACH).
2. Refactor `are/evidence.py` dan `are/registry.py`:
   - Gantikan seluruh pemanggilan langsung `self.event_store._get_conn()` atau `self._event_store._get_conn()` dengan public query methods di atas.
   - Hapus seluruh akses ke attribute privat `_get_conn` dari luar `storage.py`.
   - Jalankan test: pastikan seluruh 226 test baseline tetap 100% PASS.

═══════════════════════════════════════════════════════
BAGIAN B — ISOLATED CAPABILITY SANDBOX (are/sandbox.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/sandbox.py`
1. Exception `SandboxSecurityViolation(Exception)` & `SandboxTimeoutError(Exception)`
2. Dataclass `SandboxExecutionResult`:
   - Fields: success: bool, output: Any, error: Optional[str], execution_time_ms: float, memory_bytes: int, violation_detected: bool
3. Kelas `CapabilitySandbox`:
   - Metode `execute(func: Callable, args: tuple = (), kwargs: dict = None, timeout_sec: float = 2.0) -> SandboxExecutionResult`:
     * Isolasi eksekusi dari socket/network I/O (patch/block `socket.socket` dan `urllib.request` selama eksekusi; jika terpanggil, raise `SandboxSecurityViolation`).
     * Monitor waktu eksekusi: jika melebihi `timeout_sec`, gagalkan dengan `SandboxTimeoutError` (*fail-closed*).
     * Pastikan eksekusi murni deterministik.

═══════════════════════════════════════════════════════
BAGIAN C — TELEMETRY AGGREGATOR (are/telemetry.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/telemetry.py`
1. Dataclass `ExperimentTrace`:
   - Fields: experiment_id: str, candidate_id: str, timestamp: float, metrics: Dict[str, float], tags: List[str], trace_hash: str
2. Kelas `TelemetryAggregator`:
   - Inisialisasi: Menerima `event_store: EventStore`.
   - `record_trace(trace: ExperimentTrace) -> str`: Menyimpan event telemetri ke `EventStore` stream `"research_telemetry"`.
   - `get_experiment_traces(candidate_id: str) -> List[ExperimentTrace]`: Mengambil histori telemetri kandidat.
   - `compute_aggregate_metrics(candidate_id: str) -> Dict[str, float]`: Menghitung agregat deterministik (mean, median/p50, p95, stability_index).

═══════════════════════════════════════════════════════
BAGIAN D — HABITAT ADAPTER & MARKET STATE (are/habitat.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/habitat.py`
1. Dataclass `MarketStateObservation`:
   - Fields: observation_id: str, symbol: str, timestamp: float, regime: str, features: Dict[str, float], observation_hash: str
2. Kelas `ConditionAtlas`:
   - Mendaftarkan rezim-rezim kondisi pasar valid: `"TRENDING_EXPANSION"`, `"RANGE_COMPRESSION"`, `"VOLATILITY_EXPANSION"`, `"REGIME_TRANSITION"`.
   - `classify_regime(features: Dict[str, float]) -> str`: Mengklasifikasikan rezim pasar secara deterministik.
3. Kelas `HabitatAdapter`:
   - Inisialisasi: Menerima `condition_atlas: ConditionAtlas` dan `event_store: EventStore`.
   - `ingest_market_state(symbol: str, timestamp: float, features: Dict[str, float], as_of_cutoff: float) -> MarketStateObservation`:
     * Validasi Information-Time (SC-03): Jika `timestamp > as_of_cutoff`, raise `ValueError("Future timestamp violation")`.
     * Mengklasifikasikan rezim menggunakan Condition Atlas.
     * Mengembalikan objek `MarketStateObservation` terverifikasi hash.

═══════════════════════════════════════════════════════
BAGIAN E — TEST SUITES BARU ARE-3 SLICE-2 (tests/are/)
═══════════════════════════════════════════════════════

Buat modul pengujian komprehensif di `tests/are/`:
1. `tests/are/test_are3_storage_api.py`: Menguji public query API EventStore dan ketiadaan pemanggilan `_get_conn` di luar `storage.py` (ACC-317).
2. `tests/are/test_are3_sandbox.py`: Menguji isolasi socket, timeout fail-closed, dan eksekusi deterministik (ACC-311, ACC-312).
3. `tests/are/test_are3_telemetry.py`: Menguji pencatatan trace ke EventStore dan kalkulasi agregat (ACC-313, ACC-314).
4. `tests/are/test_are3_habitat.py`: Menguji Information-Time cutoff, klasifikasi rezim Condition Atlas (ACC-315, ACC-316).
5. `tests/are/test_are3_e2e_slice2.py`: Menguji integrasi E2E Slice-2 penuh (Sandbox $\rightarrow$ Telemetry $\rightarrow$ Habitat $\rightarrow$ Validation $\rightarrow$ Governor) (ACC-318).

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-311 s/d ACC-320 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (226 baseline + test baru ARE-3 Slice-2).
  Zero external dependencies (Python Standard Library only).
  Working tree clean.

LARANGAN
- Dilarang menyentuh broker API, socket live trading, atau eksekusi modal.
- Dilarang melemahkan authorizer atau triggers append-only di are/storage.py.
- Dilarang menggunakan modul random tanpa seed deterministik.

PROSES
1. Tambahkan public methods di EventStore (are/storage.py) dan refactor evidence.py & registry.py -> jalankan 226 test tetap hijau.
2. Implementasikan Bagian B (sandbox.py), Bagian C (telemetry.py), Bagian D (habitat.py).
3. Buat test suite Bagian E di tests/are/.
4. Jalankan full test suite -> pastikan seluruh test PASS.
5. Commit di main: "feat(are3): implement Slice-2 Sandbox, Telemetry, Habitat & DB Encapsulation (DELEGASI_011)"
6. Laporkan hasilnya ke Lead Architect.
```
