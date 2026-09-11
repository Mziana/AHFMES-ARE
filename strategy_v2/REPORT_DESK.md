# REPORT DESK — Implementasi Analyst Desk v2.5 (plan 7-langkah)

Tanggal: 2026-09-09 · Plan: `.hermes/plans/2026-09-08_133000-are-analyst-desk-7-steps.md`
Status: **Paket A–D terimplementasi penuh & terverifikasi.** Dua item visi di luar
scope plan (self-learning otomatis, pemahaman kausal news) — detail di §6.

---

## 1. Ringkasan eksekutif

ARE kini punya alur **analyst desk 7-langkah** di atas gate engine yang sudah
teruji — gate veto TIDAK diubah sama sekali:

```
MT5 feed (1) ─► Context (2) ─► Setup (3) ─► SCORE (4: BARU, deskriptif 0-100)
     ─► Risk (5: B7 veto tetap keras) ─► TRADE PLAN (6: BARU, narrative)
     ─► JOURNAL (7: BARU, plan→paper→review→usulan)
```

- **Full suite: 874 passed, 0 fail** (baseline sebelum desk: 866 → +8 test baru
  yang mengunci kontrak desk; 105 subtests tetap hijau).
- **Determinism ×2**: replay window F2 ×2 → JSONL `cmp` byte-identik (Pagar 4).
- **Schema `--validate`: 125 records OK** — field baru semuanya OPTIONAL;
  record lama tanpa field desk tetap valid (backward-compatible).
- **Layer separation teruji**: menghapus / memutasi H-SCORE-DESK-01 dari
  registry → `decision` & `first_veto_reason` 125 record **identik persis**.
  Scorer adalah layer presentasi; gate veto tetap satu-satunya jalur entry.
- **Funnel 3-tier mengekspos hampir-setup** yang funnel biner sembunyikan
  (detail §4).

## 2. Status per paket plan

| Paket | Deliverable plan | Status | Artefak |
|---|---|---|---|
| A1 | SetupScorer + H-SCORE-DESK-01 | ✅ | `strategy_v2/scorer.py`, registry (16 hipotesis, entry baru append-only), `tests/strategy_v2/test_scorer.py` (15 test) |
| A2 | setup_score → decision log (optional) | ✅ | `replay.py`, `schemas/decision_log.schema.json`, test backward-compat |
| B1 | TradePlanBuilder deterministik | ✅ | `strategy_v2/trade_plan.py`, test di test_scorer.py |
| B2 | Wire plan ke replay + funnel 3-tier + laporan | ✅ | `replay.py` (`build_funnel` desk_tiers), `REPORT_P2.md` §12 |
| C1 | JournalLoop append-only + paper driver | ✅ | `strategy_v2/journal.py`, `strategy_v2/paper.py`, `tests/strategy_v2/test_journal.py` (7 test), `tests/strategy_v2/test_paper_desk.py` (4 test) |
| C2 | Review report USULAN (tanpa auto-apply) | ✅ | `strategy_v2/review_report.py`, `tests/strategy_v2/test_review_report.py` (6 test) |
| D | UI desk read-only | ✅ | `UI/src/app/api/are/desk/route.ts`, `UI/src/app/desk/page.tsx` (tsc: 0 error baru) |

Kontrak bobot & tier (persis plan, di-hash Pagar 1):
`weights = {trend:30, momentum:20, volume:15, level:15, catalyst:10, rr:10}`,
`tiers = {watch:40, paper:60, trade:75}`. Tier boundary exact teruji:
39→PAST, 40→WATCH, 59→WATCH, 60→PAPER, 74→PAPER, 75→TRADE (label skor —
B5 patern STRONG=10/MODERATE=6, vol_ratio ≥1.2→10 linear ke 0.8→0,
distance_atr 0→10 linear ke 0.5→0, RSI M5 dekat 50→10, RR 2.0→10).

## 3. Keputusan turunan (tercatat di DECISIONS.md)

1. **Bahasa trade plan = Inggris** (konsisten decision log; open question §2).
2. **Tier PAPER di-paper-trade OTOMATIS di research plane** memakai simulator
   F1b yang SAMA (`run_execution_replay` — next-bar-open, BID/ASK, cost model,
   state machine; anti cost-soup / satu simulator). Approval manual hanya untuk
   live (open question §1, sesuai rekomendasi plan).
3. Field log baru optional: `setup_score`, `trade_plan`, `risk_calc` (raw B7
   input utk paper simulator), `market_snapshot.close`.

## 4. Hasil funnel 3-tier (window F2: Sep 7 22:00 → Sep 8 08:25, MICRO_V2)

