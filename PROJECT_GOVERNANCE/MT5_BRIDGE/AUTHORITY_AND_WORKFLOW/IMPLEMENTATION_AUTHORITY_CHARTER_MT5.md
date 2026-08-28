# IMPLEMENTATION AUTHORITY CHARTER — MT5_BRIDGE

Status: **RATIFIED T4 — IMPLEMENTATION AUTHORIZED**  
Fase: **MT5_BRIDGE (MetaTrader 5 Adapter, Gateway & Demo Runner)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@6a3763d`

---

## 1. Deklarasi Mandat MT5_BRIDGE

Dengan ini disahkan bahwa modul integrasi **MT5_BRIDGE** (**MetaTrader 5 Live Feed Adapter, Safety-Gated Execution Gateway, dan Live Demo Runner**) resmi berstatus **AUTHORIZED** untuk diimplementasikan.

## 2. Batasan Otoritas & Firewall

1. **Gated by Capital Safety Kernel (CSK):** Seluruh order yang menuju fungsi eksekusi MT5 (`order_send()`) WAJIB melalui verifikasi non-bypassable `CapitalSafetyKernel.evaluate_order_intent()`. Jika `allowed == False`, pengiriman order langsung dibatalkan (*vetoed*).
2. **Emergency Flat Protection:** Jika terjadi pelanggaran drawdown atau tombol kill-switch aktif, gateway WAJIB memicu fungsi `close_all_positions()` untuk melikuidasi seluruh posisi terbuka di MT5.
3. **Demo / Mock First Architecture:** Implementasi wajib menyediakan simulator/mock mode (`MT5MockFeed`, `MT5MockGateway`) sehingga seluruh fungsionalitas dapat diuji secara 100% deterministik tanpa mewajibkan instalasi terminal fisik MT5 saat pengujian otomatis.
4. **Zero External Dependencies Core Requirement:** Modul bridge menggunakan `MetaTrader5` secara opsional/dynamic-import jika terpasang, dengan fallback murni Python Standard Library (stdlib only: `json`, `math`, `time`, `typing`, `dataclasses`, `sqlite3`, dll.) agar tidak merusak build lingkungan non-Windows/CI.

---

```text
RATIFIED BY: Lead Architect & Auditor
DATE       : 2026-08-28
DISPOSITION: MT5_BRIDGE IMPLEMENTATION AUTHORIZED
```
