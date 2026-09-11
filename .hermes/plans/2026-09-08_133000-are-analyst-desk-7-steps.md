# PLAN — ARE TRADING DESK v2.5: Dari Gate Engine ke "Analyst Desk" 7-Langkah

Tanggal: 2026-09-08 · Penyusun: Lead Architect (audit-verified terhadap kode)
Status: PLAN — menunggu persetujuan owner sebelum mandat implementasi dibuat.

---

## GOAL (satu kalimat)

Mengubah ARE dari "gate engine biner (WAIT/TRADE)" menjadi **analyst desk 7-langkah**
(Feed → Context → Setup → Score → Risk → Trade Plan → Journal) yang menghasilkan
**trade plan lengkap bertulis** (thesis, invalidation, confidence) untuk SETIAP
setup yang teramati — bukan hanya yang ditrade — dengan semua scoring sebagai
**hipotesis terdaftar yang diuji**, bukan kebijaksanaan bebas.

## CURRENT CONTEXT / ASSUMPTIONS (audit-verified)

Yang SUDAH ada (jangan dibangun ulang):
- **Step 1 Feed**: bridge MT5 (`are/mt5_server.py` — /account, /candles dgn tick_volume,
  /ticks, auth token P0-01) + `UI/src/lib/indicators.ts` (ema, rsi, atr, macd, adx,
  mfi, vwap, `getSupportResistanceZones`).
- **Step 2 Context**: `strategy_v2/gates.py` B3 (regime M15: BUY_ONLY/SELL_ONLY/NO_TRADE),
  `UI/src/lib/analysis.ts` analyzeMarket (13 indikator, MTF confirmation).
- **Step 3 Setup**: `strategy_v2/gates.py` B4 (location: SR zone / EMA pullback) +
  B5 (closed-candle trigger patterns dari `signals.ts::detectCandlePatterns`).
- **Step 5 Risk**: `strategy_v2/gates.py` B7 (stop bounds ATR+spread floor, cooldown,
  sizing konstan-dolar) + live safety stack (equity breaker, kill switch, reset harian).
- **Step 7 parsial**: `are/shadow_ab.py` (paper tracking), `data/learning/buckets.json`
  (agregat win/loss per fingerprint), decision log JSONL (`data/research/v2_replay/`).
- Provenance penuh: `config_hash`, `dataset_hash`, `engine_version` (Pagar 1/4 v2.3).

Yang BELUM ada (gap nyata — hasil audit):
- **Step 4 Score**: v2.3 sengaja MENGHAPUS scoring (masalah bot lama = score soup).
  Visi user meminta scoring kembali — desain harus mendamaikan keduanya:
  scoring sebagai **descriptive triage** (watch/paper/past), BUKAN mesin keputusan.
- **Step 6 Trade Plan narrative**: decision log punya `gate_results` + angka, tapi
  tidak ada `thesis`/`invalidation`/`confidence` bertulis.
- **Three-tier outcome**: funnel sekarang biner (signal/WAIT); visi user: WATCH →
  PAPER → PAST (atau TRADE setelah risk check). Data funnel 7 Sep: 222 evaluasi,
  0 lolos semua gate, padahal 42 lolos volume, 5 lolos location, 45 lolos trigger —
  tiga-tier akan mengekspos "hampir-setup" yang sekarang tersembunyi.
- **Journal loop**: belum ada satu alur plan → paper → review → improve yang
  menghubungkan shadow trade ke peningkatan hipotesis terdaftar.

Asumsi/aturan yang dipertahankan (dari v2.3/v2.4 — tidak dinegosiasikan ulang):
1. Closed-bar only; entry next-bar-open. 2. No-lookahead global (evaluation-time
slicing). 3. `now()` dilarang di jalur keputusan (market timestamp). 4. Experiment
freeze: scoring weights = hypothesis registry (H-SCORE-xx), bukan angka bebas.
5. Live path TIDAK disentuh — semua ini research/replay plane dulu.
6. Execution truth repair (F1/F2 mandat `MANDAT_EXECUTION_TRUTH_F1_F2.md`) = PRASYARAT
Fase ini (PnL harus benar sebelum journal bisa "review" dengan jujur).

---

## ARCHITECTURE / APPROACH

