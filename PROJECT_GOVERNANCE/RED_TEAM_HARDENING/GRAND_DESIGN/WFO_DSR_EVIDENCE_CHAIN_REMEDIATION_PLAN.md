# MASTER DESIGN & REMEDIATION PLAN v2: CANONICAL WFO EVIDENCE CHAIN & DSR INTEGRITY

```text
DOKUMEN          : GRAND_DESIGN / WFO_DSR_EVIDENCE_CHAIN_REMEDIATION_PLAN.md (VERSION 2.0)
OTORITAS         : Lead Architect & Red Team Advisory Council
STATUS           : BLUEPRINT RESMI TERKUNCI (GELOMBANG 3 RED TEAM)
TANGGAL          : 2026-08-29
BASELINE KODE    : Commit 6767cc9 on main (457 tests pass 100%)
TARGET REMEDIASI : 11 Residu Kritis (RES-WFO-01 s/d RES-WFO-11) + 14 Perubahan Wajib
```

---

## I. Prinsip Rekayasa Mutlak v2 (Core Mandates)

1. **Preflight Strictly Consumer (Producer-Consumer Separation):** `are/preflight.py` DILARANG menjalankan WFO sendiri. Preflight murni mengonsumsi objek kanonikal `WFOEvidence`. Jika `wfo_evidence is None` -> status langsung `INVALID` / `NO_GO`.
2. **Deep Immutability:** Seluruh struktur data bukti (`WFOEvidence`, `WFOFoldEvidence`) menggunakan `@dataclass(frozen=True)` dan struktur data immutable `tuple`, bukan `list`.
3. **Pemisahan Bukti Mentah vs Derivasi:** `WFOEvidence` menyimpan data kebenaran faktual. Evaluasi integritas menghasilkan `WFOIntegrityResult`, evaluasi bias seleksi menghasilkan `DSRResult`, dan evaluasi ambang batas performa menghasilkan `PerformanceResult`.
4. **WFE Formula Per-Fold:** $WFE_i = \frac{OOS_i}{IS_i}$ per fold. Dilaporkan sebagai `mean_wfe`, `median_wfe`, `worst_wfe`.
5. **OOS Chronological Non-Overlap Invariant:** Penggabungan deret OOS wajib melewati validasi waktu $t_{oos\_start}[i+1] \ge t_{oos\_end}[i]$.
6. **4-State Gate Composition:** Status kelayakan terdiri dari `INVALID`, `FAIL`, `BORDERLINE`, dan `PASS`. Hanya status `PASS` murni yang *eligible* untuk `GO`.

---

## II. Arsitektur Target Rantai Bukti v2

```text
                    RAW HISTORICAL DATA
                             │
                             ▼
                  ┌─────────────────────┐
                  │  WFO SPLIT ENGINE   │
                  └──────────┬──────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
          TRAIN            PURGE             OOS
     [t0 ... t_train]  [purge_bars]     [t_oos_start ... t_oos_end]
            │       (>= label_horizon)        │
            ▼                                 │
     PARAMETER SEARCH                         │
     (_wfo_selection_key)                     │
            │                                 │
            ▼                                 │
     TIE-BREAK AUDIT                          │
     (Max DD -> Turnover)                     │
            │                                 │
            ▼                                 │
     SELECTED WINNER                          │
            │                                 │
            └────────────────┬────────────────┘
                             ▼
                 CANONICAL WFO EVIDENCE
             (Immutable Frozen Data Object)
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
     WFOIntegrityResult  DSRResult   PerformanceResult
             │               │               │
             └───────────────┼───────────────┘
                             ▼
                  PRE-FLIGHT FINAL GATE
                  (Checkpoint 5 Consumer)
                             │
                     ┌───────┴───────┐
                     ▼               ▼
                   PASS            NO-GO
                 (Eligible)   (INVALID / FAIL /
                                BORDERLINE)
```

---

## III. Spesifikasi Struktur Data Kanonikal v2

```python
@dataclass(frozen=True)
class WFOFoldEvidence:
    fold_id: int
    train_start_ts: float
    train_end_ts: float
    purge_start_ts: float
    purge_end_ts: float
    oos_start_ts: float
    oos_end_ts: float
    candidate_count: int
    selection_metric: str
    winner_params: Dict[str, Any]
    winner_is_score: float
    runner_up_params: Optional[Dict[str, Any]]
    runner_up_is_score: Optional[float]
    tie_count: int
    tie_break_rule: str
    is_metrics: Dict[str, float]
    oos_metrics: Dict[str, float]
    oos_returns: Tuple[float, ...]
    wfe: float

@dataclass(frozen=True)
class WFOEvidence:
    run_id: str
    dataset_hash: str
    data_start_ts: float
    data_end_ts: float
    folds: Tuple[WFOFoldEvidence, ...]
    
    # Trial Accounting (RES-WFO-02)
    fold_count: int
    parameter_family_size: int
    evaluation_count: int
    effective_trial_count: int
    effective_trial_method: str  # "CONSERVATIVE_FAMILY_SIZE_PROXY"
    effective_trial_assumption: str
    
    # Overlap Disclosure (RES-WFO-07)
    training_overlap_ratio: float
    oos_overlap_ratio: float
    
    # Parameter Kontrak (RES-WFO-06)
    purge_bars: int
    label_horizon_bars: int
    label_horizon_unit: str  # "BARS"
    warmup_bars: int
    
    # Strict Pooled OOS Evidence (RES-WFO-05)
    pooled_oos_returns: Tuple[float, ...]
    pooled_oos_equity: Tuple[float, ...]
    pooled_oos_sharpe: float
    pooled_oos_return: float
    pooled_oos_max_drawdown: float
    
    # Fold Distribution Metrics
    mean_fold_oos_sharpe: float
    median_fold_oos_sharpe: float
    worst_fold_oos_sharpe: float
    std_fold_oos_sharpe: float
    mean_wfe: float
    median_wfe: float
    worst_wfe: float
    
    provenance_hash: str
```

---

## IV. Spesifikasi 12 Test Invarian End-to-End

1. **Test A (Selection Leakage):** Parameter A menang IS, Parameter B menang OOS -> WFO wajib memilih A.
2. **Test B (OOS Mutation Resistance):** Memutasi deret OOS -> `winner_params` tiap fold tidak berubah.
3. **Test C (DSR Provenance Binding):** Sharpe arbitrer di luar `pooled_oos_returns` ditolak.
4. **Test D (Trial Count Sensitivity):** Mutasi `parameter_family_size` mengubah DSR p-value secara konsisten.
5. **Test E (Missing WFO Fail-Closed):** Pre-flight Checkpoint 5 dengan `wfo_evidence = None` menghasilkan `INVALID`.
6. **Test F (Missing DSR Fail-Closed):** Evidence tanpa DSR evaluasi menghasilkan `NO_GO`.
7. **Test G (Warmup Contamination Resistance):** Spike return di warmup tidak mengubah strict OOS returns.
8. **Test H (OOS Overlap Rejection):** OOS tumpang tindih antar fold memicu `WFOIntegrityResult.is_valid = False`.
9. **Test I (Purge Violation):** `label_horizon > purge_bars` memicu `ValueError("PURGE_VIOLATION")`.
10. **Test J (Evidence Tampering Detection):** Mutasi `pooled_oos_sharpe` memicu hash mismatch pada audit integritas.
11. **Test K (Deterministic Tie-Break):** Kandidat dengan Sharpe identik diurutkan via Max DD terendah lalu Turnover terendah.
12. **Test L (Gate Permutations):** Kombinasi matriks status membuktikan hanya `PASS` murni yang berhak `GO`.