# Operational Readiness Notes — Wave E (2026-09-07)

Catatan berbasis bukti runtime (audit + implementasi Wave A–D). Tidak ada
patch besar di wave ini; setiap butir berisi rekomendasi tindak lanjut.

## E-1. `tests/test_bot_lifecycle.py` men-place order demo RIIL
- Bukti: sesi log `data/bot_logs/bot_day_2026-09-07T12-08-40.log` (dibuat oleh
  full-suite run pertama) membuka posisi nyata #423355892 di akun Finex demo;
  full-suite run berikutnya juga menghasilkan deal ARE-MICRO.
- Dampak: menjalankan test suite = men-trading-kan akun demo (tiap run pindah
  balance ±beberapa dolar).
- Rekomendasi: pindahkan ke marker `@pytest.mark.integration` (deselect
  default), atau beri flag env `ARE_LIVE_ITEST=1` sebagai gerbang eksplisit.
- Status: DILAPORKAN (belum dipatch — butuh keputusan terpisah).

## E-2. Stop bot di Windows = TerminateProcess, bukan graceful
- Bukti: semua sesi bot berakhir TANPA baris `STOPPED` di log; state ditulis
  ulang oleh `UI/src/app/api/are/bot/stop/route.ts` (komentar routenya sendiri:
  "On Windows, SIGTERM is immediate").
- Dampak: cleanup dalam bot (log final PnL, unlink pid) tidak pernah jalan
  saat dihentikan dari UI. Karena `save_state` atomik (.tmp+os.replace),
  risiko korupsi rendah — ini masalah observability, bukan integritas.
- Rekomendasi: stop route kirim sinyal yang ditangani bot (mis. tulis flag
  `stop_requested` di state file yang dipoll bot tiap 1 dtk).

## E-3. Dua interpreter Python + shim WindowsApps
- Bukti: bridge lama berjalan via pythoncore-3.14; python 3.11 (terminal
  default) tidak punya MetaTrader5/polars; `python` bare bisa resolve ke shim
  `WindowsApps\python.exe`.
- Dampak: kegagalan import tergantung interpreter yang memulai proses; shim
  pid ≠ pid interpreter asli (sudah diantisipasi bot: state.pid = os.getpid()).
- Rekomendasi: pin interpreter di launcher (`run_bridge.bat`, `ARELauncher.bat`)
  ke path python yang punya dependensi, atau buat venv proyek.

## E-4. Rotasi log belum ada untuk beberapa output
- Bukti: `data/logs/bridge_auth.log`, `data/logs/ui_dev_restart.log`,
  `tmp/ui_dev.out.log` (2.3 MB) tumbuh tanpa batas; `bot_logs/*.log` satu file
  per sesi (aman); `trade_history` bot dipangkas 100 entri (aman).
- Rekomendasi: rotasi sederhana per-hari atau size-cap pada log bridge/UI.

## E-5. Kill-switch CLI/UI kini terikat ke jalur bot (Wave B)
- `safety-kill`/`/api/are/system action=kill` menulis execution_state.json;
  bot membacanya tiap iterasi (cache 2 dtk) dan memveto entry baru.
- Sisa risiko: keputusan kill TIDAK otomatis menutup posisi terbuka (by design:
  close = risk-reducing dan tetap dijalankan). Jika ingin flat-total, gunakan
  bridge `/close_all` via UI (kini token-protected).

## E-6. Keputusan breaker harian masih per-sesi, bukan per-kalender
- `max_daily_loss` dihitung dari `starting_balance` sesi berjalan; tidak ada
  reset otomatis pergantian hari (bot yang jalan menyeberang tengah malam
  membawa baseline sesi lama).
- Rekomendasi: simpan `session_date` di state; reset baseline saat tanggal
  UTC berganti.

## E-7. Sisa temuan audit TOP-20 yang BELUM dipatch (urutan berikutnya)
- P1-06: `/api/are/wfo` (UI) masih mengembalikan hasil Math.random().
- P1-08: DSR tanpa estimasi skew/kurtosis/var dari data; trial count = |grid|.
- P1-09: drift skema artifact bkt-* (CLI vs web_ui) mematahkan list/equity UI.
- P1-11: CI drift (ci.yml hanya install polars; ada import yaml/requests/MT5).
- P2-12: purify ulang per slice kandidat WFO (inkonsistensi halus + kerja ulang).
- P2-13: limit input/complexity endpoint komputasi berat web_ui (8080).
- P2-14: model portofolio backtest return-space (tanpa lot/margin/leverage).
- P2-15: filter tanggal local-time + pemilihan file "prefix terbaru" di loader.
- P2-16: decision engine TS tanpa versi/hash + tanpa golden-vector test.
- P2-17: heuristik offset epoch candle bridge (tick-time).
- P2-18: lapisan idempotensi EventStore (receipts/nonce) belum terpakai.


---

# Update Gelombang P2 (2026-09-07)

## Patched (P2 batch)
- **P2-12**: WFO memurifikasi data sekali (`pre_purified` jalur) — `5350cc9`.
- **P2-15**: data_loader UTC + pemilihan file by cakupan — `713b8dd`.
- **P2-17**: offset epoch candle dikuantisasi batas bar — `458f37b`.
- **P2-16**: decision engine provenance (engineVersion + strategyConfigHash) — UI `c8ca389`.
- **P2-13**: web_ui heavy-guard (503 fail-fast), payload 1MB, clamp WFO — `0f137bf`.
- **P2-14**: deklarasi batas model portofolio di kedua engine — `ec7bdfb`.

## Ditemukan & diperbaiki EMPIRIS (bukti nilai audit-jalan)
- **P2-12 fix empiris** (`f62dc0d`): CLI `backtest wfo` crash 100% (TypeError
  pre_purified) — lolos dari 646 test hijau karena tak ada test kontrak antar
  engine. Sekarang ada `test_engine_wfo_compat_p2_18.py`.
- **P3-20 dikonfirmasi**: CumulativeTrialTracker TIDAK ter-wire ke CLI
  `backtest wfo` (trials tetap 100 sebelum/sesudah run). Masih terbuka.

## Ditutup tanpa patch (sudah benar / status bukan cacat)
- **P2-18**: mesin idempotensi EventStore teruji menyeluruh di unit/e2e
  (test_storage.py, 32 referensi). Tabel receipts/nonce kosong di DB produksi
  = belum dipakai runtime, bukan bug. Rekomendasi: wire saat ada jalur
  order-state-event (Wave C lanjutan).
- **E-2/E-6 dst.**: tetap terbuka sesuai catatan awal.

## Sisa backlog setelah P2
- P3-20 wiring trial tracker ke WFO (bukti empiris ada).
- E-1 integration test men-trade demo riil (butuh keputusan).
- E-3 pin interpreter; E-4 rotasi log; E-6 reset harian breaker.
