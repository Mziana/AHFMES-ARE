# SLICE 1 CONTRACT — ARE-4 (Capital Safety Kernel & Operational Brain)

Status: **FROZEN T3 — RATIFIED FOR IMPLEMENTATION / AUTHORIZED**  
Fase: **ARE-4 Slice-1**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@ebf931d` (246 tests pass, Manifest V41)

---

## 1. Lingkup Komponen Slice-1 ARE-4

### A. `CapitalSafetyKernel` (`are/safety.py`)
- **A1:** Dataclass `SafetyLimits`: `max_position_size`, `max_drawdown_pct`, `volatility_cutoff`, `max_order_rate_per_min`, `kill_switch_active`.
- **A2:** Dataclass `SafetyDecision`: `allowed: bool`, `action: str ("EXECUTE" / "ABSTAIN" / "EMERGENCY_FLAT")`, `reason: str`, `decision_hash: str`.
- **A3:** Kelas `CapitalSafetyKernel`:
  - `evaluate_action(intended_action: Dict[str, Any], current_drawdown: float, current_volatility: float, recent_order_count: int, emergency_signal: bool = False) -> SafetyDecision`:
    * Jika `emergency_signal == True` atau `kill_switch_active == True` $\rightarrow$ veto `EMERGENCY_FLAT` (ACC-401).
    * Jika `current_drawdown >= max_drawdown_pct` $\rightarrow$ veto `ABSTAIN` (ACC-402).
    * Jika `current_volatility >= volatility_cutoff` $\rightarrow$ veto `ABSTAIN` (ACC-403).
    * Jika `recent_order_count >= max_order_rate_per_min` $\rightarrow$ veto `ABSTAIN` (ACC-404).
    * Jika `intended_action["size"] > max_position_size` $\rightarrow$ potong (*clamp*) atau veto ke `max_position_size` (ACC-405).
    * Semua keputusan dihitung secara deterministik dan fail-closed.

### B. `OperationalBrain` & Fast Loop (`are/operational.py`)
- **B1:** Dataclass `OperationalSignal`: `signal_id: str`, `symbol: str`, `raw_signal: Dict[str, Any]`, `safety_decision: SafetyDecision`, `final_action: str`, `timestamp: float`.
- **B2:** Kelas `OperationalBrain`:
  - Menerima `champion_registry: ChampionRegistry`, `safety_kernel: CapitalSafetyKernel`, `habitat: HabitatAdapter`, `event_store: EventStore`.
  - `process_tick(symbol: str, timestamp: float, market_features: Dict[str, float], current_risk_state: Dict[str, float], as_of_cutoff: float) -> OperationalSignal`:
    * 1. Validasi Information-Time barrier (ts $\le$ as_of_cutoff per ACC-406).
    * 2. Ambil model Champion aktif dari `champion_registry`.
    * 3. Klasifikasi rezim pasar via `habitat`.
    * 4. Hitung *bounded decision value* dari Champion.
    * 5. Filter keputusan melalui `safety_kernel.evaluate_action(...)` (ACC-407).
    * 6. Catat keputusan operasional ke EventStore stream `"operational_signals"` (ACC-408).

---

## 2. Kriteria Penerimaan Formal (ACC-401 s/d ACC-410)

| ID | Deskripsi Kriteria Penerimaan | Verifikasi |
|---|---|---|
| **ACC-401** | CSK memicu `EMERGENCY_FLAT` saat kill-switch aktif atau sinyal darurat diterima | `test_are4_safety.py` |
| **ACC-402** | CSK memveto (`ABSTAIN`) saat drawdown melampaui batas toleransi risiko | `test_are4_safety.py` |
| **ACC-403** | CSK memveto (`ABSTAIN`) saat volatilitas melampaui ambang batas cutoff | `test_are4_safety.py` |
| **ACC-404** | CSK membatasi laju order (*rate limit / frequency cap*) | `test_are4_safety.py` |
| **ACC-405** | CSK membatasi (*clamp*) ukuran posisi agar tidak melebihi `max_position_size` | `test_are4_safety.py` |
| **ACC-406** | OperationalBrain menegakkan Information-Time barrier saat memproses market tick | `test_are4_operational.py` |
| **ACC-407** | OperationalBrain menyaring seluruh output Champion melalui CSK secara deterministik | `test_are4_operational.py` |
| **ACC-408** | OperationalBrain mencatat sinyal dan keputusan keselamatan ke EventStore stream | `test_are4_operational.py` |
| **ACC-409** | Integrasi E2E Fast Loop & CSK Penuh | `test_are4_e2e_slice1.py` |
| **ACC-410** | Seluruh test suite (246 baseline + test baru ARE-4 Slice-1) 100% PASS (stdlib only) | `python -m pytest tests/` |

---

## 3. Batasan & Larangan Keras
- **DILARANG** terhubung ke broker eksternal, live network socket, atau mengeksekusi uang riil.
- **DILARANG** memperbolehkan sinyal model lolos tanpa evaluasi `CapitalSafetyKernel`.
- **DILARANG** menggunakan pustaka acak non-deterministik.
