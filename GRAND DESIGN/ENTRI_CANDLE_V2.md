# DESAIN V2 — Entri Berbasis Candle + SL/TP Manual per Style (Micro & Scalp)

Status: rancangan (belum implementasi). Dokumen ini MENYESUAIKAN dua rencana
sebelumnya (INTEGRASI_TAB_ANALISA_V1.md dan LEARNING_MEMORI_V1.md) ke paradigma
candle-first sesuai masukan user.

## 1. Prinsip inti (hasil diskusi)

1. **Arah tetap dari analisa tab** (master signal + taScore) — ini jawaban "ke mana".
2. **Candle adalah pemicu entri** — jawaban "SEKARANG atau TUNGGU": bot hanya
   menarik pelatuk saat kondisi candle M1/M5/M15 mendukung (momentum searah /
   pembalikan terkonfirmasi), bukan saat mayoritas sinyal sudah BUY/SELL.
3. **SL/TP bukan lagi kaku**: user mengatur sendiri dalam POIN per style
   (micro & scalp), disimpan sebagai default entri. Engine memakai angka itu.
4. **R:R turun menjadi informasi, bukan gerbang** — karena TP/SL sudah bisa
   di-adjust, bot tidak perlu menolak entri karena R:R rendah; cukup
   menampilkan peringatan lunak. (Gerbang R:R utk micro & scalp dihapus.)

## 2. Alur keputusan V3 (micro & scalp)

```
analyzeMarket (tab) ─► master + per-TF (13 indikator + pola + volume)
        │
        ▼
1. GATE ARAH   : taScore = master(±2) + M5(±1) + M15(±1) + M1(+1 bonus)
                 BUY ≥ +3 · SELL ≤ −3 · selain itu WAIT "TA belum searah"
        │
        ▼
2. GATE CANDLE (utama — lihat §3) : setup = READY / WAITING / BLOCKED
                 BLOCKED → WAIT "candle keras melawan"
                 WAITING → WAIT "menunggu pembalikan …" (polling 1 dtk)
                 READY   → lanjut
        │
        ▼
3. GATE MEMORI : bucket kondisi serupa; n≥8 & WR<45% → WAIT (soft)
        │
        ▼
4. R:R         : DILAPORKAN, tidak memblokir. Peringatan lunak bila
                 SL > 2×ATR (terlalu lebar) atau TP < SL×0.5 (target kecil)
        │
        ▼
5. EKSEKUSI    : SL/TP = override user (data/bot_config.json → sl_tp)
                 kalau belum di-set → pakai default formula engine
                 lot = risk% dari SL user (aman otomatis)
```

Urutan gate sama untuk micro dan scalp; perbedaan hanya default SL/TP + ATR.

## 3. GATE CANDLE — rubrik kualitas entri (menggantikan gate sederhana kemarin)

Candle dibaca di M1, M5, M15 dari 6 candle terakhir + pola terdeteksi:

### a. Sinyal TIMING (pendukung arah)
- streak searah / lawan arah (M1 & M5, maks 3 bar)
- body candle terakhir vs range (besar/kecil) dan vs ATR
- posisi harga: dekat EMA21 M5 (pullback) vs jauh (ekstensi)
- posisi di range 20-candle M5 (atas/bawah) & dekat zona SR swing

### b. Sinyal PEMBALIKAN (membatalkan "tunggu")
- reversal candle muncul: doji/hammer/pin/engulfing/piercing searah
- candle M1 terakhir sudah berbalik searah
- M5 menutup di atas/bawah high/low 3 candle sebelumnya (struktur pecah)

### c. Klasifikasi setup (keluar dari engine)
| Setup    | Arti                                   | Aksi |
|----------|----------------------------------------|------|
| READY    | arah TA + momentum candle searah       | entry diizinkan |
| WAITING  | arah TA benar tapi candle masih lawan  | tunggu pembalikan |
| BLOCKED  | arah TA vs candle keras (mis. gap, candle lawan body >80%, M1 4+ streak) | tunggu, alasan jelas |

- Skor kualitas 0–10 ikut dicatat (skor = bobot sinyal timing + pembalikan).
- Alasan WAIT kini berbunyi, mis.:
  `candle: WAITING — M1 3× bear, tunggu pembalikan bullish (READY saat M1 close > EMA9 M1)`
  `candle: READY skor 7 — pullback ke EMA21 M5 + engulfing bullish`
- Ambang skor & aturan transisi dibuat konstanta di config agar bisa disetel
  tanpa ubah kode (Fase 2).

### d. Pencatatan ke memori
Fingerprint entri bertambah: `candle_setup` (READY/WAITING), `candle_score`,
`candle_detail` (streak/posisi/pola). Bucket tetap kasar; setup jadi dimensi
opsional yang bisa diaktifkan setelah sampel cukup.

## 4. SL/TP MANUAL PER STYLE (menu & penyimpanan)

