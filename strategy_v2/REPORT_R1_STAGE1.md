# REPORT R1 Stage 1 — Kalibrasi & Seleksi 4 Arm Paralel

Tanggal: 2026-09-09 · Kontrak: `docs/PAKET_HIPOTESIS_R1.md` §3 · Driver:
`scripts/r1_stage1_arms.py` · Artefak: `data/research/r1/stage1_arms.json`
(results_hash `b331815818de45cb…`)

> **VERDICT SELEKSI: KILL_ALL — tidak ada arm yang lolos kriteria Stage 1.**
> Sesuai kontrak §3: "Semua arm gagal → KILL semua, kembali ke owner dengan
> dekomposisi lengkap." Laporan ini adalah dekomposisi tersebut. TIDAK ada
> tweak, TIDAK ada iterasi tambahan — budget revisi R1 sesuai kontrak, dan
> keputusan lanjut sepenuhnya milik owner.

## 1. Kondisi eksekusi

| Item | Nilai |
|---|---|
| Training window | dataset P3 terkunci, hash `86014edf…` |
| Dataset M1 (S0.1) | 150.000 bar, hash `bf92b34e…`, verdict `LAYAK_DENGAN_DEVIASI_TERDOKUMENTASI` (5 gap 120s) — deviasi dikonfirmasi owner ("lanjut stage 1", 2026-09-09) |
| Champion parity | 199 sinyal = P4 iter-3 ✅ (identitas eksperimen utuh) |
| Cost model | base 17 poin/$1-per-poin; sel wajib ×1.5 + slip2 + delay0 |
| Eksekusi | M5 grid (A) & M1 first-available (B/C/D, `run_execution_m1`) |
| Real order | OFF arsitektural (replay saja) |

## 2. Hasil per arm (kriteria lolos: expNet_base > 0 ∧ expNet_must > 0 ∧ n ≥ 30)

| Arm | Hipotesis | Sinyal | Base n / expNet | Must n / expNet | Verdict |
|---|---|---|---|---|---|
| A — B4 0.75×ATR | `H-LOC-03` | 110 | 81 / **+1.2621** | 82 / **−0.3325** | ❌ (must gagal) |
| B — eksekusi M1 | `H-EXEC-M1-01` | 199 | 140 / **+0.3454** | 142 / **−1.0096** | ❌ |
| B' — champion M5 (baseline tangga) | `H-SCORE-01` | 199 | 136 / +0.6940 | 138 / −0.6844 | ❌ (referensi) |
| C — sweep T* rule C1 | `H-VOL-02` | 199 | 12 titik grid | tidak ada T lolos | ❌ `NO_VIABLE_THRESHOLD` |
| D — inside-bar pending STOP | `H-IBREAK-01` | 99 | 79 / **−4.6524** | 79 / −5.9665 | ❌ |

Kesimpulan aturan seleksi: **KILL_ALL, winners = []**.

## 3. Dekomposisi — kenapa semuanya gugur

1. **Akar yang sama dengan P5/P6, kini terukur lebih tajam**: edge kotor positif
   di sel base (A +1.26, champion +0.69) **tidak bertahan** terhadap sel wajib
   ×1.5+slip2. Selisih base→must ≈ −1.6 s/d −1.9 $/trade — persis biaya tambahan
   (spread +8.5 poin ≈ $8.5/lot/round-trip ≈ −0.9…−1.2 $/trade pada lot ±0.01-0.02,
   plus slippage 2 poin). Edge per trade champion (~+0.69) < penambahan biaya.
2. **Arm A (B4 0.75)**: base justru membaik (+0.69 → +1.26) — diagnostik bucket
   benar, zona emas nyata — tapi tetap kalah biaya di sel wajib (−0.33).
   Artinya: **filter lokasi bukan masalahnya; biaya adalah masalahnya.**
3. **Arm B (M1)**: base menurun vs champion M5 (+0.35 vs +0.69). Hapus delay
   5 menit TIDAK menambah edge pada training window ini — karena pada data
   training, entry M5 next-open sebenarnya *lebih untung* (delay justru pernah
   menyelamatkan dari entry cepat yang mundur). Temuan ini melawan ekspektasi
   kontrak (§2 "delay fatal") — ekspektasi itu berasal dari P5; pada champion
   iter-3 di training, delay bukan sumber kerugian utama.
