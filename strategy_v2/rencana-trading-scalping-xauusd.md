# Rencana Trading Scalping XAUUSD — Multi-Timeframe (Smart Money Concept / ICT)

> Disusun untuk trading manual dengan acuan pola candle, sekaligus sebagai blueprint logika untuk bot Python (non-AI, rule-based).

\---

## 0\. Filosofi Dasar

Struktur ini memakai pendekatan **top-down**: timeframe tinggi menentukan **bias/arah**, timeframe menengah menentukan **zona \& tipe setup**, timeframe rendah menentukan **timing entry**. Prinsipnya: *"HTF memberi peta, LTF memberi pemicu (trigger)."* Tidak ada entry yang diambil hanya dari satu timeframe — sinyal LTF hanya valid kalau searah/selaras dengan konteks HTF.

Tiga lapisan:

|Lapisan|Timeframe|Fungsi|
|-|-|-|
|**Bias**|1D, 4H|Direction, Liquidity mayor, Supply \& Demand mayor|
|**Setup**|4H, 1H, 15M|Trend, Breakout (BOS/CHoCH), Reversal, Order Block, FVG, Liquidity minor|
|**Entry**|5M, 1M|Confirmation micro-structure + pola candle + eksekusi|

\---

## 1\. Lapisan Bias — Timeframe 1D \& 4H

### 1.1 Direction (Arah)

Tentukan bias dengan membaca struktur swing pada 1D dan 4H:

* **Bullish bias**: rangkaian *Higher High (HH)* dan *Higher Low (HL)* yang konsisten.
* **Bearish bias**: rangkaian *Lower High (LH)* dan *Lower Low (LL)*.
* **Ranging/no bias**: swing tidak membentuk pola HH/HL maupun LH/LL yang jelas → kurangi ukuran posisi atau tunggu breakout struktur.

Cara deteksi programatis: gunakan **swing point / fractal detection** (bandingkan candle ke-*n* dengan *k* candle di kiri-kanan; titik itu swing high jika high-nya lebih tinggi dari semua tetangga dalam window, demikian sebaliknya untuk swing low). Susun urutan swing high/low kronologis → klasifikasikan HH/HL/LH/LL.

Tambahan filter arah yang gampang dikodekan: EMA 50 vs EMA 200 di 4H (bullish jika EMA50 > EMA200 dan price di atas EMA50; bearish jika sebaliknya). Ini dipakai sebagai *filter kedua*, bukan penentu utama — struktur swing tetap prioritas karena lebih dekat ke price action asli.

### 1.2 Liquidity (di 1D/4H)

Identifikasi kolam likuiditas mayor tempat stop-loss retail terkumpul:

* **Equal Highs (EQH)** / **Equal Lows (EQL)**: beberapa swing high/low yang levelnya hampir sama (toleransi ± beberapa pip atau ±0.1–0.2×ATR). Di sinilah *buy-side liquidity* (di atas EQH) dan *sell-side liquidity* (di bawah EQL) terkumpul.
* **Old High/Old Low** yang belum di-sweep (swing high/low signifikan yang belum pernah ditembus setelah terbentuk).
* **Trendline liquidity**: level yang menjadi tempat berkumpulnya stop di sepanjang garis tren.

Fungsi liquidity di sini adalah sebagai **target** (arah yang cenderung "ditarik" harga) dan sebagai **filter validitas zona**: zona demand/supply yang berdekatan dengan liquidity pool punya probabilitas reaksi lebih tinggi karena ada motif institusional untuk mengambil likuiditas dulu sebelum membalik/melanjutkan.

### 1.3 Supply \& Demand Zone (mayor)

* **Demand zone**: area konsolidasi/base sebelum pergerakan impulsif naik (biasanya ditandai 1–3 candle sebelum ledakan bullish).
* **Supply zone**: area base sebelum pergerakan impulsif turun.
* Prioritaskan **fresh zone** (belum pernah disentuh ulang) dibanding zona yang sudah "tested" berkali-kali (setiap sentuhan mengurangi kekuatan zona).
* Tandai juga posisi harga saat ini relatif terhadap range 1D/4H: **discount** (di bawah 50% range/equilibrium) untuk cari buy, **premium** (di atas 50%) untuk cari sell. Ini prinsip *premium/discount* ala ICT.

**Output lapisan ini**: bias arah (long/short/no-trade), 1–2 zona supply/demand mayor sebagai *Point of Interest (POI)*, dan target likuiditas terdekat searah bias.

\---

