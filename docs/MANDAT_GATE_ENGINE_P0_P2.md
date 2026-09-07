# MANDAT: GATE ENGINE & DETERMINISTIC REPLAY — STRATEGY V2 (P0–P2)

> **PERAN KAMU**: Senior Quantitative Systems Engineer. Kamu mengimplementasikan
> P0–P2 dari kontrak **`docs/DESIGN_STRATEGY_V2.md` (v2.3)** — BACA FILE ITU DULU,
> itu dokumen desain yang disepakati dan menjadi kontrak kerjamu.
> Lingkupmu HANYA P0–P2. Live engine, WFO, DB, UI, order path = DILARANG disentuh.
>
> **Kalimat paling penting untuk kamu**:
> Jangan mencoba membuktikan bahwa Strategy v2 profitable pada P0–P2.
> Bangun mesin eksperimen yang membuat kita mampu membuktikan atau membantah
> profitabilitasnya tanpa lookahead, tanpa ambiguity, dan tanpa menyembunyikan biaya.
> Data yang akan memutuskan nasib strategi — bukan optimisme kita.

---

## 1. KONTEKS PROYEK (kamu tidak punya akses ke chat sebelumnya — baca ini)

Repo: `D:\Hermes\AHFMES-ARE` — sistem trading/research XAUUSD (Next.js UI + bridge MT5
+ bot live + research plane Python). Windows, shell = git-bash (POSIX syntax).

### 1.1 Sejarah singkat yang mendasari desain ini
- Bot micro-style lama men-trade **122× pada 7 Sep**, hasil **−$42.02**.
- Diagnosis: (a) entry berdasarkan **candle yang masih terbentuk** (intrabar noise),
  (b) RSI dipakai terbalik (BUY saat RSI 30 = menangkap pisau jatuh),
  (c) **122 trade/hari membuat biaya spread (~$41) menghabiskan gross edge (≈$0)**.
- Kesimpulan review 3 tahap: masalahnya **orchestration & entry timing**, bukan kurang
  indikator. Solusi: **gate architecture** — 9 gate VETO (bukan skor), dua profil
  (SCALP = high-confidence, MICRO = higher-frequency), dengan kontrak eksperimen
  yang leakage-proof, cost-aware, dan dapat diaudit.
- Desain lengkap + semua koreksi review: `docs/DESIGN_STRATEGY_V2.md` v2.3 (FINAL untuk P0–P2).

### 1.2 Environment (VERIFIED — jangan asumsikan)
- Shell `python` = WindowsApps shim → resolve ke `pythoncore-3.14-64` (3.14.5):
  punya polars, pandas, pytest, **dan** MetaTrader5. Gunakan `python` dari shell.
- `C:/Users/Fajar/AppData/Local/Python/pythoncore-3.14-64/python.exe` = interpreter yang sama.
- Test suite baseline: **678 passed** (`python -m pytest tests/ -q --ignore=tests/test_bot_lifecycle.py`).
  `test_bot_lifecycle.py` di-gate env `ARE_LIVE_ITEST=1` (men-trade demo riil) — JANGAN dijalankan.
- Bridge MT5 mungkin hidup di `127.0.0.1:18888` (auth token di `data/bridge_token.txt` —
  JANGAN pernah commit/print). UI Next.js mungkin hidup di `127.0.0.1:4028`.
- Bot live bisa berjalan kapan pun. ATURAN: P0–P2 tidak menyentuh jalur live sama sekali,
  jadi tidak perlu stop/start apa pun. JANGAN start bot, JANGAN restart bridge, JANGAN
  men-place order (meski demo).
- Git: konvensi satu finding = satu commit, push ke `origin/main` di akhir. Tanpa merge/rebase.

### 1.3 Kode yang relevan (sudah ada, JANGAN diubah — hanya dibaca/dipakai)
| File | Isi | Catatan penting |
|---|---|---|
| `UI/src/lib/indicators.ts` | ema, rsi, atr, findSwingPoints, getSupportResistanceZones, mfi, vwap | **`findSwingPoints` (line 312–332) mengakses `highs[i+k]`** — swing dikonfirmasi bar masa depan. DI REPLAY INI LOOKAHEAD. Kamu harus menangani ini (lihat Bagian C). |
| `UI/src/lib/signals.ts` | detectCandlePatterns (hammer/shooting star/doji/engulfing/morning-evening star/3 soldiers), newsSentimentAdjustment | pola candle: kontraknya diperjelas di desain §Gate B5 |
| `UI/src/lib/analysis.ts` | analyzeMarket (cache per-symbol) | engine analisa yang dipakai decision route |
| `UI/src/app/api/are/decision/route.ts` | decision engine lama + `DECISION_ENGINE_VERSION` + `styleConfigFingerprint` | JANGAN diubah. Kamu membangun sistem baru yang paralel, bukan memodifikasi ini. |
| `UI/src/app/api/news/route.ts` | fetch kalender ForexFactory (`ff_calendar.php?week=this&timezone=UTC`) + RSS | sumber berita; parser impact belum ada |
| `are/backtest.py` | `IsolatedBacktestEngine` dgn `execution_model` (`signal_timing='next_bar_open'`), `run_walk_forward_optimization` | referensi execution semantics |
| `are/data_pipeline.py` | `DataPurifier` (duplicate reject, chronology, toxic spread, market-closed tag) | dipakai untuk P3 nanti (bukan P0–P2) |
| `data/research/deals_sep7_raw.json` | 250 deals MT5 riil 7 Sep (hasil audit sebelumnya) | bahan replay |
| `data/research/micro_trades_sep7_fixed.json` | 122 trade ter-pairing (FIFO, direction dari deal IN) | pembanding baseline lama |

