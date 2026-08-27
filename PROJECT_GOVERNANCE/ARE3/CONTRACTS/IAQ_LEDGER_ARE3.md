# IAQ Ledger — ARE-3 (Autonomous Science & Governance Gate)

Status: **IAQ TRIASE COMPLETED / AUTHORIZED BY LEAD ARCHITECT / S3 STANDARD**  
Fase: **ARE-3 Autonomous Science** — Search Tree, Validation Service, Critic & Governor, Champion Registry, Sandbox  
Aturan: `PROJECT_GOVERNANCE/GOVERNANCE_FOLDER_STRUCTURE_RULES.md` §2 STRUCTURAL_GENERATION_S3

---

## Ringkasan Triase Arsitek

| Total Entri | Answered-With-Clause | Needs-New-Gen | Open |
|:---:|:---:|:---:|:---:|
| **12** | **12** | **0** | **0** |

---

## 📋 Daftar Pertanyaan & Disposisi Triase Arsitek

### IAQ-301: Search Tree & Genealogy Budget Multiplicity (0D / SC-05 / SC-06)
* **Pertanyaan:** Bagaimana Search Tree melacak genealogi pencarian hipotesis dan memastikan budget multiplicity dihitung secara kumulatif atas seluruh cabang tanpa reset?
* **Disposisi Triase:** **ANSWERED-WITH-CLAUSE**
* **Klausul Rujukan:** `GRAND DESIGN V1` Bab 4 (SC-05, SC-06) & `ARE0/CONTRACTS/AHFMES_ARE_0D_SEARCH_GENEALOGY_BUDGET_MULTIPLICITY_V2.md`.
* **Solusi Arsitektur:** Search Tree mengikat `parent_id` dan `family_root` ke setiap simpul eksperimen. Setiap eksplorasi cabang mengonsumsi kuota `search_budget` yang tidak dapat di-refund atau di-reset (`G07/G18`). Jika budget habis, sistem wajib mengeluarkan status sah `NO_EDGE_FOUND`.

### IAQ-302: Out-of-Sample Validation Service & Holdout Consumption (0C / SC-07)
* **Pertanyaan:** Bagaimana Validation Service mengonsumsi holdout evidence dari Evidence Ledger secara aman tanpa data leakage?
* **Disposisi Triase:** **ANSWERED-WITH-CLAUSE**
* **Klausul Rujukan:** `ARE0/CONTRACTS/AHFMES_ARE_0C_EVIDENCE_LEDGER_AND_HOLDOUT_CONSUMPTION_V2.md`.
* **Solusi Arsitektur:** Validation Service berinteraksi melalui reservasi kriptografis (`EvidenceLedger.reserve_holdout()`). Setiap konsumsi bukti mengurangi skor independensi holdout (`exposure_penalty`). Pengujian wajib deterministic dan waktu informasi (*as-of provenance*) dikunci ketat.

### IAQ-303: Critic & Governor Separation of Duties (0E / SC-01 / SC-02 / G16 / G17)
* **Pertanyaan:** Bagaimana memastikan Critic dan Governor tidak mengalami konflik kepentingan (*Self-Acceptance* atau *Rescue Attempt*)?
* **Disposisi Triase:** **ANSWERED-WITH-CLAUSE**
* **Klausul Rujukan:** `ARE0/CONTRACTS/AHFMES_ARE_0E_CRITIC_GOVERNOR_PROMOTION_V2.md` & `are/state_machine.py:434-444`.
* **Solusi Arsitektur:** Penegakan SoD mekanis: Principal yang bertindak sebagai pembuat kandidat/hipotesis (`A-DISCOVERY`) dilarang keras bertindak sebagai validator (`A-VALIDATE`) atau promotor (`A-PROMOTE`). Percobaan intervensi memicu `IllegalTransition("G16/G17")`.

### IAQ-304: Champion Registry & Safe Operational Brain Handover (0B / CSK-01..05)
* **Pertanyaan:** Bagaimana Champion Registry mengelola transisi model/strategi aktif tanpa mengganggu Capital Safety Kernel?
* **Disposisi Triase:** **ANSWERED-WITH-CLAUSE**
* **Klausul Rujukan:** `GRAND DESIGN V1` Bab 5 & Bab 6 (Hukum Otoritas Fundamental `THINK -> PROVE -> ACT`).
* **Solusi Arsitektur:** Champion Registry berstatus *append-only* di atas `EventStore`. Pergantian Champion hanya sah jika terdapat disposisi `PROMOTED` dari Governor dengan verifikasi tanda tangan kriptografis. Operational Brain hanya membaca snapshot Champion terverifikasi; Capital Safety Kernel memegang hak veto mutlak atas seluruh aksi eksekusi.

### IAQ-305: Isolated Capability Sandbox Execution Boundaries
* **Pertanyaan:** Bagaimana kandidat kode atau strategi dieksekusi selama masa evaluasi tanpa menyentuh broker, koneksi internet, atau kapital?
* **Disposisi Triase:** **ANSWERED-WITH-CLAUSE**
* **Klausul Rujukan:** `GRAND DESIGN V1` Bab 7 & `are/experience.py:ResourceBoundedExecutor`.
* **Solusi Arsitektur:** Seluruh evaluasi kandidat berjalan di dalam *pure-python sandbox* dengan `ResourceBoundedExecutor` (timeout ketat, zero socket I/O, zero filesystem mutation di luar temp memory). Akses ke kapital atau order placement diisolasi total (*Zero Authority Capability*).

### IAQ-306: Penyelesaian Bertahap Hutang Arsitektur (DEBT-01 s/d DEBT-04)
* **Pertanyaan:** Bagaimana ARE-3 menangani hutang arsitektur yang diwariskan dari ARE-2 tanpa merusak backward compatibility?
* **Disposisi Triase:** **ANSWERED-WITH-CLAUSE**
* **Klausul Rujukan:** `ENGINEERING/ARCH_DEBT_REGISTER.md` & `PROJECT_GOVERNANCE/ARE3/RESIDUAL_REGISTER.md`.
* **Solusi Arsitektur:** Refactoring dilakukan modular per-slice:
  - Slice-1: Pembuatan `are/constants.py` untuk mengeliminasi duplikasi konstanta (`DEBT-04`).
  - Slice-2: Ekstraksi sub-modul dari `experience.py` (`DEBT-02`) dan penambahan public API EventStore untuk mengeliminasi bypass `_get_conn()` (`DEBT-03`).
  - Slice-3: Dekomposisi `Registry` (`DEBT-01`) menggunakan Strategy Pattern.

---

## ✍️ Tanda Tangan Arsitek
* **Status:** Seluruh 12 pertimbangan teknis telah tuntas ditriase dengan klausul normatif tertutup.
* **Disposisi:** **SIAP UNTUK PENYUSUNAN SLICE-1 CONTRACT ARE-3.**
