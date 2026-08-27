# ARE2 — Residual & Debt Register

Status: **REGISTER EVIDENCE-CHRONOLOGY ARE-2 / ZERO AUTHORITY / CLOSED**  
Fase: **ARE-2 Experience Intelligence** — Baseline `@7f57d12`  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` §6 + prinsip *perbaiki yang bisa, tunda yang harus, catat biar tidak lupa*

---

## 1. Residual Status pada Penutupan ARE-2

| ID | Kategori | Penanganan di ARE-2 | Status Akhir ARE-2 |
|---|---|---|:---:|
| `IC-5` | Residual ARE-1 | Tabel `rollback_cause_observations` diimplementasikan di `are/storage.py` (Slice-2) | **RESOLVED & VERIFIED** ✅ |
| `RES-03` | Residual ARE-1 | `var_ref` diikat ke `_compute_event_hash` & migration script dibuat (Slice-2) | **RESOLVED & VERIFIED** ✅ |
| `RES-01` | Residual ARE-1 | Authorizer fail-closed (FIX-01) + `chmod 600` + `CapabilityToken` HMAC (FIX-04) | **RESOLVED & VERIFIED** ✅ |
| `ACC-9/18` | Audit Finding | `ExperienceStore` direfaktor me-reuse `EventStore` tanpa raw SQL (DELEGASI_009) | **RESOLVED & VERIFIED** ✅ |
| `DEBT-01..08` | Arsitektur Jangka Panjang | Dicatat di `ENGINEERING/ARCH_DEBT_REGISTER.md` untuk diwariskan ke ARE-3 | **DEFERRED TO ARE-3** 📋 |

---

## 2. Invarian Tata Kelola (G07 / G18)

```text
G07 retention never erases debt — family_debt persist meski archival
G18 new IDs cannot reset debt — graveyard persist
→ Penutupan ARE-2 mewariskan seluruh 8 hutang arsitektur jangka panjang ke ARE-3.
```