---

## 2. DELIVERABLES — EMPAT PAKET (P0–P2), lima commit

### PAKET 1 (commit #1) — `P0: CONTRACT FREEZE`
Buat direktori baru `strategy_v2/` di root repo (package mandiri, Python + JSON schema):
```
strategy_v2/
  contracts/
    timestamps.md          # temporal semantics (baca desain §Pagar 4): market timestamp
    data_integrity.md      # Layer A semantics: apa yang dianggap DATA_INVALID
    gate_semantics.md      # Layer B: 7 gate, reason codes lengkap (desain §1 Layer B)
    hypothesis_registry.json   # registry SEMUA hipotesis + nilai awal + status
    profile_scalp.json         # konfigurasi profil scalp (immutable per experiment)
    profile_micro.json         # konfigurasi profil micro
  schemas/
    decision_log.schema.json   # JSON Schema untuk decision log (desain §2)
  registry.py                  # loader registry + config_hash computation
```
Aturan wajib:
- **Experiment freeze (Pagar 1)**: `config_hash` = SHA-256 atas seluruh konten
  profile + hypothesis registry + cost model + execution timing + timeframe +
  timezone + session calendar. Satu byte berubah → hash berubah → identity baru.
- `hypothesis_registry.json` minimal memuat: `H-SESSION-01` (07:00–17:00 UTC awal),
  `H-RSI-BIAS-01` (M15 RSI>50 / <50), `H-RSI-ENTRY-01` (M5 pullback zona 40–55),
  `H-LOC-01` (SR distance ≤0.5×ATR), `H-LOC-02` (EMA pullback ≤0.25×ATR),
  `H-VOL-01` (ratio 1.2, baseline 5 bar), `H-ATR-01` (SL/TP multiplier),
  `H-Q1` (market quality bounds) — semua dengan field `{"id","value","status":"HYPOTHESIS","source":"design_v2.3"}`.
- Profil berisi: session_windows, atr multipliers, max_trades_per_day (RISK CAP:
  scalp 6, micro 20), cooldown (scalp 30m, micro 5m), volume gate on/off,
  max_stop_points (scalp 400, micro 250), min_stop formula params.
- `decision_log.schema.json` harus meng-enforce semua field wajib desain §2:
  `evaluation_timestamp` (epoch BAR CLOSE), `data_available_until`, `strategy_version`,
  `profile_id`, `hypothesis_registry_id`, `config_hash`, `dataset_hash`,
  `first_veto_reason`, `all_gate_results` (semua gate dinilai), `decision`,
  plus `market_snapshot`. **`now()`/wall-clock DILARANG masuk log** (Pagar 4).

### PAKET 2 (commit #2) — `P1: PURE GATE ENGINE`
Buat `strategy_v2/gates.py` — **fungsi murni, zero I/O, zero import MT5/DB/UI**:
```
layer_a_data_integrity(bars, ticks_meta, config) -> DATA_VALID | DATA_INVALID:<reason>
b1_news(now_ts, calendar, policy)     -> PASS | NEWS_EVENT_ACTIVE | NEWS_PROVIDER_DOWN
                                         | NEWS_DATA_STALE | NEWS_CALENDAR_UNAVAILABLE
b2_session(now_ts, session_windows)   -> PASS | FAIL:outside
b3_regime(m15_closed_bars, config)    -> PASS:BUY_ONLY | PASS:SELL_ONLY | FAIL:NO_TRADE
b4_location(profile, m15_zones, m5_bars, config) -> PASS:<ref> | FAIL:far
b5_trigger(m5_closed_bars, bias, config) -> PASS:<pattern> | FAIL:none
b6_volume(m5_closed_bars, config)     -> PASS | FAIL:ratio | FAIL:baseline_invalid
b7_risk(state, config, sl_calc)       -> PASS | FAIL:cap | FAIL:cooldown | FAIL:stop_bounds
evaluate_all(bars_dict, profile, config, market_snapshot) -> FullDiagnostic
decide(diagnostic) -> first_veto_reason | decision
```
Aturan implementasi:
- **Semua fungsi murni**: input apa pun dengan timestamp > T tidak boleh dipakai.
  Implementasi **evaluation-time slicing**: fungsi menerima `bars_until_T` (array yang
  SUDAH dipotong), bukan dataset penuh + T. Ini satu-satunya cara aman menghindari
  lookahead seperti `findSwingPoints`.
