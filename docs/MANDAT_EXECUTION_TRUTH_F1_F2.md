# MANDAT: EXECUTION TRUTH REPAIR — STRATEGY V2 (F1 + F2)

> **PERAN KAMU**: Senior Quantitative Systems Engineer. Tugas kamu memperbaiki
> **kebenaran ekonomi** dari execution replay dan memulihkan evidence dataset,
> sesuai `docs/DESIGN_STRATEGY_V2.md` **§10 (v2.4)** — baca file itu DULU, khususnya
> §10.1 (E-1..E-4), §10.2 (klaim yang DITOLAK — jangan dikerjakan ulang), §10.4 (urutan).
>
> **PRINSIP**: Sebelum fase ini, PnL execution replay adalah fiksi matematika
> (bug unit 100× + double-count spread). Setelah fase ini, setiap angka PnL harus
> bisa dipertanggungjawabkan ke biaya riil broker. Kamu TIDAK menyentuh gate engine
> (gates.py, zones.py), jalur live, bridge, bot, WFO core.

---

## 1. KONTEKS (kamu tidak punya akses chat — ini semua yang perlu kamu tahu)

Repo `D:\Hermes\AHFMES-ARE`, Windows, git-bash. Shell `python` = 3.14.5 (polars,
pandas, pytest, MetaTrader5). Baseline test: **747 passed + 105 subtests** —
zero regression WAJIB.

Fakta terverifikasi audit (percayai ini):
- **Gate engine (P0–P2) SEHAT**: no-lookahead terbukti (injeksi 25 bar future → log
  222 record pertama identik), determinism ×2 bit-identik, Layer A menolak NaN/
  duplikat dengan benar. JANGAN menyentuh gates.py/zones.py kecuali untuk test.
- **Execution replay SAKIT** — 2 bug terbukti:
  1. **Double-count spread**: entry BUY sudah = open + spread + slippage (biaya masuk
     ke harga), lalu `cost_usd` memotong `entry_spread + exit_spread` lagi → spread
     dihitung dua kali. Round-trip test (harga flat, spread 1700 unit): net simulasi
     −$3551/lot vs realita −$150/lot.
  2. **Unit spread 100×**: bridge `/account` melaporkan `spread` = (ask−bid)×10000
     (contoh riil: bid 4412.42 / ask 4412.59 → spread "1700"), sedangkan `compute_cost`
     mengasumsikan poin = 0.01 harga (×100). 1 poin XAUUSD (0.01) = $1/lot; spread
     0.17 harga = **17 poin (0.01) = $17/lot**, bukan $1700. Seluruh PnL kini fiksi.
- **Evidence B1 mati**: replay 7 Sep → 222/222 diveto `B1:NEWS_DATA_STALE` karena
  kalender ForexFactory yang di-fetch saat itu post-dates window replay (provenance
  guard bekerja dengan benar — jangan dilemahkan).
- **Klaim red team yang SUDAH DIVERIFIKASI SALAH — JANGAN dikerjakan**:
  WFO pooled equity chaining (benar), DSR evaluation_count (salah — pakai
  effective_trial_count), provenance hash tidak lengkap (salah — semua field),
  infinite loop CPU 100% (salah — raise-on-error / sleep 1s). Detail: desain §10.2.

---

## 2. DELIVERABLES — EMPAT PAKET

### PAKET 1 (commit #1) — `F1a: RED invariant round-trip + normalisasi unit`
1. Buat `strategy_v2/broker_meta.py`:
   - `normalize_spread(raw_value, source_unit)` — `source_unit` ∈ {`PRICE_1E4`,
     `POINTS_001`}; konversi ke poin 0.01-harga. Fail-closed bila unit tak dikenal.
   - `load_broker_meta(bridge_account: dict) -> dict` — ekstrak `contract_size`,
     `point`, `tick_value` dari `symbol_info` bila tersedia (field baru di bridge
     TIDAK wajib — bila tak ada, fallback konstanta profil + label `FALLBACK`).
   - `point_value_usd_per_lot(broker_meta)` → $1/lot utk XAUUSD kontrak 100oz —
     DIHITUNG, bukan hardcode.
2. Tulis **RED tests dulu** (`tests/strategy_v2/test_round_trip_invariant.py`):
   - **INVARIANT ROUND-TRIP (desain §10.1 E-1)**: pada harga flat, round-trip BUY
     dan SELL (slippage=0, delay=0, komisi=0) masing-masing menghasilkan
     `net_usd = -(entry_spread + exit_spread) * point_value * lot` **PERSIS**.
   - Unit test: `normalize_spread(1700, "PRICE_1E4") == 17.0`;
     `normalize_spread(17, "POINTS_001") == 17.0`.
   - Test ini HARUS GAGAL terhadap kode sekarang (bukti bug nyata) — sertakan
     output kegagalannya di commit message.
3. Commit pesan: `test(strategy-v2): F1a RED — round-trip invariant + unit normalisasi (bukti bug PnL fiksi)`

### PAKET 2 (commit #2) — `F1b: GREEN — execution contract BID/ASK + state machine`
Perbaiki `strategy_v2/replay.py::run_execution_replay`:
1. **Kontrak harga (desain §10.1 E-1)** — `candle_price_basis = BID`:
   - BUY: entry = open(BID) + spread + slippage_adverse; SL/TP dievaluasi pada
     BID bar (low/high) — level SL/TP dihitung dari entry; **exit pada BID level
     tanpa menambah spread ke harga**.
   - SELL: entry = open(BID) − slippage_adverse; SL/TP dievaluasi pada BID bar;
     **exit pada ASK = level + spread** (atau setara: exit BID dengan biaya spread
     exit di USD — PILIH SATU BENTUK, yang penting round-trip invariant PASS dan
     konsisten untuk BUY & SELL; dokumentasikan pilihanmu di DECISIONS.md).
   - Dilarang double-count: spread muncul TEPAT SATU KALI per arah per trade.