## 2\. Lapisan Setup — Timeframe 4H / 1H / 15M

Di lapisan ini, konteks HTF "diturunkan" ke struktur yang lebih presisi.

### 2.1 Trend

Konfirmasi ulang arah dari lapisan bias memakai struktur swing di 1H/15M. Jika trend 15M searah bias 1D/4H → mode **continuation**. Jika trend 15M berlawanan → berarti sedang retracement/counter-trend, potensi setup **reversal** setelah likuiditas diambil.

### 2.2 Breakout — BOS vs CHoCH

* **Break of Structure (BOS)**: harga menembus swing high (dalam uptrend) atau swing low (dalam downtrend) searah tren yang berlaku → konfirmasi tren **berlanjut**.
* **Change of Character (CHoCH)**: harga menembus swing point yang berlawanan arah dengan tren berlaku (misal dalam downtrend, menembus swing high terakhir) → sinyal awal potensi **pembalikan** struktur.
* Deteksi teknis: setelah swing high/low teridentifikasi, cek apakah candle *close* (atau *wick*, tergantung setting) melewati level swing tersebut. BOS = break searah struktur sebelumnya; CHoCH = break berlawanan arah struktur sebelumnya.

### 2.3 Reversal Setup

Kombinasi yang dicari: **liquidity sweep** (harga menembus EQH/EQL atau old high/low sebentar dengan wick lalu ditolak) + **CHoCH** segera setelahnya. Ini pola *Swing Failure Pattern (SFP)* / *stop hunt reversal* — salah satu setup dengan win-rate paling dicari di strategi SMC karena menangkap titik institusi "membalik" harga setelah menyapu stop.

### 2.4 Order Block (OB)

* **Bullish OB**: candle bearish (merah) terakhir sebelum muncul rangkaian candle bullish impulsif yang membentuk BOS naik.
* **Bearish OB**: candle bullish (hijau) terakhir sebelum rangkaian candle bearish impulsif yang membentuk BOS turun.
* Validitas OB meningkat jika: diikuti *displacement* kuat (candle impulsif dengan body besar/ATR tinggi), dan menyebabkan BOS/CHoCH struktural.
* **Refined OB**: gunakan hanya bagian tertentu dari range OB (misalnya 50%-nya, atau area *origin* dari FVG di dalam OB) sebagai zona entry presisi, bukan seluruh body candle.
* **Mitigasi**: OB dianggap "dipakai/mitigated" saat harga kembali menyentuhnya. OB yang belum pernah disentuh (*fresh/unmitigated*) lebih diutamakan.

### 2.5 Fair Value Gap (FVG) / Imbalance

* Pola 3 candle: FVG bullish terbentuk jika **high candle-1 < low candle-3** (gap di antaranya = zona FVG). FVG bearish jika **low candle-1 > high candle-3**.
* FVG merepresentasikan *inefisiensi harga* yang cenderung "ditarik ulang" (dikunjungi kembali) sebelum harga melanjutkan arah aslinya.
* Gabungkan OB + FVG yang overlap ("OB dengan FVG di dalamnya") sebagai POI dengan probabilitas lebih tinggi.

### 2.6 Liquidity (minor, di 1H/15M)

Sama seperti di 1.2 tapi skala lebih kecil — EQH/EQL jangka pendek yang relevan untuk timing beberapa jam ke depan. Berguna untuk menentukan target TP jangka pendek dan mengetahui area yang kemungkinan disapu sebelum reaksi di POI.

**Output lapisan ini**: satu POI presisi (OB dan/atau FVG yang overlap, idealnya searah bias HTF dan berada di zona discount/premium yang tepat), plus level liquidity minor terdekat sebagai calon *sweep point* sebelum reaksi.

\---

## 3\. Lapisan Entry — Timeframe 5M / 1M

Begitu harga bergerak mendekati/menyentuh POI dari lapisan setup, turun ke 5M/1M untuk *timing* presisi.

### 3.1 Confirmation (struktur mikro)

1. Tunggu harga masuk ke POI (OB/FVG) yang sudah ditandai.
2. Idealnya didahului **liquidity sweep mikro**: wick menembus sedikit level EQH/EQL/low-high terakhir di 5M/1M lalu ditolak — ini menunjukkan stop retail sudah "dimakan".
3. Setelah sweep, tunggu **CHoCH mikro** pada 1M/5M (struktur mikro berbalik searah rencana entry) sebagai konfirmasi bahwa tekanan sudah berbalik, bukan sekadar pantulan sesaat.

