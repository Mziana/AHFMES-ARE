# MANDAT P3–P6 + INTEGRATION — Roadmap, Kriteria Lulus, dan Aturan Main

v1.0 — 2026-09-08. Penerus MANDAT_EXECUTION_TRUTH_F1_F2 (selesai, 4 commit ter-push).
Sumber desain: docs/DESIGN_STRATEGY_V2.md §P3–P6, §9 (keputusan start bot), §10.3 (pra-syarat Domain B).

---

## 0. Prinsip yang mengikat semua tahap

1. **Fail-closed selalu.** Data gagal Layer A → tidak ada keputusan; gate down → veto; bridge down → tidak ada order.
2. **Identitas eksperimen.** Setiap tahap mengunci `config_hash` + `dataset_hash`. Dataset/konfigurasi berubah → hash berubah → angka tahap lama BATAL (diulang), bukan dibandingkan silang.
3. **Satu klaim = satu artefak ber-hash + satu commit.** Tanpa artefak, klaim tidak ada.
4. **OOS buruk → revisi HIPOTESIS terdaftar di registry** (ID baru), bukan tweak diam-diam (desain §P6).
5. **Urutan tidak boleh dilompati.** P3 → P4 → P5 → P6; integration boleh mulai paralel SETELAH P4 lulus, tidak pernah sebelumnya.

---

## TAHAP 0 — Identitas Bersih (pra-syarat P3)

**Isi:** mengeksekusi keputusan owner (B1/B2 disabled "24/7 adaptive") secara disiplin:
- Tulis ulang 4 test kontrak lama (test_b1_news_four_codes, 3 test provenance P0-01, test_profiles_frozen_fields, test_inv5_news_codes_separate_all_veto) ke kontrak BARU — bukan dihapus/di-skip.
- Kunci profile_micro.json: session [[0,24]], max_stop 350, ema_pullback 1.0, volume_gate off.
- Bump STRATEGY_VERSION — gates penuh vs 24/7 harus terbaca dari versi.
- Commit paket symbol_info E-2 (bridge + conflict guard tick_value + wiring --bridge-account).

**Kriteria lulus:** full suite hijau 0 fail (tanpa skip) → 2 commit (T0a config+tests, T0b symbol_info) → push.

---

## P3 — Data Qualification (desain §P3)

**Isi:** dataset XAUUSD M5+M15 paralel multi-minggu (target ≥ 4 minggu ≈ ≥ 20.000 bar M5), satu sumber: bridge copy_rates_from_pos (jalur copy_rates_range terbukti beku di terminal ini), plus snapshot /account (symbol spec + spread live) sebagai file deterministik.

| Cek | Kriteria lulus |
|---|---|
| Duplicate timestamp | = 0 (fail-closed) |
| NaN / OHLC invalid | = 0 (fail-closed) |
| Gap intra-hari (< 3600s) | ≤ 0.1% bar; tiap kasus tercatat ts-nya |
| Gap ≥ 3600s | Diklasifikasi session_break, bukan korupsi |
| Timezone | Epoch UTC kontinu; offset server UTC+3 ternormalisasi; semua Δ kelipatan 300/900s |
| Spread | p50/p95/p99 dilaporkan; snapshot live (PRICE_1E4 → poin) tercatat |
| tick_volume | Semua ≥ 0; distribusi dilaporkan |
| Symbol spec | contract_size/point/tick_value/stops_level dari snapshot; meta hash masuk config_hash |

**Lulus:** REPORT_P3.md + dataset ber-hash → dataset_hash DIKUNCI untuk P4–P6.
**Gagal:** fail-closed tak terjelaskan, atau data < 2 minggu → perluas window, jangan turunkan standar.

---

## P4 — Baseline + Ablation (desain §P4)

**Isi:** tiga arm di dataset P3 yang sama, cost model sama:
1. OLD-MICRO (engine lama are/) — baseline pembanding
2. V2-MICRO (profil terkalibrasi T0)
3. V2-SCALP

**Ablation per gate:** tiap arm dijalankan satu gate off (B3/B4/B5/B6, sisanya utuh). Gate yang kehadirannya menurunkan expectancy net → DIBUANG, tercatat sebagai revisi hipotesis terdaftar.