2. **Position state machine (desain §10.1 E-3)** — `ONE_POSITION_ONLY`:
   - State: `FLAT | LONG | SHORT` (+ `entry_ts`, `ticket_ref`).
   - Sinyal searah saat terbuka → `REJECTED:position_open` (masuk
     `rejected_execution_reasons`).
   - Sinyal berlawanan saat terbuka → `exit_then_reverse` (tutup posisi pada bar itu
     dengan aturan harga exit normal, lalu buka baru — atau veto reversal, PILIH
     SATU per profil, dokumentasikan di DECISIONS.md; satu pilihan konsisten
     untuk scalp & micro pada baseline ini).
   - EOD_MARK (akhir dataset) tetap ada, dilabeli.
3. **Broker metadata injection**: hapus `price_mult = 0.01` hardcode → pakai
   `point_value_usd_per_lot` dari broker_meta; `spread_points` masuk replay
   **sudah dinormalisasi** (unit di-declare eksplisit di caller). Broker meta masuk
   `config_hash` (Pagar 1) via `registry.compute_config_hash` — extend bila perlu.
4. Sertakan field baru di trade record: `price_basis`, `entry_side` (BID/ASK),
   `exit_side`, `broker_meta_hash`.
5. GREEN: semua RED test lulus + seluruh suite lama tetap hijau.

### PAKET 3 (commit #3) — `F2: EVIDENCE REPAIR — kalender pre-dated + replay ulang`
1. **Sourcing kalender historis**: fetch ForexFactory weekly calendar dan simpan
   sebagai artifact dengan timestamp pengambilan < window replay, ATAU bangun
   dataset multi-hari (pilih yang feasible; user mengizinkan tanpa batas hari).
   Bila bridge hidup: tarik candle M5/M15 beberapa hari (multi-hari disarankan).
   Bila tidak tersedia, dokumentasikan limitasi — JANGAN mengarang data.
2. Re-run replay kedua profil dengan evidence valid → funnel **natural**:
   B1 PASS di ≥80% bar di luar blackout nyata (target; laporkan angka aktual).
3. Simpan artifact kalender + hash ke `data/research/v2_replay/` (runtime path,
   tidak di-commit) — hash masuk config_hash otomatis (sudah ada).
4. Update `strategy_v2/REPORT_P2.md` → tambah bagian "F2 natural funnel" dengan
   perbandingan: funnel lama (222×B1 stale) vs baru, dan angka PnL yang kini
   dalam unit dolar benar (setelah fix 100×).

### PAKET 4 (commit #4) — `F2b: laporan unit-akurat + regresi guard`
1. `strategy_v2/REPORT_F1_F2.md`: tabel sebelum/sesudah — PnL per trade contoh
   (angka fiksi lama vs benar), funnel natural, dan deklarasi unit spread
   (`PRICE_1E4` dari bridge).
2. Tambahkan regression guard: satu test yang memverifikasi `total_cost_usd` pada
   contoh riil (spread 0.17 harga) = **$17/lot**, bukan $3400 — mencegah bug unit
   kembali.

---

## 3. KRITERIA TERIMA (fail-closed)
1. Round-trip invariant PASS untuk BUY dan SELL pada flat price (dengan bukti output di laporan).
2. `normalize_spread(1700, "PRICE_1E4") == 17.0` dan contoh riil: cost = $17/lot (regression guard).
3. State machine: sinyal searah saat terbuka → `REJECTED:position_open`; tidak ada phantom stacking.
4. Funnel natural: B1 tidak lagi memveto 100% (angka aktual dilaporkan; target ≥80% PASS di luar blackout).
5. Full suite: ≥ 747 baseline + test baru, **0 fail** (`--ignore=tests/test_bot_lifecycle.py`).
6. 4 commit terpisah sesuai urutan (RED dulu, baru GREEN); push `origin/main`.
7. Tidak menyentuh: `gates.py`, `zones.py`, `are/bot.py`, `are/mt5_server.py`, `are/backtest.py`,
   `are/validation.py`, UI. (Kecuali registry.py untuk extend config_hash bila perlu —
   catat di DECISIONS.md.)
8. Semua keputusan desain yang kamu ambil (basis exit, reversal policy) dicatat di
   `strategy_v2/DECISIONS.md`.

## 4. BATASAN KERAS
- Dilarang menambah dependency. Dilarang menyentuh jalur live. Dilarang mengarang data.
- Dilarang mengubah gate semantics (B1–B7) dan hypothesis registry nilai (hanya
  boleh tambah entri BARU bila perlu, dengan status HYPOTHESIS).
- Bila data multi-hari tidak bisa ditarik (bridge down), kerjakan F1 penuh +
  F2 sebatas artifact kalender, catat limitasi, jangan berhenti total.
- Laporan akhir: per paket — file berubah, hasil test angka pasti, bukti eksekusi
  (potongan output), commit hash, `git log --oneline -8`, `git status --short`.

## 5. AUDIT YANG AKAN DILAKUKAN ATASMU
Saya akan: menjalankan round-trip invariant sendiri (BUY & SELL, flat & trending),
menguji normalisasi unit dengan angka bridge riil, memverifikasi state machine
(dua sinyal searah → satu trade), memeriksa funnel natural B1, rerun full suite,
dan meng-grep `price_mult` yang tersisa. Kegagalan satu kriteria = dikembalikan.
