# TEMPORAL SEMANTICS (PAGAR 4)

Sumber waktu semantic untuk seluruh jalur decision strategy_v2 adalah
**MARKET TIMESTAMP dari data candle** — dilarang keras memakai `now()`,
`time.time()`, `datetime.now()`, atau jam komputer dalam keputusan trading.

## Definisi

- `bar.time` = **open time** bar (epoch detik, UTC), dari dataset.
- **CLOSED bar** pada evaluation time T = bar dengan
  `time + bar_seconds <= T`. Bar forming (yang masih terbentuk pada T)
  **tidak boleh dipakai** untuk keputusan (invariant #2).
- `evaluation_timestamp` dalam decision log = **epoch bar CLOSE M5 yang
  dievaluasi** (`bar.time + bar_seconds`), bukan epoch evaluasi komputer.
- `data_available_until` = T eksplisit (epoch bar close M5).

## Konsekuensi implementasi

1. **Evaluation-time slicing**: engine menerima `bars_until_T` — array yang
   SUDAH dipotong sehingga tidak ada bar dengan `time + bar_seconds > T`.
   Ini satu-satunya cara aman menghindari lookahead ala `findSwingPoints`.
2. `now()` DILARANG di seluruh `strategy_v2/gates.py`, `strategy_v2/zones.py`,
   `strategy_v2/replay.py` jalur decision (grep-auditable).
3. Replay yang sama dijalankan dua kali → decision log **identik bit-per-bit**
   untuk field deterministik (invariant #4).
4. `time.time()` hanya boleh dipakai di jalur non-decision (mis. stamping
   meta file output), dan tidak boleh masuk record decision.

## Bar seconds

| TF | bar_seconds |
|---|---|
| M5 | 300 |
| M15 | 900 |
