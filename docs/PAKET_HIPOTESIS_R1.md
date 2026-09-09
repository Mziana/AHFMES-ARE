# PAKET HIPOTESIS REVISI R1 — KONTRAK TERSETUJUI OWNER

> Status: **DISETUJUI** (2026-09-09) — dokumen ini adalah kontrak eksekusi R1.
> Dasar: verdict Track A **KILL_REVISE** (artefak hash `b8a4b682…`) → revisi HANYA lewat
> hipotesis terdaftar (kontrak WAJIB #4, genealogy di `strategy_v2/genealogy.py`).
> Fondasi konseptual: dokumen penelitian owner *"Arsitektur Konfluensi Teknikal untuk
> Bot Scalping XAU/USD"* (Varian 1 = SCALP, Varian 2 = MICRO) — terverifikasi cocok
> dengan implementasi (laporan pemetaan, 2026-09-09).

---

## 0. Keputusan owner yang terkunci (dasar paket ini)

| # | Keputusan | Konsekuensi teknis |
|---|---|---|
| K1 | Gerbang lokasi B4 dilonggarkan ke **0,75×ATR** (bukan 1,0) | Arm A |
| K2 | **Eksekusi M1** untuk micro; M15 tren, M5 sinyal | Arm B |
| K3 | Filter berita tetap **OFF untuk micro**; ON untuk SCALP Fase 2 | kontrak profil |
| K4 | Volume **layak diuji** — sebagai komponen skor (veto biner tetap off) | Arm C |
| K5 | Uji **paralel** entri yang berbeda sifat — "tinggal mana yang lebih baik" | struktur 4 arm |
| K6 | Pola candle ketat yang sudah terpasang (hammer/engulfing/star/soldiers) **dipertahankan** | tanpa perubahan B5 |
| K7 | SCALP = **sniper 4-lapis** (D1/H1 → M15 → M5 → M1 eksekusi) — Fase 2 terpisah | §5 |
| K8 | Inside-Bar breakout (entry pending) ikut diuji **bersamaan** | Arm D |
| K9 | Sesi jelek → **parameter berubah per blok jam**, bukan mati-total | antrean H-SESSION-02 (§6) |

---

## 1. Prinsip yang mengikat (sama dengan siklus sebelumnya)

1. **Kalibrasi hanya di training window** (29 Jul – 8 Sep, hash `86014edf…`); data
   backward OOS (23 Apr – 28 Jul, hash `da72f41e…`, 18.515 bar M5, fail-closed 0,
   disjoint dua lapis terbukti) **hanya disentuh sekali**, oleh pemenang.
2. **RUN ONCE** — verdict hanya 3 opsi: `GO_RESEARCH | INCONCLUSIVE | KILL_REVISE`.
   Tidak ada tweak di antaranya; hasil jelek = informasi.
3. **Satu klaim = satu artefak ber-hash + satu commit + satu push.** Full suite hijau
   tiap commit.
4. **Pembukuan trial**: paket ini menambah trial tercatat (4 arm + sweep threshold
   Arm C) — masuk registry untuk deflasi DSR berikutnya. Tidak ada trial tersembunyi.
5. **Real order tetap OFF arsitektural** — Track B (ShadowGateway, parity, state
   machine) sudah lulus; semua arm dijalankan di replay/shadow, bukan order nyata.
6. **Kejujuran data**: window backward OOS sudah pernah "dilihat" sekali (saat
   champion lama gugur di sana). Sah untuk *seleksi arm*, tapi vonis pamungkas R1
   tetap butuh data forward yang benar-benar segar.

---

## 2. Empat arm paralel (tangga kumulatif: A ⊂ B ⊂ {C, D})

Semua arm mewarisi inti champion beku (skor 0–100 + gerbang, T*=60,1 terverifikasi
dari artefak C1 — selection rule "terendah yang lolos"; bukti anti-cherry-picking:
T=66,1 lebih cantik tapi TIDAK diambil). Model biaya identik untuk semua arm:
spread 17 poin, pv $1/poin/lot; sel wajib ×1,5+slip2+delay0 dilaporkan.

| Arm | ID Hipotesis | Parent | Satu perubahan | Ekspektasi (berbasis bukti) |
|---|---|---|---|---|
| **A** | `H-LOC-03` | H-LOC-02, H-SCORE-01 | B4: 0,25 → **0,75×ATR** (dibekukan dari diagnostik bucket training: 0,25–0,75 = +2,09/+2,01 per trade; >0,75 = −2,90) | zona emas yang dulu dibuang kembali; **skala skor tak berubah** → T*=60,1 tetap sah |
| **B** | `H-EXEC-M1-01` | H-SCORE-01 | Eksekusi M5 → **M1** (sinyal tetap M5 closed, masuk di open M1 pertama ≥ T) | menyerang delay 5 menit yang terbukti fatal (P5: −2,89 s/d −5,56); **tidak menyembuhkan akar rezim** — perbaikan eksekusi, bukan edge |
| **C** | `H-VOL-02` | H-VOL-01 | **B + volume sebagai komponen skor** (definisi graded, bukan cliff-edge; veto biner tetap off) | menjawab K4 dengan bentuk yang benar; **skala skor berubah** → T\* Arm C **wajib kalibrasi ulang** (rule C1 dideklarasikan ulang persis: terendah T dengan expNet_base>0 ∧ expNet_must>0 ∧ trades≥30 pada grid tetap) |
| **D** | `H-IBREAK-01` | H-SCORE-01, Varian 1 dokumen owner | **B + keluarga Inside-Bar breakout**: order pending STOP di luar range inside bar (arah mengikuti bias B3), skor ≥ T\* dievaluasi saat pemasangan order | entri beda sifat sesuai K5/K8; usaha engineering terbesar (§4) |

Keputusan desain Arm D (dibekukan, disetujui owner):
- **Expiry**: order pending kedaluwarsa setelah `N = 12` bar M1 (≈ 12 menit) atau
  saat sinyal berlawanan baru muncul — tidak diutak-atik nanti.
- **Kejujuran fill**: replay tidak tahu jalur harga intrabar — fill diasumsikan di
  harga trigger + sel slippage. Sel slippage {2, 5} poin **wajib** dilaporkan
  untuk Arm D.
- **Lokasi**: inside bar harus terbentuk dekat EMA (≤ 0,75×ATR, sama dengan Arm A)
  atau zona S/R M15 — tidak ada breakout di "ruang kosong".

---

## 3. Protokol eksekusi (urutan tidak boleh dilompati)

```
STAGE 0 — Persiapan (engineering murni, tanpa keputusan strategi)
  S0.1 Dataset M1: tarik via bridge (copy_rates_from_pos), kualifikasi penuh
       gaya A2 (fail-closed 0, grid 60s, session break ≥60s terklasifikasi),
       hash terkunci. (M1 ≈ 92 ribu bar untuk window 64 hari.)
  S0.2 Replay: pisahkan trigger TF (M5) dari execution TF (M1) — tanpa
       lookahead: keputusan dari M5 CLOSED, entry di open M1 pertama >= T.
  S0.3 Gateway: dukungan order pending STOP (replay + ShadowGateway + state
       machine, transisi eksplisit, expiry tercatat).
  S0.4 Parity test semua arm vs run_execution_replay (toleransi
       max(1 point, tick_size snapshot)) — wajib MATCH sebelum lanjut.

STAGE 1 — Kalibrasi & seleksi (training window SAJA)
  Jalankan A, B, C, D paralel (model biaya identik).
  Laporan per arm: expNet base, expNet sel wajib, n trade, WR, PF, worst streak.
  Aturan seleksi (dideklarasikan SEKARANG, sebelum hasil dilihat):
    - Arm lolos ⇔ expNet_base > 0 ∧ expNet_must > 0 ∧ n >= 30.
    - Pemenang = expNet_must tertinggi di antara yang lolos.
    - Dua arm selisih <= 0,5 $/trade → keduanya lanjut (profil beda, bukan
      saingan satu slot — kesepakatan slot terpisah MICRO/SCALP).
    - Semua arm gagal → KILL semua, kembali ke owner dengan dekomposisi lengkap.
  Arm C: kalibrasi ulang T* dengan rule C1 persis (grid tetap, "terendah yang lolos").

STAGE 2 — RUN ONCE backward OOS (pemenang saja, parameter FROZEN)
  Dataset da72f41e (23 Apr – 28 Jul). Nol perubahan setelah hasil terlihat.
  Analisis wajib: expNet net, PSR, DSR (jumlah trial N tercatat penuh), CI95,
  worst periode, loss streak, bucket skor + monotonisitas, dekomposisi
  (arah, sesi koarse, volatilitas, rezim slope).

STAGE 3 — Verdict
  GO_RESEARCH → forward treadmill (live-shadow >= 1 minggu, viability latency
  P99 <= 5 s) → review owner.
  INCONCLUSIVE → diagnosis terjadwal, hipotesis berikutnya.
  KILL_REVISE → revisi terdaftar lagi (parent = hipotesis arm yang gugur).
```

---

## 4. Estimasi usaha engineering (jujur)

| Item | Isi | Estimasi |
|---|---|---|
| Arm A | config profil + test kontrak + rerun | 0,5 hari |
| Arm B | pipeline M1 + kualifikasi + replay dual-TF + parity + test | 1–2 hari |
| Arm C | komponen volume graded + sweep T* + test | 1 hari |
| Arm D | pending STOP di replay+gateway+state machine + expiry + test | 2–3 hari |
| Stage 1–2 | run + analisis + laporan ber-hash | 0,5–1 hari |
| **Total** | | **±5–8 hari kerja** |

Risiko engineering terbesar: semantik pending order (fill intrabar, expiry, cancel) —
dibuat identik di replay DAN ShadowGateway, diverifikasi parity.

---

## 5. Fase 2 — SCALP "sniper" (TERPISAH; tidak dieksekusi sebelum R1 selesai)

```
D1/H1   : konteks makro & arah mayor (lapis bias tertinggi)  <- BARU (bridge sudah dukung)
M15     : struktur + zona S/R (<= 0,5xATR, sudah ada)          <- sudah ada (profil scalp)
M5      : pemicu pola candle (kontrak ketat)                   <- sudah ada
M1      : eksekusi presisi                                     <- dari Arm B, dipakai ulang
B1 news : ON (+-30 menit berita besar)                         <- K3: berita untuk scalp saja
Sesi    : jam likuiditas (London-NY overlap) — dikalibrasi, bukan diasumsikan
```

Prinsip terkunci: SCALP **dikalibrasi dari datanya sendiri** — tidak pernah mewarisi
kalibrasi MICRO. Ekonomi strukturalnya: TP lebih lebar + holding lebih panjang →
biaya sebagai % dari target jauh lebih kecil → sniper mampu menanggung banyak lapis
konfirmasi, rifle tidak. Slot posisi terpisah per profil di bawah CapitalSafetyKernel
global — *strategy independence, capital dependence*.

---

## 6. Antrean setelah R1 (terdaftar, tidak dieksekusi sekarang)

| Hipotesis | Isi | Alasan ditunda |
|---|---|---|
| `H-SESSION-02` | Blok sesi koarse (Asia/London/NY-overlap/NY-late), parameter per blok dikalibrasi dari training | K9; jaga jumlah trial R1 tetap kecil |
| `H-B2-SESSION` (budget) | spread-guard per sesi jam malam (p95 = 33 poin vs titik mati empiris 21) | menyatu ke H-SESSION-02 |
| Inside-Bar di SCALP | breakout di zona S/R M15 | setelah SCALP Fase 2 berdiri |

---

## 7. Yang TIDAK kita lakukan (tetap)

Tidak ada LLM/AI di hot path; tidak ada filter DXY/SMT; tidak ada indikator di luar
paket ini; T*=60,1 tidak disentuh untuk arm yang skalanya tak berubah; tidak ada
perubahan pola reversal ketat (K6); tidak ada order real.

---

## 8. Checklist persetujuan owner (tercentang saat approval 2026-09-09)

1. ☑ Ambang Arm A dibekukan **0,75×ATR** tanpa sweep tambahan (anti data-mining).
2. ☑ Struktur tangga **A ⊂ B ⊂ {C, D}** dan aturan seleksi Stage 1 seperti §3.
3. ☑ Arm C menerima **kalibrasi ulang T\*** (konsekuensi perubahan skala skor).
4. ☑ Desain Arm D: expiry **12 bar M1**, sel slippage wajib {2,5}, lokasi <=0,75×ATR
   atau zona S/R.
5. ☑ Pemenang ganda (selisih <=0,5) boleh dua-duanya lanjut ke RUN ONCE.
6. ☑ Estimasi 5–8 hari kerja dan urutan Stage 0–3.
7. ☑ SCALP sniper (§5) menunggu R1 selesai — tidak paralel dengan R1.