- **Anti-lookahead S/R (bug terbukti!)**: buat `strategy_v2/zones.py` — RE-IMPLEMENTASI
  swing detection & zone clustering yang deterministik dan hanya pakai bar ≤ T
  (definisi: swing = high/low tertinggi/terendah vs 5 bar kiri+kanan CONFIRMED —
  artinya swing baru terkonfirmasi di bar T jika bar [T-5..T] sudah closed;
  cluster distance = 0.75×ATR(M15); band ±0.5×ATR; max 5 zona/sisi; window 200 bar).
  DILARANG memanggil `getSupportResistanceZones` dari indicators.ts untuk replay
  (tidak bisa dijamin anti-lookahead).
- Candle pattern semantics: pola dari CLOSED bars; morning/evening star = 3 closed bars;
  signal bar = bar close trigger; entry = open bar T+1.
- Volume: baseline = mean volume 5 bar SEBELUM signal bar (exclude-self);
  zero-volume baseline → `FAIL:baseline_invalid`; missing → `FAIL:baseline_invalid`
  (bukan PASS). Terminologi: "tick-activity proxy".
- **Diagnostic full-evaluation**: `evaluate_all` menilai SEMUA gate meski satu sudah veto;
  `decide` menghasilkan first_veto. Keduanya output terpisah dalam satu record.
- Reason codes persis seperti desain §1 (terutama B1 news: 4 kode terpisah).
- Cost model helper `strategy_v2/costs.py`: `compute_cost(entry_spread, exit_spread,
  commission, slippage, delay)` — bila spread historis tak tersedia → flag
  `ESTIMATED_COST_MODEL` (Pagar cost model desain §4).

### PAKET 3 (commit #3) — `P2a: REPLAY ENGINE + DATA`
Buat `strategy_v2/replay.py`:
- Input: dataset candles (parquet/json) + profil frozen + config_hash.
- **Evaluation loop per bar M5 closed**: slice `bars[0..T]` → gates → decision record JSONL.
- **Append-only JSONL** ke `data/research/v2_replay/` (gitignored path OK, tapi engine-nya di-commit).
- Dua output terpisah (Pagar 3 — tiga truth):
  - **Decision Replay** — distribusi gate results, rejection reasons, funnel;
    TIDAK menghitung PnL.
  - **Execution Replay** — decision → simulator next-bar-open + cost model → trade list
    + PnL + expectancy, dengan label sumber spread (`HISTORICAL` atau `ESTIMATED_COST_MODEL`).
- **Diagnostic completeness report** (Pagar 6) — WAJIB ada sebelum "selesai":
  evaluation opportunities, DATA_INVALID count, veto per gate (+kombinasi), final signals,
  executed trades, rejected executions, gross expectancy, total costs, net expectancy.
- Determinism (Pagar 4): `now()` dilarang di seluruh jalur decision; waktu semantic =
  market timestamp. Run yang sama dua kali = log identik.
- Dataset 7 Sep: bangun candles M5 dari `data/research/deals_sep7_raw.json` (pairing FIFO
  sudah benar; kalau perlu candle, minta via bridge `/candles` DENGAN token — baca
  `data/bridge_token.txt` saat runtime, JANGAN hardcode; bridge mungkin down —
  bila begitu, pakai data yang ada dan catat limitasi, JANGAN mengarang data).
- **Data qualification ringan** untuk dataset replay (missing bars, duplicate ts,
  OHLC integrity) — lapor di output, bila invalid → jangan dipakai tanpa catatan.

### PAKET 4 (commit #4) — `P2b: INVARIANT + ADVERSARIAL TESTS`
Buat `tests/strategy_v2/` — setiap invariant DUA arah: happy path + adversarial mutation:
1. **No-lookahead global**: inject future candle ke input → hasil evaluasi TIDAK berubah.
   Uji khusus zones: `zone(T)` dari `bars[0..T]` = pure & identik kapan pun dihitung ulang.