Menambah **lapisan presentasi & kualitas di ATAS gate engine yang sudah ada**, tanpa
mengubah gate semantics: gate tetap veto keras (sandarannya sudah teruji). Yang baru:
(1) `SetupScorer` — mengubah `all_gate_results` + `market_snapshot` menjadi skor
0–10 per dimensi (trend/momentum/volume/level/catalyst/rr) + total 0–100, dengan
SEMUA bobot & threshold dari hypothesis registry; (2) `TradePlanBuilder` — mengubah
evaluasi (lolos atau hampir-lolos) menjadi `TradePlan` JSON bertulis (thesis,
invalidation, confidence, entry/stop/target) untuk outcome WATCH/PAPER/TRADE;
(3) `JournalLoop` — menghubungkan plan → shadow/paper execution → outcome → update
bucket hipotesis. Semua murni deterministik (Pagar 4 tetap berlaku), direplay-able,
dan diuji adversarial seperti P0–P2.

Aliran baru (menempatkan langkah user di atas infrastruktur):

```
MT5 feed (1) ──► Context (2: regime+snapshot) ──► Setup (3: location+trigger)
     ──► SCORE (4: baru, descriptive 0-100 + tier) ──► RISK (5: B7 veto — TETAP keras)
     ──► TRADE PLAN (6: baru, narrative) ──► JOURNAL (7: baru, plan→paper→review→improve)
```

---

## STEP-BY-STEP TASKS

> Konvensi: semua file baru di `strategy_v2/` (Python, research plane) dan
> `tests/strategy_v2/`. Zero I/O di scorer/builder. Setiap task = RED test dulu →
> implement minimal → GREEN → commit. Full suite (`747+` baseline) wajib tetap hijau
> di akhir tiap paket. Prasyarat: mandat F1/F2 (execution truth) selesai — kalau
> belum, jalankan itu dulu.

### PAKET A — Step 4: SetupScorer (commit 1–2)

**A1. `strategy_v2/scorer.py` — struktur + registry.**
- Tambah ke `strategy_v2/contracts/hypothesis_registry.json` (append, status
  HYPOTHESIS, jangan ubah entri lama):
  ```json
  "H-SCORE-01": {"value": {"weights": {"trend": 30, "momentum": 20, "volume": 15,
     "level": 15, "catalyst": 10, "rr": 10}, "tiers": {"watch": 40, "paper": 60,
     "trade": 75}}, "status": "HYPOTHESIS", "source": "vision-user-2026-09-08"}
  ```
- Buat `strategy_v2/scorer.py`:
  ```python
  def score_setup(all_gate_results: dict, market_snapshot: dict,
                  setup: dict, risk: dict, weights: dict) -> dict:
      """0-100 descriptive score per dimensi. PURE. Tidak mengubah decision."""
      # trend: dari b3_regime (PASS arah=10, NO_TRADE=0) — skala ke 0-10
      # momentum: rsi_m5 posisi dalam zona pullback (dekat 50 = baik utk continuation)
      # volume: vol_ratio (b6) — >=1.2 -> 10, linear turun ke 0 di 0.8
      # level: b4 distance_atr (0.0 = di level = 10; >=0.5 = 0)
      # catalyst: pola strength (STRONG pattern=10, MODERATE=6, none=0)
      # rr: tp_points/sl_points (2.0+ -> 10; 1.0 -> 4)
      # total = sum(weight_i * dim_i) / sum(weights) * 100
      # tier: >=paper->"PAPER", >=watch->"WATCH", else "PAST"
      return {"dimensions": {...}, "total": int, "tier": "WATCH|PAPER|PAST"}
  ```
- **RED test** `tests/strategy_v2/test_scorer.py`:
  - `test_score_pure_and_deterministic` — input sama ×2 → output identik.
  - `test_tier_boundaries` — total 39→PAST, 40→WATCH, 60→PAPER, 74→PAPER, 75→TRADE-tier.
  - `test_weights_from_registry` — ubah weight 1 poin di registry → config_hash berubah
    (Pagar 1) → skor bisa berubah; mutasi weight mid-run tertangkap.
  - `test_score_never_changes_first_veto` — scorer menerima gate_results yang sudah
    ada; `decision`/`first_veto_reason` output replay TIDAK berubah (scorer = layer
    presentasi, bukan gate).
- Verifikasi: `python -m pytest tests/strategy_v2/test_scorer.py -v` → gagal dulu (RED),
  implement, lulus (GREEN).
- **Commit 1**: `feat(strategy-v2): A1 SetupScorer — skor deskriptif 0-100 dari gate diagnostics (H-SCORE-01)`

**A2. Integrasikan scorer ke decision log (opsional field, backward-compatible).**
- `strategy_v2/schemas/decision_log.schema.json`: tambah optional `setup_score` object
  (dimensions, total, tier). `strategy_v2/replay.py`: panggil scorer setelah gates,
  tulis ke record. Schema `--validate` tetap wajib lulus untuk 222 record lama
  (field optional → record lama tetap valid).
