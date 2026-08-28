# WEB_UI — Residual Register

Status: **ACTIVE TRACKING / MINOR DEBTS ONLY**  
Fase: **WEB_UI Localhost Control Center & Interactive Chat Copilot**

---

## 1. Status Hutang Arsitektur Utama (Telah Tuntas)

| ID | Kategori | Ringkasan Deskripsi | Status di WEB_UI |
|---|---|---|:---:|
| `DEBT-01` | High | God Class `Registry` pemecahan ke Sub-Managers Strategy Pattern | **RESOLVED & VERIFIED** (ARE-4 Slice-2) ✅ |
| `DEBT-02` | High | God File `experience.py` pemecahan ke 4 Submodul Domain & Facade | **RESOLVED & VERIFIED** (ARE-4 Slice-3) ✅ |
| `DEBT-03` | Critical | Enkapsulasi DB: `_get_conn()` dilarang di luar `storage.py` | **RESOLVED & VERIFIED** (ARE-3 Slice-2) ✅ |
| `DEBT-04` | Medium | Duplikasi konstanta lifecycle `state_machine.py` ↔ `registry.py` | **RESOLVED & VERIFIED** (ARE-3 Slice-1) ✅ |

---

## 2. Hutang Arsitektur Minor Tersisa (Non-Blocking)

| ID | Kategori | Ringkasan Deskripsi | Rencana Penanganan |
|---|---|---|:---:|
| `DEBT-05` | Low | Folder `GRAND DESIGN` (spasi dalam nama direktori) | DEFERRED |
| `DEBT-06` | Medium | Over-engineering dokumentasi tata kelola | ACKNOWLEDGED |
| `DEBT-07` | Low | Ketiadaan `pyproject.toml` / konfigurasi formal | TARGET HOUSEKEEPING BATCH |
| `DEBT-08` | Low | Ketiadaan `conftest.py` shared fixtures | TARGET HOUSEKEEPING BATCH |