### 3.2 Pola Candle sebagai Trigger Entry

Karena kamu memakai pola candle sebagai acuan entry, berikut daftar pola yang paling relevan dipasangkan dengan POI, lengkap kriteria presisi (mudah dikodekan):

|Pola|Kriteria (long, mirror untuk short)|Kekuatan sinyal jika...|
|-|-|-|
|**Bullish Engulfing**|`close\[i] > open\[i]` dan `open\[i] <= close\[i-1]` dan `close\[i] >= open\[i-1]` (body candle sekarang membungkus body candle sebelumnya)|body candle-i jauh lebih besar dari body candle-(i-1), terjadi tepat di POI|
|**Pin Bar / Rejection**|`lower\_wick >= 2 × body` dan `close` berada di sepertiga atas range candle|wick menembus level liquidity/OB lalu ditutup kembali di atas zona|
|**Hammer di zona demand**|body kecil di atas, lower wick panjang (≥2× body), terjadi setelah leg turun|muncul persis di OB/FVG bullish|
|**Morning Star (simplified 3-candle)**|candle-1 bearish besar → candle-2 body kecil (indecision) → candle-3 bullish menutup di atas midpoint candle-1|di ujung leg turun + sudah sweep liquidity|
|**Inside Bar + Breakout**|candle-2 sepenuhnya di dalam range candle-1 (`high\[2]<high\[1]` \& `low\[2]>low\[1]`), entry saat breakout dari range inside bar searah bias|dipakai untuk continuation setelah retrace kecil ke OB|
|**Liquidity Sweep + Rejection (SFP)**|wick menembus swing low/EQL lalu `close` kembali di atas level tsb dalam candle yang sama atau 1–2 candle berikutnya|paling kuat kalau bertepatan dengan CHoCH mikro|

Untuk short, gunakan pola mirror: Bearish Engulfing, Shooting Star, Evening Star, dst — logikanya simetris.

### 3.3 Dua Model Entry

**Model A micro — Continuation (trend-following):**
HTF bias searah → MTF trend \& BOS searah → harga retrace ke OB/FVG fresh di MTF → turun ke LTF, tunggu reaksi (pola candle) tanpa perlu CHoCH besar, cukup micro-confirmation → entry searah tren.

**Model B scalp — Reversal (liquidity sweep):**
HTF/MTF menunjukkan harga mendekati liquidity pool (EQH/EQL/old high-low) yang berlawanan dengan bias HTF namun searah dengan arah pembalikan yang diharapkan → tunggu sweep di LTF → CHoCH mikro → pola candle rejection → entry berlawanan arah pergerakan sesaat (melawan sweep, searah bias HTF awal).

> Aturan emas: entry \*\*hanya\*\* diambil kalau arah akhirnya tetap selaras dengan bias 1D/4H (kecuali strategi kamu sengaja didesain sebagai \*counter-trend scalp\* jangka sangat pendek — kalau begitu, perkecil ukuran posisi dan target).

\---

## 4\. Manajemen Exit

* **Stop Loss**: ditempatkan di luar POI (di bawah OB/FVG untuk long, di atas untuk short) + buffer sebesar spread atau 0.1–0.2× ATR(5M) agar tidak kena "noise wick". Untuk model reversal, SL diletakkan di luar titik ekstrem sweep (wick terjauh), bukan di level liquidity itu sendiri.
* **Take Profit bertingkat**:

  * **TP1** (partial close, misal 50%): di liquidity/level struktur terdekat searah trade (mis. EQH/EQL minor berikutnya) — umumnya 1R–1.5R.
  * Setelah TP1 tercapai → **pindahkan SL ke breakeven (BE)**.
  * **TP2** (sisa posisi): di target liquidity/OB berlawanan pada timeframe lebih tinggi (1H/4H), atau pakai trailing.
* **Trailing**: dua opsi mudah dikodekan —

  1. *Structure trailing*: geser SL ke swing low/high (LTF) terbaru setiap kali terbentuk swing baru searah posisi.
  2. *ATR trailing*: SL = harga saat ini ∓ (k × ATR(14) di 5M), k biasanya 1.5–2.5.
* **Time-based exit** (opsional untuk scalping murni): tutup posisi jika target belum tercapai dalam N candle (misal 15–20 candle di 5M) untuk menghindari posisi "nyangkut" di market yang mendatar.

\---

## 5\. Manajemen Risiko

|Parameter|Rekomendasi awal (sesuaikan via backtest)|
|-|-|
|Minimum Risk:Reward|≥ 1:1.3 (setelah spread/komisi)|
|Position sizing (lot) sementara gunakan yang sudah ada||

