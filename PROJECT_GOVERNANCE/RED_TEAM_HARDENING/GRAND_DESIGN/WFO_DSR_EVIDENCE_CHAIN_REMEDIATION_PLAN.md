# MASTER DESIGN & REMEDIATION PLAN: WFO -> DSR -> FINAL GATE EVIDENCE CHAIN

```text
DOKUMEN          : GRAND_DESIGN / WFO_DSR_EVIDENCE_CHAIN_REMEDIATION_PLAN.md
OTORITAS         : Lead Architect & Red Team Advisory Council
STATUS           : BLUEPRINT RESMI TERKUNCI (GELOMBANG 3 RED TEAM)
TANGGAL          : 2026-08-29
BASELINE KODE    : Commit 6767cc9 on main (457 tests pass 100%)
TARGET REMEDIASI : 11 Residu Kritis (RES-WFO-01 s/d RES-WFO-11)
```

---

## I. Latar Belakang & Akar Masalah (The Core Vulnerability)

Pada audit penutup commit `6767cc9`, Red Team menemukan bahwa meskipun fungsi `run_walk_forward_optimization()` sudah mampu melakukan train-test grid search, **rantai pembuktian out-of-sample ke Final Gate belum terikat secara fisik (disconnected evidence chain)**:

1. **Injeksi Parameter Manual:** `are/preflight.py` mengevaluasi validasi statistik dengan menyuntikkan angka manual `wf_score=0.80` dan `num_trials=10` ke `validate_statistical_robustness()`, bukan mengekstraknya langsung dari objek WFO nyata.
2. **Ketiadaan Objek Kanonikal:** WFO mengembalikan dictionary longgar tanpa tipe data kanonikal immutable (`WFOEvidence`) yang menyatukan deret return OOS gabungan, metadata fold, dan hash pembuktian.
3. **Distorsi `mean_oos_sharpe`:** Menggunakan rata-rata aritmatika Sharpe fold yang secara matematis bukan Sharpe dari keseluruhan jalur ekuitas OOS gabungan (*pooled OOS Sharpe*).
4. **Purge Tanpa Kontrak Label Horizon:** `purge_bars` tidak memiliki batas bawah formal terhadap `label_horizon_bars` strategi, membuka potensi kontaminasi label.
5. **DSR Tidak Terkunci ke OOS Terpilih:** DSR mengevaluasi Sharpe dari single backtest in-sample/full-sample, bukan dari OOS murni pemenang seleksi.

---

## II. Arsitektur Target Rantai Bukti (Target Architecture)

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
            │          (>= label_h)           │
            ▼                                 │
     PARAMETER GRID                           │
     (Argmax Sharpe)                          │
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
                    WFO FOLD EVIDENCE
                    (IS Metrics, OOS Returns,
                     Winner, Runner-up, Ties)
                             │
                             ▼
                    CANONICAL WFO EVIDENCE
                    (Pooled OOS Returns, Pooled Sharpe,
                     Effective Trial Count, Overlap Ratio)
                             │
                             ▼
                    MULTIPLE-TESTING AUDIT
                    (Deflated Sharpe Ratio on Pooled OOS)
                             │
                             ▼
                    FAIL-CLOSED FINAL GATE
                    (Pre-Flight Checkpoint 5)
                             │
                     ┌───────┴───────┐
                     ▼               ▼
                    GO             NO-GO
               (Cryptographic   (INVALID /
                Certificate)      FAIL)
```

---

## III. Rincian Remediasi 11 Residu (WFO-01 s/d WFO-11)

| ID Residu | Target File & Komponen | Solusi Teknis Mendalam |
| :--- | :--- | :--- |
| **RES-WFO-01** | `are/preflight.py` | Mengikat Checkpoint 5 secara langsung untuk menerima `wfo_evidence: WFOEvidence`. Menghapus total hardcoded `wf_score=0.80` dan `num_trials=10`. |
| **RES-WFO-02** | `are/backtest.py` | Memisahkan `parameter_family_size`, `evaluation_count`, dan `effective_trial_count` dengan deklarasi eksplisit `trial_count_method="PARAMETER_FAMILY"`. |
| **RES-WFO-03** | `are/validation.py`<br>`are/preflight.py` | Mengunci kalkulasi DSR pada `wfo_evidence.pooled_oos_sharpe` dan `wfo_evidence.effective_trial_count`. Dilarang menggunakan Sharpe in-sample. |
| **RES-WFO-04** | `are/backtest.py` | Mengimplementasikan `WFOEvidence` dan `WFOFoldEvidence` sebagai return type kanonikal `run_walk_forward_optimization()`. |
| **RES-WFO-05** | `are/backtest.py` | Menggabungkan (*concatenate*) seluruh irisan return OOS non-overlapping dan menghitung `pooled_oos_sharpe`. Menjadikan `mean_fold_oos_sharpe` murni metrik sekunder. |
| **RES-WFO-06** | `are/backtest.py` | Menambahkan parameter `label_horizon_bars: int = 0` dan guard clause fail-closed `assert purge_bars >= label_horizon_bars`. |
| **RES-WFO-07** | `are/backtest.py` | Menghitung `training_overlap_ratio` dan `oos_overlap_ratio` (wajib 0.0 untuk strict pooled OOS). |
| **RES-WFO-08** | `are/backtest.py` | Merekam audit per-fold: pemenang, skor IS, runner-up, skor runner-up, dan batas temporal. |
| **RES-WFO-09** | `are/backtest.py` | Menerapkan deterministic multi-tier tie-breaking: `(is_sharpe, -is_max_dd, -is_turnover)` dan mencatat `tie_count`. |
| **RES-WFO-10** | `are/preflight.py` | Menerapkan fail-closed mutlak pada Final Gate: jika `wfo_evidence` hilang, korup, atau `dsr_passed == False`, status langsung `INVALID` / `NO_GO`. |
| **RES-WFO-11** | `tests/are/test_wfo_evidence_chain_invariants.py` | Membuat 7 invariant test end-to-end (Test A s/d G) yang membuktikan kekedapan rantai bukti terhadap mutasi dan kebocoran. |

---

## IV. Disposisi 4-Kelas Final Gate

Final Gate pada `are/preflight.py` mengadopsi 4 kelas disposisi:

1. **`INVALID` (Evidence Broken):** Missing WFO, missing DSR, purge violation, fold overlap > 0, data hash mismatch -> **HALT OPERASIONAL**.
2. **`FAIL` (Performance Unacceptable):** Bukti valid, namun `pooled_oos_sharpe < threshold`, `dsr_p_value >= 0.05`, atau `max_drawdown > limit` -> **VETO**.
3. **`BORDERLINE` (Underpowered / Unstable):** Lolos batas minimum tetapi WFE < 0.50 atau `worst_fold_oos_sharpe < -1.0` -> **PERLU RISET TAMBAHAN**.
4. **`PASS` (Authoritative GO):** 7/7 Checkpoints lolos, WFO valid, DSR valid, Triple Crisis selamat -> **SERTIFIKAT RESMI DITERBITKAN**.