- **RED test**: `test_setup_score_in_log` (record baru punya setup_score),
  `test_old_records_still_valid` (schema backward-compatible).
- **Commit 2**: `feat(strategy-v2): A2 setup_score masuk decision log (optional field)`

### PAKET B — Step 6: TradePlanBuilder (commit 3–4)

**B1. `strategy_v2/trade_plan.py`.**
```python
def build_trade_plan(record: dict, profile: dict, broker_meta: dict) -> dict:
    """Trade plan narrative dari evaluasi. PURE. Untuk tier PAPER/TRADE (dan
    WATCH dengan plan hipotesis). Semua angka dari record, teks dari template."""
    # thesis: "Price [bounced off|pulled back to] <zone_ref> with <volume_state>
    #          volume; <regime> regime aligned" — dari setup/gate_results/snapshot
    # invalidation: "Close back below <entry - sl_points> <basis>" — dari sl_points
    # confidence: total skor (transparent: = H-SCORE-01 output, bukan angka ajaib)
    # entry/stop/target/rr: dari record (sl_points/tp_points) + broker_meta point value
    return {"plan_id": ..., "thesis": str, "invalidation": str, "confidence": int,
            "entry_points": ..., "stop_points": ..., "target_points": ..., "rr": float}
```
- Aturan teks: deterministik — template + angka dari record. Dilarang LLM/free-text.
- **RED test** `tests/strategy_v2/test_trade_plan.py`:
  - `test_plan_fields_complete` — semua field ada & non-empty untuk tier PAPER.
  - `test_plan_deterministic` — input sama → teks sama persis (×2).
  - `test_plan_numbers_match_record` — entry/stop/target = angka record, bukan
    hasil hitung lain (consistency dengan execution replay).
  - `test_invalidations_mentions_price` — invalidation memuat harga konkret.
- **Commit 3**: `feat(strategy-v2): B1 TradePlanBuilder — thesis/invalidation/confidence deterministik`

**B2. Wire plan ke replay output.**
- `run_decision_replay` menghasilkan `trade_plan` pada record dengan tier PAPER/TRADE
  (dan plan "hipotesis" untuk WATCH bila `profile.plan_on_watch=true` — masuk profil).
- Jalankan replay 7 Sep ulang (dataset sudah ada di `data/research/v2_replay/`) →
  berapa WATCH/PAPER/PAST? Ini angka baru yang menarik: funnel lama bilang 0 lolos;
  funnel baru mungkin bilang "X WATCH" — laporkan jujur di `REPORT_P2.md` (append).
- **Commit 4**: `feat(strategy-v2): B2 trade plan masuk replay + laporan funnel 3-tier 7 Sep`

### PAKET C — Step 7: JournalLoop (commit 5–6)

**C1. `strategy_v2/journal.py`.**
- `open_paper_trade(plan, fill_ts, fill_price) -> journal_entry` — dipanggil execution
  replay saat tier PAPER (paper = dijalankan simulator, dilabeli `paper:true`).
- `close_paper_trade(entry, exit_ts, exit_price, reason)` → outcome (pnl, rr realized,
  held_bars).
- `review(journal_path) -> dict` — agregat per (profile, direction, pattern, score_band):
  n, win_rate, avg_rr, expectancy — format kompatibel `data/learning/buckets.json`
  (supaya dua sistem belajar dari satu format).
- Append-only JSONL: `data/research/v2_replay/journal_<profile>.jsonl` (runtime path).
- **RED test** `tests/strategy_v2/test_journal.py`: determinism, append-only
  (file tidak boleh dimodifikasi mundur), review math (expectancy = avg net),
  paper-trade TIDAK pernah mengubah decision gate (layer separation).
- **Commit 5**: `feat(strategy-v2): C1 JournalLoop — plan→paper→outcome→review (append-only)`

**C2. Review loop → hypothesis feedback (manual-in-the-loop, TANPA auto-tuning).**
- `strategy_v2/review_report.py`: generate laporan markdown dari `review()` —
  "score band X punya expectancy positif di n>=20; band Y negatif" → rekomendasi
  perubahan H-SCORE-01/H-VOL-01 ditulis sebagai USULAN (file), TIDAK auto-applied
  (experiment freeze tetap; perubahan = identity baru + keputusan owner).
- **Commit 6**: `feat(strategy-v2): C2 review report — usulan perubahan hipotesis dari data paper`

### PAKET D — Wiring UI (opsional, setelah C; commit 7)