**Kriteria lulus:**
- ≥ 1 arm V2: expectancy_net > 0 dengan ≥ 30 trade tereksekusi (nol trade = tak ada yang bisa diuji).
- Funnel menjelaskan 100% opportunity (Pagar 6).
- Gate yang bertahan punya kontribusi positif terukur dari ablation.
- V2 mengungguli OLD-MICRO pada expectancy net.

**Gagal:** revisi hipotesis (registry) → ulangi P4; maks 3 iterasi, lebih dari itu kembali ke owner.

---

## P5 — Cost Stress (desain §P5)

**Isi:** grid biaya atas arm juara P4 (params frozen): spread ×1.25 / ×1.5 / ×2.0 (17 → 21.25 / 25.5 / 34 poin) × slippage {0,2,5} poin × delay {0,1} bar — min 9 kombinasi.

**Lulus:** edge bertahan expectancy_net > 0 pada spread ×1.5 + slippage 2 + delay 0 (garis wajib desain), plus kurva degradasi per kombinasi.
**Gagal:** tak layak live pada biaya ini → revisi hipotesis (TP lebih lebar / frekuensi lebih rendah) → ulangi P4→P5.

---

## P6 — WFO + Statistik (desain §P6, §10.3 B-1/B-4) — gerbang GO/NO-GO demo

**Isi:** WFO purge/embargo ≥ 1 hari; parameter FROZEN dari P4/P5 (tidak boleh diutak-atik per fold); metrik: PSR, DSR (momen nyata), CI95 expectancy net, worst-fold, fold dispersion (dari backtest.py — wajib tampil, syarat B-4); Preflight Certificate run_full_preflight_battery() menempel pada run (syarat B-1).

**Kriteria lulus (GO demo):**
- PSR > 0.80 dan DSR > 0 dan CI95 expectancy net > 0
- Worst-fold tidak lebih buruk dari −(2× biaya rata-rata per trade)
- Semua fold OOS dilaporkan (bukan hanya pooled); OOS buruk → revisi hipotesis terdaftar
- Keputusan akhir GO/NO-GO milik owner (desain §9) — mandat hanya menyiapkan bukti.

---

## FASE I — Integration Layer (mulai paralel setelah P4 lulus)

**Isi:** adapter murni: keputusan Strategy V2 → ExecutionStateMachine → MT5ExecutionGateway. Kontrak eksekusi = kontrak replay terbukti (basis BID, spread tepat satu kali per arah, clamp stops_level + spread live saat eksekusi, lot = risk_percent × balance / SL points).

**Kriteria lulus:**
1. Parity test: adapter vs run_execution_replay di dataset sama → urutan trade identik (bar entry/exit, arah, lot), toleransi 1 tick.
2. Fail-closed: bridge down / Layer A invalid / gate down → tidak ada order, terlog.
3. Risk satu sumber: b7_risk ↔ CapitalSafetyKernel selaras — tidak ada dua kebenaran.
4. Shadow mode ≥ 1 minggu di akun demo, nol divergensi keputusan-vs-order.

## FASE D — Demo

**Syarat masuk:** P6 lulus (GO) + Fase I lulus + shadow bersih. **Pengaman:** lot minimal, daily loss cap, kill switch aktif, semua order ter-shadow-log.

---

## Tabel status

| Tahap | Status | Kunci lulus |
|---|---|---|
| T0 Identitas bersih | ❌ | suite hijau + 2 commit + push |
| P3 Qualification | ❌→🔧 | fail-closed 0, gap ≤ 0.1%, ≥ 2 (target 4) minggu, hash terkunci |
| P4 Baseline+ablation | ❌ | ≥ 30 trade, net > 0, funnel 100% |
| P5 Cost stress | ❌ | edge bertahan ×1.5 + slip 2 |
| P6 WFO+statistik | ❌ | PSR > 0.8, DSR > 0, CI95 > 0, certificate |
| Fase I Integration | ❌ | parity, fail-closed, risk satu sumber, shadow 1 minggu |
| Fase D Demo | ❌ | semua di atas + keputusan owner |