Position sizing (lot) dihitung otomatis: `risk\_amount = equity × risk\_percent`; `lot = risk\_amount / (SL\_distance\_in\_price × contract\_size\_per\_lot × pip\_value)`. Untuk XAUUSD, 1 lot standar biasanya = 100 oz, jadi pergerakan $1 = $100/lot — sesuaikan dengan spesifikasi broker (kontrak mini/mikro berbeda).

\---

## 6\. Filter Tambahan

* **Sesi trading**: XAUUSD paling likuid \& volatil saat overlap sesi **London–New York** (sekitar 19:00–23:00 WIB, cek ulang sesuai broker time). akukan adaptasi di  sesi Asia (volatilitas rendah, spread relatif lebih lebar terhadap pergerakan) kecuali strategi kita sesuaikan untuk range-scalping,atau gunakan strategi sama untuk ujicoba.
* **Filter volatilitas/spread**: skip entry jika spread saat itu > threshold (misal >35 pips point broker) atau ATR(5M) di luar rentang normal (terlalu rendah = pasar sepi/tidak layak scalping, terlalu ekstrem = risiko slippage tinggi saat berita).
* **Filter korelasi**: cek DXY (indeks dolar) — pergerakan XAUUSD sering berkorelasi negatif dengan DXY; divergensi signifikan bisa jadi filter tambahan (opsional, lebih lanjut).

\---

## 7\. Checklist Confluence (Scoring) — Basis Logika Bot

Gunakan sistem skor sederhana; makin tinggi skor, makin kuat sinyal, dan bisa langsung dipetakan ke variabel boolean di kode:

|#|Kondisi|Bobot|
|-|-|-|
|1|Bias 1D \& 4H searah (HH/HL atau LH/LL konsisten)|2|
|2|Harga berada di zona discount (long) / premium (short) terhadap range 4H|1|
|3|POI (OB/FVG) di 4H/1H/15M fresh \& searah bias|2|
|4|BOS searah bias terjadi di 1H/15M sebelum retrace ke POI|1|
|5|Liquidity sweep (EQH/EQL atau old high/low) tepat sebelum reaksi|2|
|6|CHoCH mikro di 5M/1M setelah sweep|2|
|7|Pola candle valid (lihat tabel 3.2) menutup di dalam/di atas POI|2|
|8|Tidak dalam window berita high-impact \& spread normal|wajib (gate, bukan skor)|
|9|R:R terhitung ≥ minimum yang ditentukan|wajib (gate)|

Total skor maksimum non-gate: 12. Tentukan threshold entry (misal ≥ 8/12) lewat backtest — ini jadi parameter yang bisa dioptimasi.

\---

## 8\. Arsitektur Bot Python (Rule-Based, Non-AI)

### 8.1 Alur Modul

```
\[Data Feed] → \[Multi-TF Structure Engine] → \[Zone/POI Detector] 
   → \[Liquidity Engine] → \[Confluence Scorer] → \[LTF Trigger Engine 
   (candle pattern + micro CHoCH)] → \[Risk/Position Sizing] 
   → \[Order Execution] → \[Trade Manager (SL/TP/BE/Trailing)] 
   → \[Logger/Journal]
```

### 8.2 Struktur Modul (disarankan sebagai package)

```
xauusd\_bot/
├── data/
│   └── feed.py            # ambil OHLC multi-timeframe
├── structure/
│   ├── swings.py          # deteksi swing high/low
│   ├── bos\_choch.py       # BOS / CHoCH
│   └── trend.py           # klasifikasi HH/HL vs LH/LL, EMA filter
├── zones/
│   ├── order\_block.py     # deteksi OB + mitigasi
│   ├── fvg.py              # deteksi FVG + mitigasi
│   └── supply\_demand.py   # zona S\&D mayor (1D/4H)
├── liquidity/
│   └── liquidity.py       # EQH/EQL, sweep detection
├── patterns/
│   └── candlestick.py     # semua pola candle (tabel 3.2)
├── signal/
│   ├── scorer.py           # confluence scoring (bagian 7)
│   └── entry\_engine.py     # gabungkan bias+setup+entry jadi 1 sinyal
├── risk/
│   └── position\_sizing.py
├── execution/
│   ├── broker\_api.py       # wrapper MT5 / broker lain
│   └── trade\_manager.py    # SL/TP/BE/trailing/partial close
├── filters/
│   └── session\_news.py     # filter sesi \& kalender berita
├── backtest/
│   └── engine.py           # replay historis untuk validasi
└── main.py                 # loop utama / event handler on\_new\_bar
```