- Endpoint read-only `/api/are/desk` (Next.js) yang menampilkan: context snapshot,
  setup aktif + skor per dimensi, tier, trade plan terakhir — dari decision log JSONL
  (bukan engine baru). Halaman sederhana di `UI/src/app/desk/page.tsx`.
- Wajib lewat middleware auth (sudah ada) dan tanpa mengubah decision engine.
- **Commit 7**: `feat(UI): desk page — read-only analyst desk view dari decision log`

---

## TESTS / VALIDATION (ringkas per paket; detail TDD di tiap task)

| Paket | Gate kualitas |
|---|---|
| A | scorer pure+deterministic; tier boundary exact; registry-driven (Pagar 1); **tidak mengubah decision** (layer separation test) |
| B | plan deterministik & numbers-consistent dengan execution replay; schema backward-compatible (222 record lama tetap valid) |
| C | journal append-only; review math benar; paper TIDAK mengubah gate; format kompatibel buckets.json |
| D | endpoint read-only, auth middleware, tsc bersih |
| Semua | full suite ≥747+baru, 0 fail; replay ×2 identik; adversarial: NaN/missing/duplicate/weight-mutation gagal dengan benar |

Verifikasi akhir tiap paket: `python -m pytest tests/ -q --ignore=tests/test_bot_lifecycle.py -o addopts=""`
→ angka expected: ≥ 747 + jumlah test baru, 0 failed.

## RISKS, TRADEOFFS, OPEN QUESTIONS

**Risiko:**
1. **Scoring = jalan kembali ke score soup?** Mitigasi: scorer TIDAK mengubah keputusan
   (test layer-separation), hanya triage untuk manusia & journal; gate veto tetap satu-
   satunya jalur entry. Kalau suatu saat scoring dipakai memutuskan, itu perubahan
   kontrak = identity baru + persetujuan owner.
2. **Confidence 80% = angka pura-pura.** Mitigasi: confidence = skor transparan dari
   registry, dilabeli "descriptive, bukan probabilitas terkalibrasi"; kalibrasi beneran
   butuh sampel journal besar (F2 multi-hari + paper run).
3. **Scope creep ke live.** Mitigasi: semua di research plane; wiring ke bot = fase
   terpisah + mandat baru, hanya setelah F1/F2 + journal teraudit.
4. **Watch/PAPER bisa menumpahkan trade "hampir" yang sebenarnya buruk** (bias seleksi
   menipu diri). Mitigasi: journal mencatat SEMUA tier; review report wajib menampilkan
   expectancy per tier — kalau PAPER expectancy ≤ 0, tier PAPER dinonaktifkan (keputusan
   owner dari data).

**Tradeoffs:**
- Menambah ~2 modul + 2 field schema (kecil, backward-compatible) vs visi user yang
  butuh narrative & jurnal — sepadan karena journal adalah mesin pembelajaran
  jangka panjang, dan narrative membuat bot bisa "dipahami manusia".
- Scoring descriptive (bukan decision) sedikit "kurang otentik" terhadap visi user
  ("SETUP SCORE = 80/100" sebagai filter) — tapi ini sengaja: bukti 7 Sep menunjukkan
  scoring bebas adalah akar 122 trade. Score boleh memPRIORITASKan perhatian manusia,
  bukan menggantikan gerbang.

**Open questions (untuk owner, jawab sebelum mandat ditulis final):**
1. Tier PAPER: dijalankan otomatis oleh replay (semua setup PAPER di-paper-trade), atau
   hanya yang di-approve manual? Rekomendasi saya: otomatis di research plane (tanpa
   biaya), manual hanya untuk live.
2. Bahasa thesis/invalidation: Inggris (konsisten log) atau Indonesia (konsisten UI)?
3. Paket D (UI desk) masuk mandat ini atau sesi terpisah?
4. Konfirmasi: implementasi boleh mulai SEKARANG, atau tunggu F1/F2 (execution truth)
   selesai dulu? Rekomendasi saya: F1/F2 dulu (journal tanpa PnL benar = review palsu).

---

## YANG BELUM TERCAKUP (jujur — supaya ekspektasi benar)
- "ARE understands what's happening and why" dalam arti pemahaman sebab-akibat
  (news→price reaction) belum bisa: butuh data kausal (kalender+reaksi historis) —
  kandidat eksperimen SETELAH baseline v2 terbukti (satu perubahan per eksperimen).
- "Improve: refine the edge" otomatis (self-learning) — sengaja manual-in-the-loop:
  sistem mengusulkan, owner memutuskan (experiment freeze v2.3 melarang auto-tuning).