| Tier | n | Arti |
|---|---|---|
| PAST | 28 | skor < 40 — tidak menarik perhatian |
| WATCH | 78 | skor 40–59 — **"hampir-setup" yang funnel biner sembunyikan** |
| PAPER | 19 | skor 60–74 — layak paper trade otomatis (research plane) |
| TRADE | 0 | skor ≥ 75 (label; entry tetap wajib lolos semua gate veto) |

Funnel lama: **0 lolos semua gate** dari 123 bar layer-B. Funnel desk:
**97 bar WATCH+** — seleksi gate (B2 session, B4 location) memang sangat ketat;
sekarang ketatnya terlihat, bukan tersembunyi. Contoh plan narrative hasil
replay (deterministik):

> thesis: `XAUUSD pulled back to ema9@4412.33 with subdued volume; BUY regime
> aligned (ATR 227 pts, three_white_soldiers trigger).`
> invalidation: `Close back below 4409.69 (SL 284 pts from ema9@4412.33).`
> confidence 58 (= skor H-SCORE-DESK-01; "descriptive score, not calibrated
> probability").

⚠️ Bukan hasil P5/P6 — tidak ada klaim edge baru; ini visibilitas, bukan
profitabilitas. expectancy per tier baru bermakna setelah journal terisi
paper run multi-hari (§6.1).

## 5. Pagar yang diuji eksplisit

| Pagar | Test |
|---|---|
| Layer separation (skor ≠ keputusan) | `test_score_never_changes_first_veto`, `test_weight_mutation_mid_registry_does_not_change_decisions` — hapus/mutasi registry → keputusan identik |
| Determinism (Pagar 4) | skor/plan/journal ×2 byte-identik; tanpa `open(`/`time.time`/`datetime.now` di scorer; replay ×2 `cmp` identik |
| Registry-driven (Pagar 1) | mutasi 1 bobot → config_hash berubah; bobot degenerate → None (fail-closed, bukan skor pura-pura) |
| Adversarial | NaN/None/missing → komponen 0 tanpa crash, tanpa kredit |
| Append-only journal | prefix file tidak pernah berubah mundur; hanya mode `'a'`; tidak ada import gates/replay di journal (paper TIDAK mengubah gate) |
| Review math | expectancy = avg net; win_rate; avg_rr; format kompatibel `data/learning/buckets.json` (n/win/pts/pnl/updated) |

## 6. Yang SENGAJA di-exclude plan — dan jalan menuju sana

Keduanya adalah bagian dari visi user ("ARE understands what's happening and
why… Improve: refine the edge") yang plan tetapkan **di luar mandat ini**
dengan alasan arsitektural — bukan kelalaian, dan bukan "ditolak selamanya".

### 6.1 Self-learning otomatis ("Improve: refine the edge")

**Kenapa di-exclude:**
1. **Experiment freeze v2.3 (Pagar 1)**: bobot/ambang hanya boleh berubah
   sebagai hipotesis BARU di registry dengan genealogy + keputusan owner.
   Auto-tuning diam-diam = melanggar kontrak paling inti dari pembelajaran
   insiden 122-trade (scoring bebas = score soup = akar masalah lama).
2. **Sampel belum ada**: usulan bobot butuh n ≥ 20 per band (kontrak C2);
   journal paper baru dibuat hari ini — kosong. Belajar dari sampel kecil =
   overfit yang tersamar sebagai "improvement".
3. **Prasyarat F1/F2 baru saja selesai**: PnL benar baru terjamin sejak
   2026-09-08; review otomatis atas PnL lama akan mempelajari angka fiksi.

**Yang SUDAH dibangun untuk jalur menuju otomasi (loop setengah-jadi):**
- Journal paper append-only → `review()` agregat per
  `<profile>|<direction>|p_<pattern>|b_<tier>` — format kompatibel
  `data/learning/buckets.json`, jadi pembelajaran live & paper bisa digabung.
- `review_report.py` menghasilkan **USULAN otomatis** (mis. "band PAPER
  expectancy ≤ 0 pada n≥30 → usulkan nonaktifkan tier PAPER"; "band PAST
  positif n≥20 → usulkan turunkan tiers.watch") — manusia tinggal approve.
- Semua usulan mengharuskan hipotesis child (parent tercatat) — genealogy
  otomatis terjaga.

**Jalan menuju "otomatis" yang tetap aman (usulan bertahap):**
- **Tahap 1 (sekarang)**: paper run multi-hari → review report mingguan →
  owner approve usulan (manual-in-the-loop penuh).
- **Tahap 2**: kontrak `H-DESK-AUTO-01` — sistem boleh MENYIAPKAN hipotesis
  child lengkap (parameter + provenance + test RED) di folder usulan, tapi
  apply tetap satu perintah owner (diff + config_hash baru terlihat dulu).
- **Tahap 3 (opsional, risiko tinggi)**: auto-apply dengan guard keras
  (hanya perubahan bobot ≤ ±5 absolut, cooldown 2 minggu antar perubahan,
  rollback otomatis bila expectancy 7-hari turun > X). Ini butuh mandat baru
  + audit — sengaja TIDAK dibangun sekarang.

### 6.2 Pemahaman kausal news ("understands what's happening and why")

**Kenapa di-exclude:**
1. **Data kausal tidak ada**: bridge MT5 tidak menyediakan kalender historis
   per-bar (keputusan DECISIONS.md 2026-09-08: B1 replay memakai artifact
   arsip dengan provenance `information_available_at`). Tanpa riwayat
   (event → reaksi harga) yang jujur, "pemahaman sebab-akibat" pasti karangan
   — melanggar prinsip mandat "jujur > karangan".
2. **B1 sendiri sudah cukup merepotkan**: provenance kalender (P0-01
   look-ahead guard) membuat replay multi-hari butuh arsip kalender yang
   di-fetch SEBELUM window — dataset reaksi butuh disiplin provenance yang
   sama, tapi dikali ribuan event.
3. **Satu perubahan per eksperimen**: menambah faktor kausal di saat yang
   sama dengan journal paper baru mulai = dua variabel berubah bersamaan;
   atribusi jadi mustahil.

**Yang SUDAH ada sebagai fondasi:**
- B1 news gate fail-closed dengan reason code 4 arah terpisah & teruji
  (`NEWS_EVENT_ACTIVE` / `NEWS_PROVIDER_DOWN` / `NEWS_DATA_STALE` /
  `NEWS_CALENDAR_UNAVAILABLE`).
- Artifact kalender ber-provenance (`save_calendar_artifact`, hash masuk
  config_hash) — infrastruktur provenance yang dipakai dataset reaksi nanti.
- `market_snapshot` + decision log per-bar — bahan mentah event-study sudah
  terekam; setiap bar punya konteks gate lengkap.

**Jalan menuju pemahaman kausal (usulan bertahap):**
- **Tahap 1 — pengumpulan**: arsip kalender otomatis per minggu (fetch SEBELUM
  window, cron di bridge), disimpan sebagai artifact ber-hash. Tanpa ini tidak
  ada titik mulai.
- **Tahap 2 — event-study deskriptif** (hipotesis `H-NEWS-REACT-01`): untuk
  tiap event high-impact USD, ukur distribusi reaksi XAUUSD (±15/±30/±60 menit:
  range, arah, ATR multiple) dari dataset yang SUDAH terekam di decision log +
  M1 (R1 S0.1: 150k bar M1 sudah ada). Output: tabel statistik deskriptif,
  bukan prediksi.
- **Tahap 3 — gate ekspektasi**: B1 naik kelas dari fail-closed biner ke
  "blackout ekspektasi" (window sekitar event high-impact diperlebar secara
  deterministik dari data Tahap 2). Tetap veto keras — tidak menjadi scorer.
- Yang TETAP di luar cakrawala: LLM membaca berita bebas-teks → keputusan.
  Itu jalan kembali ke score soup dengan langkah lebih besar.

### 6.3 Implikasi keputusan exclude ini

- Visi user belum 100% tercapai — sengaja: 5 dari 7 langkah bermakna harus
  matang dulu (journal terisi, expectancy per tier terbaca) sebelum dua
  langkah "pemahaman & perbaikan otomatis" bisa dibangun tanpa mengulang
  kegagalan lama.
- Semua prasyarat teknis Tahap-1 untuk keduanya sudah tersedia sekarang
  (journal + registry genealogy + provenance artifact + M1 dataset).

## 7. Keputusan yang menunggu owner

1. Approve arah Tahap-2 self-learning (`H-DESK-AUTO-01`, usulan disiapkan
   otomatis, apply manual)?
2. Mulai arsip kalender otomatis mingguan (prasyarat jalur kausal)?
3. Paper run multi-hari: tier PAPER otomatis sudah aktif di research plane —
   mau dijalankan penuh sekarang?
4. Commit implementasi desk (belum di-commit; semua perubahan berada di
   working tree).

## 8. Cara pakai singkat

```bash
# replay + skor + plan (schema tervalidasi)
python -m strategy_v2.replay --profile micro \
  --m5 data/research/v2_replay/dataset_f2_m5.json \
  --m15 data/research/v2_replay/dataset_f2_m15.json \
  --calendar data/research/v2_replay/calendar_multiday.json \
  --out data/research/v2_replay --validate

# paper desk (tier PAPER/TRADE → simulator F1b → journal append-only)
python -c "from strategy_v2.paper import run_paper_desk; ..."   # driver teruji

# review → laporan markdown + usulan
python -c "from strategy_v2.review_report import build_review_report_from_journal; \
print(build_review_report_from_journal('data/research/v2_replay/journal_micro.jsonl'))"
```
UI: buka `/desk` (read-only — tier funnel, setup + skor per dimensi, plan
terakhir, first veto).