### 8.3 Pseudocode Inti (ringkas, bisa langsung jadi kerangka `.py`)

```python
# main.py (disederhanakan)
def on\_new\_bar(symbol="XAUUSD"):
    df\_1d  = get\_ohlc(symbol, "D1")
    df\_4h  = get\_ohlc(symbol, "H4")
    df\_1h  = get\_ohlc(symbol, "H1")
    df\_15m = get\_ohlc(symbol, "M15")
    df\_5m  = get\_ohlc(symbol, "M5")
    df\_1m  = get\_ohlc(symbol, "M1")

    # 1) Lapisan bias
    bias = get\_direction(df\_1d, df\_4h)          # "bullish" / "bearish" / "neutral"
    liquidity\_htf = detect\_liquidity(df\_1d, df\_4h)
    zones\_htf = detect\_supply\_demand(df\_4h)

    if bias == "neutral":
        return  # no trade

    # 2) Lapisan setup
    trend\_mtf = get\_trend(df\_1h, df\_15m)
    structure\_break = detect\_bos\_choch(df\_1h, df\_15m)
    ob\_list = detect\_order\_blocks(df\_4h, df\_1h, df\_15m)
    fvg\_list = detect\_fvg(df\_4h, df\_1h, df\_15m)
    liquidity\_mtf = detect\_liquidity(df\_1h, df\_15m)

    poi = select\_best\_poi(ob\_list, fvg\_list, zones\_htf, bias)
    if poi is None or price\_not\_near(poi, df\_15m):
        return

    # 3) Lapisan entry
    swept = detect\_liquidity\_sweep(df\_5m, df\_1m, poi)
    choch\_micro = detect\_choch(df\_5m, df\_1m)
    pattern = detect\_candle\_pattern(df\_1m, bias)

    score = compute\_confluence\_score(
        bias, trend\_mtf, structure\_break, poi, swept, choch\_micro, pattern
    )

    if not passes\_gates(session\_ok(), news\_filter\_ok(), spread\_ok()):
        return

    if score >= THRESHOLD and pattern is not None:
        entry\_price = df\_1m.close.iloc\[-1]
        sl = calc\_stop\_loss(poi, swept, df\_5m)
        tp1, tp2 = calc\_take\_profits(liquidity\_mtf, liquidity\_htf, entry\_price, sl)
        lot = calc\_position\_size(equity, risk\_percent, entry\_price, sl)

        if risk\_reward(entry\_price, sl, tp1) >= MIN\_RR:
            place\_order(symbol, direction=bias, entry=entry\_price,
                        sl=sl, tp1=tp1, tp2=tp2, lot=lot)
            log\_signal(...)  # simpan semua variabel di atas untuk audit/backtest
```

Contoh fungsi deteksi FVG (murni pandas, tanpa library eksternal, sebagai contoh gaya kode yang bisa kamu perluas):

```python
def detect\_fvg(df):
    fvgs = \[]
    for i in range(2, len(df)):
        c1, c3 = df.iloc\[i-2], df.iloc\[i]
        if c1\["high"] < c3\["low"]:
            fvgs.append({"type": "bullish", "top": c3\["low"], "bottom": c1\["high"], "index": i})
        elif c1\["low"] > c3\["high"]:
            fvgs.append({"type": "bearish", "top": c1\["low"], "bottom": c3\["high"], "index": i})
    return fvgs
```

Contoh fungsi pola Bullish Engulfing:

```python
def is\_bullish\_engulfing(df, i):
    prev, cur = df.iloc\[i-1], df.iloc\[i]
    body\_prev = abs(prev\["close"] - prev\["open"])
    body\_cur  = abs(cur\["close"] - cur\["open"])
    return (
        cur\["close"] > cur\["open"] and
        prev\["close"] < prev\["open"] and
        cur\["open"] <= prev\["close"] and
        cur\["close"] >= prev\["open"] and
        body\_cur > body\_prev
    )
```

### 8.4 Catatan Desain Penting untuk Bot

