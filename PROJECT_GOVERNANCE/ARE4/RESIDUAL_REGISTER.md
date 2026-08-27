# Residual & Architecture Debt Register — ARE-4 (Generation 41+)

Status: **REGISTER AKTIF / TRACKING RESIDUAL FASE ARE-4**  
Baseline: `@ebf931d` (Penutupan ARE-3, Pembukaan ARE-4)

---

## 1. Ringkasan Eksekutif — Pembukaan ARE-4

Daftar hutang arsitektur yang tersisa dan dilacak di fase ARE-4:

| ID | Kategori | Ringkasan Deskripsi | Status di ARE-4 |
|---|---|---|:---:|
| `DEBT-01` | High | God Class `Registry` (~700 baris, 8 lifecycle entitas) | **RESOLVED & VERIFIED** (ARE-4 Slice-2 Strategy Managers) ✅ |
| `DEBT-02` | High | God File `experience.py` (43 kelas dalam 1 file) | **RESOLVED & VERIFIED** (ARE-4 Slice-3 Submodules & Facade) ✅ |
| `DEBT-03` | Critical | Enkapsulasi DB: `evidence.py` & `registry.py` memanggil `_get_conn()` | **RESOLVED & VERIFIED** (ARE-3 Slice-2) ✅ |
| `DEBT-04` | Medium | Duplikasi konstanta lifecycle `state_machine.py` ↔ `registry.py` | **RESOLVED & VERIFIED** (ARE-3 Slice-1) ✅ |
| `DEBT-05` | Low | Folder `GRAND DESIGN` (spasi dalam nama direktori) | DEFERRED |
| `DEBT-06` | Medium | Over-engineering dokumentasi tata kelola | ACKNOWLEDGED |
| `DEBT-07` | Low | Ketiadaan `pyproject.toml` / konfigurasi formal | PLANNED BATCH |
| `DEBT-08` | Low | Ketiadaan `conftest.py` shared fixtures | PLANNED BATCH |
| `RES-01-sisa`| Infra | OS-Level keeper process & permission hardening | DEFERRED PRODUCTION |

---

## 2. Invarian Tata Kelola (G07 / G18)

```text
Aturan: Tidak ada hutang arsitektur berstatus Critical yang diabaikan.
        DEBT-01 dan DEBT-02 dijadwalkan untuk direfaktor secara modular pada gelombang ARE-4.
```
