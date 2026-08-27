# DELEGASI 014 — Engineering AI: Coding Slice-2 ARE-4 (Evolutionary Slow Loop & Registry Modularization DEBT-01)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@0ee66ed` (256 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_014 — CODING SLICE-2 ARE-4 — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 0ee66ed (ARE-4 Slice-1 CLOSED, 256 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/ARE4/CONTRACTS/SLICE_2_CONTRACT_ARE4.md

═══════════════════════════════════════════════════════
BAGIAN A — EVOLUTIONARY SLOW LOOP (are/evolution.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/evolution.py`
1. Dataclass `AdaptationTrigger`:
   - Fields: trigger_id: str, source_anomaly: str, symbol: str, suggested_hypothesis: Dict[str, Any], timestamp: float, trigger_hash: str = ""
   - `__post_init__` menghitung sha256 `trigger_hash` kanonikal.
2. Kelas `RegretAnalyzer`:
   - Inisialisasi: `event_store: EventStore`
   - `analyze_operational_stream(symbol: str, lookback_events: int = 50, regret_threshold: float = 0.40) -> Optional[AdaptationTrigger]`:
     * Membaca stream "operational_signals" dari EventStore.
     * Menghitung rasio veto / abstention / drawdown spike.
     * Jika rasio degradasi >= regret_threshold, buat dan kembalikan `AdaptationTrigger` (ACC-411).
     * Jika normal, kembalikan None.
3. Kelas `EvolutionaryLoop`:
   - Inisialisasi:
     * `regret_analyzer: RegretAnalyzer`
     * `research_coordinator: ResearchCoordinator`
     * `registry: Registry`
   - `evaluate_and_evolve(symbol: str, current_features: Dict[str, float], holdout_dataset: List[Dict[str, Any]], assignment: AgentAssignment, as_of_cutoff: float, evaluation_func: Callable) -> Optional[ResearchCycleResult]`:
     * 1. Jalankan `trigger = self.regret_analyzer.analyze_operational_stream(symbol)`.
     * 2. Jika `trigger is None` $\rightarrow$ tidak ada kebutuhan evolusi, kembalikan None.
     * 3. Jika ada trigger $\rightarrow$ daftarkan/ambil Problem ID di `self.registry` (misal `f"PROB_REGRET_{symbol}"`).
     * 4. Panggil `self.research_coordinator.run_autonomous_cycle(...)` menggunakan `trigger.suggested_hypothesis` dan `assignment` (ACC-412, ACC-415).
     * 5. Kembalikan hasil `ResearchCycleResult`.

═══════════════════════════════════════════════════════
BAGIAN B — MODULARISASI REGISTRY (DEBT-01 RESOLUTION)
═══════════════════════════════════════════════════════

Refaktor `are/registry.py`:
- Strukturkan internal `are/registry.py` dengan Strategy / Delegate Pattern (ACC-413):
  * `ProblemManager`: mengelola register_problem, get_problem, list_problems, retire_problem, dll.
  * `HypothesisManager`: mengelola register_hypothesis, get_hypothesis, dll.
  * `ExperimentManager`: mengelola register_experiment, get_experiment, dll.
  * `CandidateManager`: mengelola register_candidate, get_candidate, dll.
  * `CapabilityManager`: mengelola register_capability, get_capability, dll.
  * `GraveyardManager`: mengelola add_to_graveyard, is_graveyard, dll.
- Pastikan kelas `Registry` bertindak sebagai fasad bersih yang mendelegasikan pemanggilan ke sub-manager tersebut.
- KRITIS: Seluruh signature metode publik lama `Registry` WAJIB dipertahankan 100% kompatibel ke belakang (*backward-compatible*) sehingga test `tests/are/test_registry.py` dan kode pemanggil lain tidak ada yang rusak / regresi (ACC-414).

═══════════════════════════════════════════════════════
BAGIAN C — TEST SUITES BARU ARE-4 SLICE-2 (tests/are/)
═══════════════════════════════════════════════════════

Buat modul pengujian komprehensif di `tests/are/`:
1. `tests/are/test_are4_evolution.py`: Menguji deteksi anomali RegretAnalyzer dan orkestrasi EvolutionaryLoop (ACC-411, ACC-412, ACC-415).
2. `tests/are/test_are4_e2e_slice2.py`: Menguji integrasi E2E Fast Loop Anomaly $\rightarrow$ Evolutionary Trigger $\rightarrow$ Slow Loop Discovery $\rightarrow$ Champion Succession (ACC-417).

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-411 s/d ACC-420 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (256 baseline + test baru ARE-4 Slice-2).
  Zero external dependencies (Python Standard Library only).
  Working tree clean.

LARANGAN
- Dilarang merusak antarmuka publik `Registry` (DEBT-01).
- Dilarang memodifikasi policy Fast Loop secara in-place tanpa melalui Research Coordinator.
- Dilarang menyentuh broker API, live socket, atau eksekusi modal.

PROSES
1. Implementasikan Bagian A (evolution.py) dan Bagian B (refaktor registry.py).
2. Buat test suite Bagian C di tests/are/.
3. Jalankan full test suite -> pastikan seluruh 256+ test PASS.
4. Commit di main: "feat(are4): implement Slice-2 Evolutionary Slow Loop & Modularize Registry DEBT-01 (DELEGASI_014)"
5. Laporkan hasilnya ke Lead Architect.
```