### 4.1 Penyimpanan — data/bot_config.json
```jsonc
{
  "sl_tp": {
    "micro": { "sl_points": 0, "tp_points": 0, "source": "auto",
               "updated_at": null, "note": "" },
    "scalp": { "sl_points": 0, "tp_points": 0, "source": "auto",
               "updated_at": null, "note": "" }
  }
}
```
- nilai 0 = AUTO → engine memakai formula sekarang
  (micro: SL 1×ATR M5 · TP tetap 150; scalp: SL 1×ATR M5 · TP adaptif max(150,2×ATR)).
- nilai >0 = MANUAL → engine memakai persis angka user utk entri berikutnya.
- Dibaca engine tiap request (cache pendek) — berlaku tanpa restart bot.
- Route: POST /api/are/bot/config menerima patch `sl_tp`; GET mengembalikan.

### 4.2 Menu di tab OVERVIEW — "ATUR SL/TP ENTRY (poin)"
Layout per style (dengan penjelasan satu kalimat + tombol SAVE):

```
MICRO — SL default 1×ATR M5, TP cepat 150 poin.
  SL [ 350 ] poin   ·  TP [ 150 ] poin   [ SAVE TP SL ]   (auto)

SCALPING — TP adaptif mengikuti 2×ATR M5 (min 150); SL 1×ATR M5.
  SL [ 300 ] poin   ·  TP [ 500 ] poin   [ SAVE TP SL ]   (manual · 12:01)
```
- Label kecil `(auto)` / `(manual · jam)` menunjukkan sumber nilai aktif.
- Input kosong di salah satu sisi = sisi itu tetap (tidak diubah).
- Isi 0 di kedua sisi + SAVE = kembali ke AUTO (reset).
- Penjelasan singkat di bawah panel:
  "1 poin = 0.01 harga (XAUUSD). Nilai dipakai utk ENTRI berikutnya;
   posisi yang sudah terbuka diatur lewat kolom SET SL/TP di tabel OPEN
   POSITIONS. SL/TP tidak lagi ditolak karena R:R — cukup peringatan."
- Panel CHAMPION menampilkan nilai efektif: `SL 350 · TP 150 (manual)`
  atau `(auto)` agar tahu sumbernya.

### 4.3 Kolom per posisi terbuka (sudah ada)
Tetap: ubah SL/TP posisi berjalan langsung ke MT5 (poin dari entry).

## 5. R:R jadi INFORMASI (bukan gerbang)

- Untuk micro & scalp: ambang minRR tidak lagi memblokir.
- Engine tetap menghitung & menampilkan `rr` dan memperingatkan bila:
  - SL > 2×ATR → "SL lebar, risiko $X — yakin?"
  - TP < SL×0.5 → "target kecil vs SL — lihat ekspektasi"
  - Peringatan tampil di reason + panel, tanpa membatalkan entri.
- Lot sizing tetap dari risk% × balance ÷ SL user → risiko uang konsisten.
- (Day/swing/position di luar lingkup; masih pakai minRR 1.5 sementara.)

## 6. Penyesuaian rencana Learning Memory (V1 → V2)

- Rejection kategori baru sudah ada: `candle`, `memory`; kini `ta` WAIT
  tetap tercatat; `rr` hanya muncul bila peringatan aktif.
- Outcome per trade + fingerprint (incl. candle_setup, skor, SL/TP yg dipakai
  & sumber auto/manual) direkam → bot belajar per konfigurasi SL/TP user.
- Laporan rutin `report_memory.py`: top setup candle terbaik/terburuk per style.

## 7. File yang disentuh (perkiraan)
1. UI/src/lib/learning.ts — (tak berubah; bucket tetap).
2. UI/src/app/api/are/decision/route.ts — gate candle V2 (rubrik skor+setup),
   hapus blok minRR utk micro/scalp, baca sl_tp override, peringatan rr.
3. UI/src/app/api/are/bot/config/route.ts — terima/simpan sl_tp.
4. UI/src/app/page.tsx — panel ATUR SL/TP ENTRY + indikator sumber nilai.
5. UI/src/app/api/are/trade/modify/route.ts — sudah ada (posisi berjalan).
6. are/bot.py — tak berubah utk SL/TP (ambil dari engine); penyesuaian kecil
   fingerprint jika perlu.
7. tests — tambah kasus override SL/TP & peringatan rr.

## 8. KEPUTUSAN DESAIN (dikonfirmasi user)

1. **Lingkup**: micro & scalp DULU. Day/swing/position tidak berubah
   (tetap minRR 1.5 & gate MTF lama) — tidak tersentuh implementasi ini.
2. **Reset ke AUTO**: TOMBOL RESET terpisah per baris (di samping SAVE TP SL)
   → set sl_points/tp_points = 0, source = "auto". Tidak memakai "isi 0".
3. **R:R**: pemblokiran minRR DIHAPUS untuk micro & scalp — R:R hanya
   dilaporkan + peringatan lunak di reason/panel. Day/swing/position tetap.
4. Menu OVERVIEW mengikuti keputusan 1 & 2 (dua baris: MICRO, SCALPING;
   tiap baris: penjelasan, input SL, input TP, [SAVE TP SL], [RESET]).
