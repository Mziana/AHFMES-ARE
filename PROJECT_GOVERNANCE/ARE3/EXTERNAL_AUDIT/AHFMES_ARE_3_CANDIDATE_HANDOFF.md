# AHFMES ARE-3 — Candidate External Audit Handoff

Status: **CANDIDATE HANDOFF / EVIDENCE-CHRONOLOGY / ZERO AUTHORITY**  
Kategori: `ARE3`  
Baseline: `@ebf931d` (ARE-3 CLOSED FULL PASS)

---

## 1. Identitas Paket Handoff ARE-3
- **Fase:** ARE-3 Autonomous Science & Direction Intelligence
- **Total Test Suite:** 246 tests passed (100% PASS)
- **Manifest Anggota:** 396 file terverifikasi dual-implementation
- **Disposisi Formal:** `ACCEPT_ARE3_AUTONOMOUS_SCIENCE_CLOSED`

## 2. Modul-Modul yang Diserahkan
1. `are/constants.py` — Centralized lifecycle constants & invariants.
2. `are/search_tree.py` — Search tree & budget monotonic manager.
3. `are/validation.py` — Out-of-sample validation service & Information-Time barrier.
4. `are/governor.py` — Adversarial critic & Governor SoD gatekeeper.
5. `are/sandbox.py` — Isolated capability sandbox & socket blocking.
6. `are/telemetry.py` — Research telemetry aggregator on EventStore stream.
7. `are/habitat.py` — Environment observation & Condition Atlas classifier.
8. `are/champion.py` — Champion registry, promotion gating & rollback.
9. `are/coordinator.py` — Multi-agent autonomous research coordinator.
