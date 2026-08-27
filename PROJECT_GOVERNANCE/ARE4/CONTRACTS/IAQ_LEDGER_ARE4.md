# IAQ LEDGER — ARE-4 (Governed Evolution & Capital Safety)

Status: **FROZEN T2 — ALL 12 IAQ ANSWERED-WITH-CLAUSE**  
Fase: `ARE-4`  
Baseline: `@ebf931d`

---

| IAQ # | Pertanyaan Arsitektur | Disposisi & Klausul Wajib |
|:---:|---|---|
| **IAQ-401** | Apakah Fast Loop diizinkan mengubah policy produksi secara *in-place*? | **DILARANG KERAS** (Bab 8). Fast Loop hanya mengestimasi state; mutasi policy wajib lewat Slow Loop. |
| **IAQ-402** | Di manakah letak lapisan Capital Safety Kernel (CSK)? | Di antara pemilihan aksi (*Action Selector*) dan eksekusi, bertindak sebagai *deterministic fail-closed veto*. |
| **IAQ-403** | Bagaimana penanganan jika data pasar kadaluarsa / desinkronisasi timestamp? | CSK langsung menerbitkan veto `ABSTAIN/FLAT` secara *fail-closed*. |
| **IAQ-404** | Apakah eksekusi Fast Loop di ARE-4 boleh terhubung ke live broker? | **DILARANG**. Tetap strictly simulation / paper test bounded. |
| **IAQ-405** | Bagaimana interaksi antara `ChampionRegistry` dan `OperationalBrain`? | `OperationalBrain` membaca snapshot active champion secara read-only. |
| **IAQ-406** | Apakah `CapitalSafetyKernel` membutuhkan dependensi pihak ketiga? | **TIDAK**. Murni Python Standard Library (100% stdlib). |
| **IAQ-407** | Bagaimana sinyal darurat (Emergency Flat) diproses? | Veto prioritas tertinggi yang mengabaikan seluruh sinyal model/champion. |
| **IAQ-408** | Bagaimana auditability keputusan CSK dipertahankan? | Setiap evaluasi CSK menghasilkan `SafetyDecision` yang memiliki hash kriptografis. |
| **IAQ-409** | Apakah modularisasi `DEBT-01` & `DEBT-02` merusak antarmuka publik lama? | **TIDAK**. Menggunakan facade / backward-compatible imports dengan 0 test regression. |
| **IAQ-410** | Bagaimana interaksi Slow Loop memicu Research Episode baru? | Anomali performa/regret yang terdeteksi dicatat sebagai event ke Problem Registry. |
| **IAQ-411** | Apakah parameter CSK boleh di-override tanpa tata kelola? | **DILARANG**. Parameter CSK dibekukan dalam konfigurasi terverifikasi. |
| **IAQ-412** | Kapan ARE-4 dinyatakan selesai? | Ketika seluruh 10 kriteria kontrak Slice-1..3 PASS, 100% test hijau, dan DEBT-01/DEBT-02 terselesaikan. |
