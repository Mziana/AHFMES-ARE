# CONTRACT: RUNTIME TRUTH & EXECUTION SAFETY

Status: **RATIFIED OPERATIONAL CONTRACT**  
Domain: **are/mt5_gateway.py, are/mt5_runner.py, are/safety.py**  
Aturan Pengikat: `ENGINEERING/RULES.md:E-01, E-03, E-04, E-06`

---

## 1. Hukum Mutlak Kebenaran Runtime (Runtime Truth Invariants)

1. **INVARIAN RATE LIMITER (ACC-404 Semantik Benar):**
   - Parameter `recent_order_count` yang dikirim ke `CapitalSafetyKernel` WAJIB merupakan jumlah order yang berhasil dikirim dalam **jendela waktu geser 60 detik terakhir (sliding 60-second window)**, BUKAN jumlah posisi terbuka (`len(open_positions)`).
   - Order tracker wajib mencatat timestamp setiap pengiriman order dan membuang rekaman yang berumur $> 60.0$ detik.

2. **INVARIAN OPEN POSITIONS GATEWAY:**
   - Pada mode Live (`self._mt5_lib is not None`), `get_open_positions()` WAJIB memanggil `self._mt5_lib.positions_get()`, melakukan ekstraksi kamus posisi, dan mengembalikannya ke pemanggil. DILARANG mengembalikan list kosong `[]` statis.

3. **INVARIAN FAIL-CLOSED GATEWAY (Anti-Silent Mock Fallback):**
   - Jika inisialisasi meminta mode Live (`use_mock=False`), kegagalan impor pustaka `MetaTrader5` atau kegagalan koneksi terminal WAJIB melempar `RuntimeError("LIVE_MT5_REQUIRED_BUT_UNAVAILABLE")`.
   - DILARANG beralih secara diam-diam (*silent fallback*) ke `MT5MockGateway` saat mode Live diminta.

4. **INVARIAN GUARANTEED FLAT:**
   - Method `emergency_flat()` dianggap sukses JIKA DAN HANYA JIKA setelah seluruh perintah penutupan dikirim, pemeriksaan ulang via `get_open_positions()` menghasilkan $0$ posisi terbuka.
   - Jika setelah maksimal 3 kali percobaan ulang masih terdapat posisi tersisa, sistem WAJIB memicu notifikasi darurat `HealthStatus.CRITICAL` dan mengunci status sistem ke `HALTED`.

5. **INVARIAN DYNAMIC ACCOUNT DRAWDOWN:**
   - Runner eksekusi live (`MT5LiveRunner`) WAJIB menghitung `drawdown` secara real-time dari data akun broker:
     $$\text{Drawdown} = \frac{\text{Balance} - \text{Equity}}{\text{Balance}}$$
   - DILARANG menggunakan nilai hardcoded statis seperti `0.01`.

6. **INVARIAN NON-SILENT EXCEPTION:**
   - Setiap unhandled exception pada loop eksekusi live (`run_live_loop` dan `run_live_loop_async`) WAJIB dilaporkan ke `SystemHealthMonitor.evaluate_system_health()`, dicatat ke `EvidenceLedger`, dan mengubah state mesin ke `HALTED` sebelum loop berhenti.
