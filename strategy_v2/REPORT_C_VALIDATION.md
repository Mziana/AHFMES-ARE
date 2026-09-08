# REPORT VALIDASI C0–C4 — UJI IMPLEMENTASI INDEPENDEN

Tanggal: 2026-09-09 · Driver: `scripts/validate_c_cycle.py` (ter-commit, reproducible) ·
Artefak hasil: `data/research/validation/c_cycle_validation.json` (results_hash `ed332b9864aae974…`) ·
Verdict: **ALL_PASS — 21/21 check, exit 0**

## Tujuan

Menguji implementasi Cognitive Layer C0–C4 secara independen terhadap klaim di
`REPORT_C.md`: kontrak, integritas artefak, determinisme, semantik gate BQ,
dan reproduksi angka C1/C2/C3 — semuanya dijalankan ulang dari nol pada dataset
terkunci P3 (`86014edf…`), bukan membaca ulang isi laporan.

## Hasil per kelompok check

### Kontrak (V1) — 4/4 PASS
| Check | Hasil |
|---|---|
| STRATEGY_VERSION | `strategy_v2/0.4.1-c1` ✅ |
| H-SCORE-01.threshold | 60.1 ✅ |
| profil MICRO `scoring.mode` | `off` — kontrak tidak mengubah perilaku live ✅ |
| profil MICRO `thresholds.candidate` | 60.1 ✅ |

### Integritas artefak (V2) — 4/4 PASS
`results_hash` c1/c2/c3/c4 **direkomputasi ulang dari isi file** dan semua cocok
dengan hash tersimpan: `2b99583d…`, `49320fb1…`, `3db5986a…`, `2ecefc60…`.
Artefak tidak pernah dimodifikasi setelah ditulis.

### Determinisme (V3–V4) — 2/2 PASS
- `evaluate_quality` dua kali pada input identik → **byte-identik** (final_score 32.66).
- `run_decision_replay` dua kali pada sesi sama (275 record) → **byte-identik**.

### Parity & semantik veto BQ (V5–V6) — 4/4 PASS (bukti kunci)
- Replay threshold-null: **199 sinyal** (parity P4/P5), semua tercatat skornya (0 fail-closed).
- **Veto BQ native (wiring kontrak, T\*=60.1) == mekanisme blank→WAIT C1, identik persis**:
  - kept: 60 native == 199 − 139 simulasi ✅
  - jumlah veto: 139 native == 139 simulasi ✅
  - skor kept minimum 60.12 (≥ ambang; tidak ada sinyal bocor) ✅
- Artinya: T\* hasil kalibrasi C1 **benar-benar dapat direproduksi oleh gate BQ
  yang di-wire di engine**, bukan hanya simulasi driver.

### Reproduksi angka (V7–V9) — 7/7 PASS
| Angka | Re-run | Artefak | Cocok |
|---|---|---|---|
| Binary base | 136 trade, +0.6940 | +0.6940 (n=136) | ✅ |
| Binary must ×1.5+slip2 | −0.6844 | −0.6844 | ✅ |
| Scorer base | 43 trade, +2.6354 | +2.6354 (n=43) | ✅ |
| Scorer must | +0.2023 | +0.2023 | ✅ |
| C3 sel wajib | +0.2023 | +0.2023 | ✅ |
| C1 baris T=60.1 | base +2.6354 / must +0.2023 | sama | ✅ |

## Test suite (pytest)

- `tests/strategy_v2`: **112 test, exit 0** (15 di antaranya test kontrak C0 `test_scoring.py`).
- Full suite (kec. `tests/test_bot_lifecycle.py` yang menjalankan bot sungguhan):
  **684 test, exit 0, nol gagal/error** (dipastikan dari progress: hanya titik, tanpa F/E).
- Catatan: baris ringkasan "N passed" tidak tampil karena `addopts = "-q …"` di
  `pyproject.toml` membuat `-q` ganda (`-qq`) menyembunyikan summary — perilaku
  pytest, bukan kegagalan test.

## Kesimpulan

1. Implementasi C0–C4 **deterministik, fail-closed, dan reproducible** — semua
   angka yang diklaim di `REPORT_C.md` terbukti kembali saat dijalankan ulang.
2. Wiring gate BQ di engine **setara persis** dengan mekanisme kalibrasi C1
   (V6) — tidak ada kesenjangan antara "skor yang dikalibrasi" dan "gate yang
   akan live".
3. Verdict riset **tidak berubah** dan kini sudah teruji integritasnya:
   C2/C3 lulus (scorer menang seleksi, garis wajib positif), C4 GAGAL_STATISTIK
   (PSR 0.747, CI95 [−4.98, +10.25], worst-fold −25.39) — keputusan tetap di
   tangan owner (backward OOS / revisi rezim / NO-GO).

## Cara mereproduksi

```bash
python scripts/validate_c_cycle.py   # 21 check, exit 0 = ALL_PASS
python -m pytest tests --ignore=tests/test_bot_lifecycle.py -p no:warnings
```
