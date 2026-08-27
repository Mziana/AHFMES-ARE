# ARE3 — Residual & Debt Register

Status: **REGISTER EVIDENCE-CHRONOLOGY ARE-3 / ZERO AUTHORITY / APPEND-ONLY**  
Fase: **ARE-3 Autonomous Science** — Baseline `@360cf76`  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` §6 + prinsip *perbaiki yang bisa, tunda yang harus, catat biar tidak lupa*  
Lokasi: `PROJECT_GOVERNANCE/ARE3/RESIDUAL_REGISTER.md` (ledger terpusat ARE-3) + `DIARY/`

---

## 1. Ringkasan Eksekutif — Pembukaan ARE-3 (Generation 41)

Seluruh hutang arsitektur yang sengaja ditunda dari fase ARE-1 & ARE-2 diwariskan ke register ini dan dilacak secara aktif:

| ID | Kategori | Ringkasan Deskripsi | Status di ARE-3 |
|---|---|---|:---:|
| `DEBT-01` | High | God Class `Registry` (~700 baris, 8 lifecycle entitas) | DEFERRED (Target Refactor ARE-3) |
| `DEBT-02` | High | God File `experience.py` (43 kelas dalam 1 file) | DEFERRED (Target Pemecahan Modul) |
| `DEBT-03` | Critical | Enkapsulasi DB: `evidence.py` & `registry.py` memanggil `_get_conn()` | **RESOLVED & VERIFIED** (Slice-2 EventStore API) ✅ |
| `DEBT-04` | Medium | Duplikasi konstanta lifecycle `state_machine.py` ↔ `registry.py` | **RESOLVED & VERIFIED** (Slice-1 `are/constants.py`) ✅ |
| `DEBT-05` | Low | Folder `GRAND DESIGN` (spasi dalam nama direktori) | DEFERRED |
| `DEBT-06` | Medium | Over-engineering dokumentasi tata kelola | ACKNOWLEDGED |
| `DEBT-07` | Low | Ketiadaan `pyproject.toml` / konfigurasi formal | PLANNED BATCH |
| `DEBT-08` | Low | Ketiadaan `conftest.py` shared fixtures | PLANNED BATCH |
| `RES-01-sisa`| Infra | OS-Level keeper process & permission hardening | DEFERRED PRODUCTION |

---

## 2. Invarian Tata Kelola (G07 / G18)

```text
G07 retention never erases debt — family_debt persist meski archival
G18 new IDs cannot reset debt — graveyard persist
→ Pembukaan fase baru ARE-3 TIDAK MENGHAPUS hutang arsitektur lama.
→ Seluruh hutang dicatat, diaudit, dan diselesaikan bertahap secara terkontrol.
```