2. **Closed-bar semantics**: sinyal dari forming bar → tidak ada / ditolak.
3. **Execution timing**: eksekusi < T+1 open → ditolak.
4. **Determinism**: replay sama ×2 → JSONL identik (bit-per-bit field deterministik).
5. **News reason codes**: 4 kode terpisah, semua → NO_NEW_ENTRY.
6. **Layer separation**: DATA_INVALID tidak masuk distribusi rejection strategi.
7. **Volume baseline guard**: exclude-self, zero-baseline = FAIL, missing = FAIL.
8. **Diagnostic ≠ operational**: full-evaluation tidak mengubah first_veto/decision.
9. **Adversarial mutation suite** (Pagar 5) — minimal: future candle disisipkan,
   historical candle dimodifikasi, data missing, NaN, duplicate timestamp,
   spread ekstrem, stale data, config berubah mid-run (harus mengubah config_hash →
   identity baru), urutan input diacak. **Sistem harus GAGAL DENGAN BENAR** (rejection
   eksplisit/error yang terdefinisi), bukan pass diam-diam.
10. **Funnel completeness**: replay output memenuhi checklist Pagar 6.

### PAKET 5 (commit #5) — `P2c: REPLAY 7 SEPTEMBER + LAPORAN`
Jalankan replay penuh atas data 7 Sep dengan kedua profil:
- Bandingkan vs baseline lama (122 trade, −$42.02): frekuensi, funnel, gate distribution.
- Hasil P2 BUKAN bukti profit — hanya: timing benar, gate behave, rejection logged,
  cost model jalan, no-lookahead terbukti, funnel lengkap.
- Tulis `strategy_v2/REPORT_P2.md`: funnel completeness + keputusan bisa dijalankan
  + limitasi (dataset 1 hari, dsb).

---

## 3. KRITERIA TERIMA (fail-closed — audit akan mengecek ini satu per satu)
1. `python -m pytest tests/ -q --ignore=tests/test_bot_lifecycle.py` → **≥ 678 + semua test baru PASS, 0 fail** (baseline tidak boleh pecah).
2. Semua test strategy_v2 lulus, TERMASUK adversarial mutations.
3. Replay 7 Sep ×2 → decision log **identik**; tidak ada `now()` di jalur decision (grep bisa dibuktikan).
4. Funnel completeness lengkap (angka di tiap tahap funnel ada di report).
5. Tidak ada file di luar daftar yang berubah: `strategy_v2/**`, `tests/strategy_v2/**`, `docs/DESIGN_STRATEGY_V2.md` (hanya bila perlu catatan kecil), `pyproject.toml` (bila perlu daftar marker/path test).
6. Tidak ada perubahan pada: `are/bot.py`, `are/mt5_server.py`, `UI/src/**` (gate engine PYTHON murni; integrasi ke decision engine TS = fase terpisah setelah audit).
7. Tanpa secret/runtime di commit (bridge token, bot_state, dsb.).
8. Laporan akhir (format): per paket — file berubah, hasil test (angka pasti), bukti eksekusi (potongan output), commit hash, `git log --oneline`, `git status --short`.

## 4. BATASAN KERAS (baca dua kali)
- DILARANG mengubah logika sinyal live, bridge, bot, WFO, gate lama.
- DILARANG menambah dependency baru (stdlib + polars + pytest yang sudah ada cukup).
- DILARANG menambah indikator/AI/ML/fitur di luar desain. Scope creep = penolakan.
- DILARANG memanggil `now()`/`Date.now()` untuk semantic trading di strategy_v2.
- DILARANG men-commit `data/bridge_token.txt`, `data/bot_state_*.json`, runtime state.
- Bila ada keputusan desain yang ambigu: pilih konservatif, catat keputusan + alasannya
  di `strategy_v2/DECISIONS.md` (append), jangan diam-diam memilih.
- Bila bridge/UI mati dan data tak terambil: jangan mengarang data; catat limitasi, kerjakan
  yang bisa dengan data tersedia, laporkan.

## 5. PROSES EKSEKUSI
0. Baca `docs/DESIGN_STRATEGY_V2.md` (v2.3) penuh — itu kontrakmu.
1. Baseline: `python -m pytest tests/ -q --ignore=tests/test_bot_lifecycle.py` (harus 678).
2. Paket 1 → test → commit.
3. Paket 2 → test → commit.
4. Paket 3 → jalankan replay → commit.
5. Paket 4 → semua invariant + adversarial → commit.
6. Paket 5 → replay penuh + REPORT_P2.md → commit.
7. Full suite + push origin/main + LAPORAN AKHIR (format di §3.8).

## 6. AUDIT YANG AKAN DILAKUKAN ATASMU (siapkan buktinya)
Auditor (bukan kamu) akan: memverifikasi setiap commit via `git show`, menjalankan ulang
replay ×2 untuk determinism, menyisipkan future candle untuk menguji no-lookahead,
memodifikasi config untuk memastikan hash berubah, meng-grep `now()` di jalur decision,
dan membandingkan funnel dengan klaim laporan. Kecurangan/kegagalan pada satu kriteria
= mandat dikembalikan untuk revisi.
