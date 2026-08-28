# COUNCIL PROTOCOL — SYSTEMIC CROSS-IMPACT AUDIT

Status: **NORMATIVE PROTOCOL / RATIFIED BY LEAD ARCHITECT**  
Effective Date: **2026-08-28**  
Target Wave: **COGNITIVE_ROADMAP (Phase 1, Phase 2, Phase 3)**

---

## 1. Prinsip Utama

Setiap audit penyelesaian delegasi **DILARANG** hanya memeriksa lulus/tidaknya unit pengujian lokal. Lead Architect dan Council wajib memverifikasi **5 Dimensi Dampak Lintas Sistem**:

1. **🛡️ Kemurnian Runtime Produksi (*Production Runtime Purity*):**
   - Memastikan nol kebocoran dependensi pihak ketiga (`polars`, `pydantic`, `psutil`) ke dalam modul inti eksekusi live (`are/safety.py`, `are/mt5_gateway.py`, `are/operational.py`).
2. **⚡ Konkurensi Threading, I/O & Memori (*Concurrency & Resource Impact*):**
   - Memastikan integritas Dual-Layer Witness (JSONL `fsync`) tidak memicu race condition, deadlock, atau file-lock contention pada SQLite WAL mode.
3. **🖥️ Kompatibilitas Web UI & Copilot (*User-Facing Stability*):**
   - Memastikan `AREServerState` dan asisten AI Copilot di Web UI tetap berfungsi transparan, thread-safe, dan memiliki kemampuan *self-healing*.
4. **🌊 Aliran Data Hulu-ke-Hilir (*Data-to-Governor Pipeline Integrity*):**
   - Memastikan data yang dibersihkan oleh `DataPurifier` tidak mengandung anomali spread/gap sebelum diratifikasi oleh `GovernorEngine`.
5. **🔄 Regresi Global & Kompatibilitas Mundur (*Zero Regression Invariant*):**
   - Memastikan 100% test suite global dari ARE-0 s/d ARE-4 tetap HIJAU tanpa flakiness.