4. **Arm C (volume)**: `NO_VIABLE_THRESHOLD` — tidak ada satu pun T pada grid
   12 titik yang memenuhi rule C1 di kedua sel biaya. Kurva tidak monoton
   (expNet naik-turun antar desil) — volume confirmation TIDAK informatif
   sebagai pemilih threshold di data ini (jawaban dua-arah K4: sisi
   "volume tidak informatif" yang menang, dengan bukti grid penuh).
5. **Arm D (inside-bar)**: negatif sejak base (−4.65). Breakout pending STOP
   pada training window ini menghasilkan set trade yang jauh lebih buruk —
   fill breakout saat momentum sudah habis (reverse at breakout). Sel slippage
   wajib {2,5} memperburuk (must −5.97). Pending mechanics bekerja benar
   (placed/triggered/expiry tercatat — stats di artefak), edge-nya yang tidak ada.

## 4. Catatan integritas proses

- Satu perubahan per arm dijalankan persis; tanpa sweep di luar yang dikontrak
  (Arm C sweep = yang dikontrak §3; Arm D slippage {2,5} = yang dikontrak §2).
- Parity champion 199 dicek FATAL dulu sebelum arm lain jalan.
- Determinisme: driver deterministik penuh (input sama → artefak sama);
  results_hash `b331815818de45cb…` mengunci hasil.
- Full suite: **874 passed, 0 fail** (perubahan kode Stage 0/1: bugfix unpack
  `b5_inside_bar_signal` di gates.py — caller kini kompatibel kontrak 2/3-tuple;
  passthrough `b5_mode`/`inside_bar_*` di replay.py — default tidak mengubah
  perilaku champion; parity 199 tetap).

## 5. Serah terima owner (opsi berikutnya — bukan keputusan engineer)

Pola dari C1→C4, P4→P6, dan kini R1 Stage 1 konsisten: **edge kotor tipis
(+0.3…+1.3) melawan biaya struktural XAUUSD demo (round-trip ±$35/lot)**.
Opsi yang tersisa (semua = paket baru, hipotesis terdaftar, budget revisi baru):

1. **Paket biaya** (paling didukung bukti): TP lebih lebar / frekuensi lebih
   rendah / SL tidak ter-couple spread (`spread_mult` dipisah dari stop sizing),
   atau instrumen/broker dengan spread rendah relatif volatilitas.
2. **Fase 2 SCALP sniper lebih awal**: ekonomi strukturalnya memang dirancang
   untuk menanggung biaya (TP lebar, holding panjang, overlap London-NY).
3. **Hentikan jalur V2 live** dan pertahankan sebagai riset (status quo P6).

Rekomendasi teknis engineer: kombinasi (1)+(2). Arm A terbukti mengarah benar
(zona emas nyata) — hipotesisnya layak diwariskan ke paket biaya (parent
H-LOC-03), bukan dibuang.

## 6. Dekomposisi lengkap (kontrak §3 — artefak `stage1_decomp.json`, hash `24c0d47e9b2e040f…`)

Diagnostik training-only (OOS TETAP disegel). Ini bahan keputusan owner:

**D1 — Sesi × arah (champion, n=136):** SELURUH edge hidup di `ny_late|BUY`
(n=48, expNet **+9.30**) dan `asia|BUY` (n=14, +1.18). Semua sel lain negatif:
london BUY −8.83, london SELL −6.26, ny_late SELL −4.70, asia SELL −2.70.
Pola sama persis di Arm A. → Bukti kuat untuk `H-SESSION-02` (K9: parameter
per blok jam) dan/atau long-only ketat.

**D2 — Break-even spread (slip2, grid turun dari 25.5):** champion positif kembali
pada spread ≤ 20 poin (+0.09 di 20; −0.42 di 22); Arm A sama (breakeven ≈ 20-21).
→ Sel wajib gagal karena 5.5-8.5 poin biaya, bukan karena sinyal; opsi negosiasi
broker/instrumen secara numerik menyelamatkan champion & Arm A tanpa mengubah
strategi sedikit pun.

**D3 — Zona emas Arm A per band jarak B4 (base):** 0-0.25 ATR = **+2.17** (n=40),
0.25-0.5 = +0.67 (n=22), 0.5-0.75 = +0.02 (n=19). Monoton menurun — klaim inti
H-LOC-03 terkonfirmasi; nilai hipotesis ini ada di band TERDEKAT.

**D4 — Porsi biaya dari gross:** champion 65.9%, Arm A 52.0% — biaya memakan
separuh hingga dua-tiga gross. Konsisten dengan pola keseluruhan: sinyal ada,
biaya yang membunuh.

— Buffy, 2026-09-09