* **Statefulness**: OB/FVG/liquidity yang sudah dideteksi harus disimpan sebagai state (list of dict dengan status `fresh`/`mitigated`) antar candle, bukan dihitung ulang dari nol tiap tick — supaya bot tahu mana zona yang "belum dipakai".
* **Event-driven per timeframe**: jalankan re-evaluasi lapisan bias hanya saat candle 4H baru terbentuk (hemat komputasi), lapisan setup saat candle 15M baru, dan lapisan entry setiap candle 1M/5M baru atau bahkan per tick untuk presisi entry.
* **Backtest dulu sebelum live**: pisahkan `entry\_engine` dari `broker\_api` sehingga logika sinyal bisa dites di *replay engine* historis tanpa menyentuh eksekusi order — sangat penting sebelum menjalankan versi live.
* **Logging lengkap**: simpan setiap variabel yang dipakai untuk mengambil keputusan (skor, semua kondisi checklist, harga, waktu) per sinyal — ini bahan evaluasi \& tuning threshold nanti.

\---

## 9\. Tools \& Library Referensi (Python)

|Kebutuhan|Rekomendasi|Catatan|
|-|-|-|
|Data \& eksekusi order|`MetaTrader5` (package resmi Python untuk MT5)|Paling praktis kalau broker kamu MT5; fungsi seperti `mt5.copy\_rates\_from()` untuk data, `mt5.order\_send()` untuk eksekusi|
|Deteksi konsep SMC/ICT siap pakai|`smartmoneyconcepts` (`pip install smartmoneyconcepts`)|Library open-source yang menyediakan fungsi untuk Order Block, Liquidity, Fair Value Gap, Swing High/Low, BOS, dan CHoCH, bekerja di atas DataFrame OHLC pandas (`smc.ob()`, `smc.fvg()`, `smc.liquidity()`, `smc.bos\_choch()`, dst). Bisa dipakai langsung atau sebagai pembanding untuk implementasi custom kamu sendiri. Proyeknya menyebut dirinya untuk tujuan edukasi, bukan pengambil keputusan tunggal — tetap kombinasikan dengan validasi manual/backtest|
|Indikator teknikal umum (EMA, ATR, RSI, dll)|`pandas-ta-classic`|Fork komunitas yang aktif dipelihara; `pandas-ta` versi asli berisiko diarsipkan karena kurang maintainer, jadi lebih aman pakai fork ini atau `TA-Lib` langsung|
|Deteksi swing/fractal|`scipy.signal.argrelextrema` atau fungsi custom|Cukup ringan, tidak perlu library besar|
|Backtesting|`backtrader`, `vectorbt`, atau `Backtesting.py`|`vectorbt` lebih cepat untuk uji parameter besar-besaran (grid search threshold skor, dsb)|
|Kalender ekonomi (filter berita)|API kalender ekonomi (mis. ForexFactory scraping tidak resmi, atau provider berbayar seperti Finnhub/Trading Economics)|Perlu dicek ulang ketentuan penggunaan masing-masing sumber|
|Notifikasi/monitoring|`python-telegram-bot` untuk kirim alert sinyal \& status bot ke Telegram|Berguna untuk memantau bot tanpa perlu selalu buka terminal|
|Penyimpanan log/jurnal|`SQLite` (via `sqlite3`) atau file CSV terstruktur|Cukup untuk skala bot personal, mudah dianalisis dengan pandas|

\---

## 10\. Saran Pengembangan Selanjutnya

1. **Backtest berlapis**: uji tiap lapisan secara terpisah dulu (apakah deteksi OB/FVG/liquidity sudah akurat secara visual di chart) sebelum menguji keseluruhan sistem skor.
2. **Optimasi threshold skor** (bagian 7) dengan walk-forward testing, bukan sekadar optimasi di satu periode data (rawan overfitting).
3. **Paper/demo trading** di kondisi live market sebelum real fund, karena scalping sangat sensitif terhadap spread, slippage, dan latency eksekusi riil yang sulit disimulasikan sempurna di backtest.
4. **Pisahkan parameter per sesi**: perilaku XAUUSD di sesi London berbeda dengan NY overlap,asia — pertimbangkan threshold/parameter berbeda per sesi kalau backtest menunjukkan itu signifikan.
5. **Dokumentasikan setiap iterasi rule** (versi strategi, tanggal perubahan, hasil backtest terkait) supaya kamu punya jejak audit saat mengevaluasi performa dari waktu ke waktu.

\---

*Catatan: dokumen ini adalah kerangka metodologi \& referensi edukasi untuk pengembangan sistem trading/bot, bukan saran keuangan. Kinerja masa lalu suatu strategi (termasuk hasil backtest) tidak menjamin hasil di masa depan — XAUUSD tergolong instrumen dengan volatilitas tinggi, dan scalping menambah eksposur terhadap risiko spread/slippage/eksekusi.*

