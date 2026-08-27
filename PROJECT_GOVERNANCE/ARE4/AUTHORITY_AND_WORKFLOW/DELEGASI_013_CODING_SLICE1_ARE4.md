# DELEGASI 013 — Engineering AI: Coding Slice-1 ARE-4 (Capital Safety Kernel & Operational Brain)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@ebf931d` (246 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_013 — CODING SLICE-1 ARE-4 — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = ebf931d (ARE-3 CLOSED, 246 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/ARE4/CONTRACTS/SLICE_1_CONTRACT_ARE4.md

═══════════════════════════════════════════════════════
BAGIAN A — CAPITAL SAFETY KERNEL (are/safety.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/safety.py`
1. Dataclass `SafetyLimits`:
   - Fields: max_position_size: float = 1.0, max_drawdown_pct: float = 0.15, volatility_cutoff: float = 2.5, max_order_rate_per_min: int = 10, kill_switch_active: bool = False
2. Dataclass `SafetyDecision`:
   - Fields: allowed: bool, action: str ("EXECUTE" / "ABSTAIN" / "EMERGENCY_FLAT"), clamped_size: float, reason: str, decision_hash: str = ""
   - `__post_init__` menghitung sha256 `decision_hash` kanonikal.
3. Kelas `CapitalSafetyKernel`:
   - Inisialisasi: `limits: Optional[SafetyLimits] = None`
   - `evaluate_action(intended_action: Dict[str, Any], current_drawdown: float, current_volatility: float, recent_order_count: int, emergency_signal: bool = False) -> SafetyDecision`:
     * 1. Jika `emergency_signal or self.limits.kill_switch_active` $\rightarrow$ return `SafetyDecision(allowed=False, action="EMERGENCY_FLAT", clamped_size=0.0, reason="Emergency kill switch triggered (ACC-401)")`.
     * 2. Jika `current_drawdown >= self.limits.max_drawdown_pct` $\rightarrow$ return `SafetyDecision(allowed=False, action="ABSTAIN", clamped_size=0.0, reason="Max drawdown threshold exceeded (ACC-402)")`.
     * 3. Jika `current_volatility >= self.limits.volatility_cutoff` $\rightarrow$ return `SafetyDecision(allowed=False, action="ABSTAIN", clamped_size=0.0, reason="Market volatility cutoff breached (ACC-403)")`.
     * 4. Jika `recent_order_count >= self.limits.max_order_rate_per_min` $\rightarrow$ return `SafetyDecision(allowed=False, action="ABSTAIN", clamped_size=0.0, reason="Order frequency rate limit reached (ACC-404)")`.
     * 5. Ukuran Posisi: `raw_size = float(intended_action.get("size", 1.0))`. `clamped = min(raw_size, self.limits.max_position_size)` (ACC-405).
     * 6. Return `SafetyDecision(allowed=True, action="EXECUTE", clamped_size=clamped, reason="Action passed Capital Safety Kernel verification")`.

═══════════════════════════════════════════════════════
BAGIAN B — OPERATIONAL BRAIN & FAST LOOP (are/operational.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/operational.py`
1. Dataclass `OperationalSignal`:
   - Fields: signal_id: str, symbol: str, raw_decision: Dict[str, Any], safety_decision: SafetyDecision, final_action: str, timestamp: float, signal_hash: str = ""
   - `__post_init__` menghitung sha256 `signal_hash` kanonikal.
2. Kelas `OperationalBrain`:
   - Inisialisasi:
     * `champion_registry: ChampionRegistry`
     * `safety_kernel: CapitalSafetyKernel`
     * `habitat: HabitatAdapter`
     * `event_store: EventStore`
   - STREAM_ID = "operational_signals"
   - `process_tick(symbol: str, timestamp: float, market_features: Dict[str, float], current_risk_state: Dict[str, float], as_of_cutoff: float, emergency_signal: bool = False) -> OperationalSignal`:
     * 1. Validasi Information-Time: jika `timestamp > as_of_cutoff`, raise `ValueError("Information-time barrier violated: timestamp in future (ACC-406)")`.
     * 2. Ambil Champion aktif: `active_champ = self.champion_registry.get_active_champion()`. Jika None $\rightarrow$ raw action = "ABSTAIN" (no active champion).
     * 3. Ambil rezim dari Habitat: `obs = self.habitat.ingest_market_state(symbol, timestamp, market_features, as_of_cutoff)`.
     * 4. Evaluasi raw signal (contoh: BUY / SELL / HOLD berdasarkan bobot fitur pasar).
     * 5. Filter melalui CSK (ACC-407):
        `safety_res = self.safety_kernel.evaluate_action(intended_action=raw_action_dict, current_drawdown=current_risk_state.get("drawdown", 0.0), current_volatility=current_risk_state.get("volatility", 1.0), recent_order_count=int(current_risk_state.get("order_count", 0)), emergency_signal=emergency_signal)`
     * 6. Tentukan `final_action` ("EXECUTE" / "ABSTAIN" / "EMERGENCY_FLAT").
     * 7. Catat `OperationalSignal` ke EventStore stream `"operational_signals"` (ACC-408).
     * 8. Return `OperationalSignal`.

═══════════════════════════════════════════════════════
BAGIAN C — TEST SUITES BARU ARE-4 SLICE-1 (tests/are/)
═══════════════════════════════════════════════════════

Buat modul pengujian komprehensif di `tests/are/`:
1. `tests/are/test_are4_safety.py`: Menguji seluruh kondisi veto CSK (kill-switch, drawdown, volatility, rate limit, clamping per ACC-401..405).
2. `tests/are/test_are4_operational.py`: Menguji Information-Time cutoff, integrasi Champion, filter CSK, dan pencatatan EventStore stream (ACC-406..408).
3. `tests/are/test_are4_e2e_slice1.py`: Menguji integrasi Fast Loop E2E penuh (ACC-409).

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-401 s/d ACC-410 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (246 baseline + test baru ARE-4 Slice-1).
  Zero external dependencies (Python Standard Library only).
  Working tree clean.

LARANGAN
- Dilarang menyentuh broker API, socket live trading, atau eksekusi modal riil.
- Dilarang melemahkan authorizer atau triggers append-only di are/storage.py.
- Dilarang menggunakan modul random tanpa seed deterministik.

PROSES
1. Implementasikan Bagian A (safety.py) dan Bagian B (operational.py).
2. Buat test suite Bagian C di tests/are/.
3. Jalankan full test suite -> pastikan seluruh test PASS.
4. Commit di main: "feat(are4): implement Slice-1 Capital Safety Kernel & Operational Brain (DELEGASI_013)"
5. Laporkan hasilnya ke Lead Architect.
```
