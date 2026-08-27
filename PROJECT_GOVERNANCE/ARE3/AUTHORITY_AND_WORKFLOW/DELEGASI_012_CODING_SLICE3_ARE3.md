# DELEGASI 012 — Engineering AI: Coding Slice-3 ARE-3 (Multi-Agent Research Coordinator & Champion Registry)

Status: **DELEGASI AKTIF / AUTHORIZED — CHARTER T4 RATIFIED**  
Diterbitkan: Lead Architect & Auditor · Baseline `@691cc97` (239 tests pass)

> Cara pakai: Tempelkan SELURUH blok prompt di bawah ke sesi Engineering AI.

---

## 📋 PROMPT UNTUK ENGINEERING AI (salin dari sini)

```text
PERAN
Kamu adalah ENGINEERING AI (bukan arsitek).
GERBANG: DELEGASI_012 — CODING SLICE-3 ARE-3 — AUTHORIZED
HANYA untuk lingkup di bawah. Luar lingkup = DILARANG.

BASELINE
HEAD saat delegasi = 691cc97 (ARE-3 Slice-2 CLOSED, 239 tests pass, Manifest V41)
Kontrak rujukan = PROJECT_GOVERNANCE/ARE3/CONTRACTS/SLICE_3_CONTRACT_ARE3.md

═══════════════════════════════════════════════════════
BAGIAN A — CHAMPION REGISTRY (are/champion.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/champion.py`
1. Dataclass `ChampionRecord`:
   - Fields: champion_id: str, candidate_id: str, promotion_disposition_hash: str, activated_at: float, status: str ("ACTIVE" / "SUPERSEDED" / "ROLLED_BACK")
2. Kelas `ChampionRegistry`:
   - Inisialisasi: Menerima `event_store: EventStore`.
   - STREAM_ID = "champion_registry"
   - `get_active_champion() -> Optional[ChampionRecord]`: Mengembalikan champion aktif saat ini dari stream.
   - `promote_champion(candidate_id: str, promotion_disposition: PromotionDisposition) -> ChampionRecord`:
     * Validasi Keras: pastikan `promotion_disposition.decision == "PROMOTED"` dan tanda tangan/hash valid (ACC-324). Jika tidak, raise `ValueError("Unauthorized promotion attempt")`.
     * Nonaktifkan champion lama menjadi "SUPERSEDED".
     * Tambahkan `ChampionRecord` baru ke EventStore stream `"champion_registry"`.
   - `rollback_champion(reason: str) -> Optional[ChampionRecord]`:
     * Me-rollback champion aktif ke versi sebelumnya (ACC-325).
     * Tandai champion aktif saat ini sebagai "ROLLED_BACK" dan aktifkan champion sebelumnya.

═══════════════════════════════════════════════════════
BAGIAN B — MULTI-AGENT RESEARCH COORDINATOR (are/coordinator.py)
═══════════════════════════════════════════════════════

Buat modul baru: `are/coordinator.py`
1. Dataclass `AgentAssignment`:
   - Fields: discovery_agent: str, validation_agent: str, governor_agent: str
2. Dataclass `ResearchCycleResult`:
   - Fields: cycle_id: str, candidate_id: str, status: str ("PROMOTED" / "REJECTED" / "NO_EDGE_FOUND"), details: Dict[str, Any]
3. Kelas `ResearchCoordinator`:
   - Inisialisasi:
     * `search_tree_engine: SearchTreeEngine`
     * `sandbox: CapabilitySandbox`
     * `telemetry: TelemetryAggregator`
     * `habitat: HabitatAdapter`
     * `validation: ValidationService`
     * `critic: CriticEngine`
     * `governor: GovernorEngine`
     * `champion_registry: ChampionRegistry`
   - `run_autonomous_cycle(hypothesis_spec: Dict[str, Any], evaluation_func: Callable, market_features: Dict[str, float], holdout_dataset: List[Dict[str, Any]], assignment: AgentAssignment, as_of_cutoff: float) -> ResearchCycleResult`:
     * 1. SoD Check (ACC-322): `governor.verify_sod(assignment.discovery_agent, assignment.validation_agent, assignment.governor_agent)`.
     * 2. Habitat Ingestion: `habitat.ingest_market_state(..., as_of_cutoff)`.
     * 3. Search Tree Spawn: `search_tree_engine.spawn_node(...)`.
     * 4. Sandbox Evaluation: `sandbox.execute(evaluation_func, args=(market_features,))`.
     * 5. Telemetry Recording: `telemetry.record_trace(...)` & `compute_aggregate_metrics()`.
     * 6. Validation: `validation.validate_candidate(..., as_of_ts=as_of_cutoff, dataset=holdout_dataset)`.
     * 7. Critic Adversarial Check: `critic.evaluate_adversarial(...)`.
     * 8. Governor Evaluation: `governor.evaluate_promotion(...)`.
     * 9. Jika PROMOTED $\rightarrow$ `champion_registry.promote_champion(...)`.
     * 10. Kembalikan `ResearchCycleResult`.

═══════════════════════════════════════════════════════
BAGIAN C — TEST SUITES BARU ARE-3 SLICE-3 (tests/are/)
═══════════════════════════════════════════════════════

Buat modul pengujian komprehensif di `tests/are/`:
1. `tests/are/test_are3_champion.py`: Menguji promosi champion, penolakan tanpa disposisi sah, riwayat suksesi, dan rollback (ACC-323, ACC-324, ACC-325).
2. `tests/are/test_are3_coordinator.py`: Menguji orkestrasi siklus riset otonom dan penegakan SoD antar agen (ACC-321, ACC-322).
3. `tests/are/test_are3_e2e_slice3.py`: Menguji integrasi siklus riset otonom penuh E2E (ACC-326).

KRITERIA TERIMA (fail-closed, semuanya wajib)
  ACC-321 s/d ACC-330 terpenuhi 100%.
  `python -m pytest tests/ -q` $\rightarrow$ seluruh test PASS (239 baseline + test baru ARE-3 Slice-3).
  Zero external dependencies (Python Standard Library only).
  Working tree clean.

LARANGAN
- Dilarang menyentuh broker API, socket live trading, atau eksekusi modal.
- Dilarang melemahkan authorizer atau triggers append-only di are/storage.py.
- Dilarang menggunakan modul random tanpa seed deterministik.

PROSES
1. Implementasikan Bagian A (champion.py) dan Bagian B (coordinator.py).
2. Buat test suite Bagian C di tests/are/.
3. Jalankan full test suite -> pastikan seluruh test PASS.
4. Commit di main: "feat(are3): implement Slice-3 Multi-Agent Research Coordinator & Champion Registry (DELEGASI_012)"
5. Laporkan hasilnya ke Lead Architect.
```
