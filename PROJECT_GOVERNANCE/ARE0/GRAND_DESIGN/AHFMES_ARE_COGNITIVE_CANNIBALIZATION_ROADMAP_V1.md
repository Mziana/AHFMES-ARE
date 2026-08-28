# AHFMES-ARE — Cognitive Cannibalization Map & Master Execution Roadmap V1

Status: **NORMATIVE GRAND DESIGN & STRATEGIC ROADMAP / RATIFIED BY LEAD ARCHITECT & ADVISORY ARCHITECT**  
Effective Date: **2026-08-28**  
Target System: **AHFMES Autonomous Research Engine (ARE)**  
Baseline Commit: `962e06b` (328 tests pass, DELEGASI_028 Certified)

---

## 🏛️ Executive Summary & Core Philosophy

Dokumen ini menetapkan peta strategis kanibalisasi arsitektur dari repositori pola kecerdasan buatan terkemuka (`awesome-llm-apps`) ke dalam ekosistem kuantitatif otonom **AHFMES-ARE**.

### Prinsip Besi Arsitektur (The Iron Rules):
1. **"Curi Polanya, Buang Framework-nya" (Zero Framework Bloat):** Dilarang keras menginstal LangChain, CrewAI, AutoGen, atau framework orkestrator berat ke dalam runtime produksi inti. Gunakan Python Standard Library + dataclasses untuk modul inti, dan isolasikan dependensi pihak ketiga (`polars`, `pydantic`) pada lapisan batas (*boundary layer*) atau riset.
2. **Hukum Otoritas Mutlak ("THINK -> PROVE -> ACT"):** Kognisi LLM dibatasi secara ketat hanya pada pembentukan hipotesis (World 1: THINK). Pembuktian dan verifikasi (World 2: PROVE) dikendalikan secara mekanis oleh SearchTree, Backtest Harness, dan Governor. Eksekusi transaksi (World 3: ACT) 100% deterministik dan bebas dari sentuhan LLM.
3. **Isolasi Perbatasan Mutlak:** Folder `TOOLS/` (Organ 7) tidak boleh diimpor langsung oleh basis kode `are/`. Komunikasi antar-organ hanya melalui file JSON terstruktur atau API lokal yang terisolasi.

---

# 🗺️ PETA CANNIBALIZATION: awesome-llm-apps → AHFMES-ARE

Sumber Referensi: [https://github.com/Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)

---

### 🧠 1. Otak (Kognisi: `alpha_generator`, `search_tree`)
* **Target dari Repo:** AI Deep Research Agent atau AI System Architect Agent.
* **Apa yang DICURI (Pola):** Pola *Tree of Thoughts* atau *Chain of Thought* yang terstruktur. Cara agen memecah satu masalah besar menjadi beberapa hipotesis kecil, mengevaluasinya, dan menggabungkan yang terbaik.
* **Apa yang DIBUANG:** Seluruh framework orchestration berat (seperti LangGraph atau AutoGen penuh).
* **Integrasi ke ARE:** Kita menulis fungsi Python murni di `alpha_generator.py` yang memanggil API LLM dengan prompt yang memaksa output berupa JSON terstruktur (daftar hipotesis), lalu memproses JSON tersebut secara lokal. LLM hanya mengusulkan, `SearchTree` & `Governor` yang mengadili.

---

### 🛡️ 2. Sistem Kekebalan (Pertahanan: `safety`, `governor`, `critic`)
* **Target dari Repo:** Typed Agentic RAG with Pydantic AI dan RAG Failure Diagnostics Clinic.
* **Apa yang DICURI (Pola):** Konsep "Validasi Skema Ketat & Penolakan Otomatis". Jika bukti tidak memenuhi kriteria (misal: tidak ada `sharpe_ratio` atau `evidence_hash`), sistem harus menolak (*refusal*), bukan mencoba menebak atau berhalusinasi.
* **Apa yang DIBUANG:** Ketergantungan pada vector database eksternal untuk validasi sederhana.
* **Integrasi ke ARE:** Gunakan `pydantic` di boundary layer (`copilot`, `web_ui`, `TOOLS`) untuk memvalidasi input sebelum masuk ke core. Core engine (`governor.py`, `safety.py`) tetap 100% Pure Python Standard Library (`dataclasses`) untuk menjaga kesucian, determinisme, dan performa.

---

### 👁️👂 3. Indra (Input: `mt5_feed`, `ingestion`)
* **Target dari Repo:** Web Scraping AI Agent (hanya konsep dasarnya).
* **Apa yang DICURI (Pola):** Pola parsing data tidak terstruktur (seperti berita atau kalender ekonomi) menjadi data terstruktur (JSON).
* **Apa yang DIBUANG:** Penggunaan headless browser berat (seperti Playwright/Selenium) yang memakan memori besar.
* **Integrasi ke ARE:** Tetap gunakan `polars` untuk data numerik berkecepatan tinggi. Jika ada input teks (berita), gunakan skrip ringan berbasis `requests` + LLM API lokal/eksternal untuk ekstraksi sentimen terstruktur, lalu simpan sebagai kolom tambahan di dataframe.

---

### 💪 4. Otot (Eksekusi: `mt5_gateway`, `mt5_runner`)
* **Target dari Repo:** TIDAK ADA. NOL.
* **Peringatan Brutal:** Jangan pernah, dalam keadaan apa pun, membiarkan LLM atau agen AI mengambil keputusan eksekusi real-time atau menulis kode eksekusi secara dinamis. LLM terlalu lambat, non-deterministik, dan rentan halusinasi.
* **Integrasi ke ARE:** Organ ini 100% algoritma deterministik murni (Python Standard Library + Async). Tidak ada sentuhan LLM di sini. Keputusan eksekusi dan perlindungan modal ditangani sub-milidetik oleh `CapitalSafetyKernel`.

---

### 🗄️ 5. Memori & DNA (Ingatan: `evidence`, `storage`, `hasher`)
* **Target dari Repo:** Trust-Gated Multi-Agent Research Team (khususnya fitur hash-chained audit trail-nya).
* **Apa yang DICURI (Pola):** Konsep bahwa setiap entri data baru harus menyertakan hash dari entri sebelumnya (`current_hash = SHA256(data + previous_hash)`).
* **Apa yang DIBUANG:** Kompleksitas multi-agen yang tidak perlu untuk sekadar menulis log.
* **Integrasi ke ARE:** Ini adalah inti dari **DELEGASI 029 (The Windows Vault Protocol)**. Mengubah `storage.py` menjadi append-only dengan rantai kriptografis SHA-256 + Dual-Layer Witness (`SQLite` + `JSONL Shadow Witness`) + OS-Level Lockdown via `icacls`.

---

### 🗣️ 6. Pusat Bahasa & Antarmuka Sadar (`web_ui`, `cli`, `copilot`)
* **Target dari Repo:** Contextual AI RAG Agent atau RAG with Database Routing.
* **Apa yang DICURI (Pola):** Pola "Text-to-Query". Mengubah pertanyaan bahasa alami ("Mengapa strategi X gagal?") menjadi kueri terstruktur yang mencari data spesifik di database/ledger, lalu merangkum hasilnya secara faktual.
* **Apa yang DIBUANG:** Fitur web search fallback yang bisa menyebabkan kebocoran data atau respons lambat.
* **Integrasi ke ARE:** Upgrade `copilot.py`. Saat Anda bertanya, ia tidak "berpikir" atau berhalusinasi sendiri. Ia menerjemahkan pertanyaan Anda menjadi kueri ke `EvidenceLedger`, mengambil payload JSON yang terverifikasi hash-nya, dan menyajikannya sebagai penjelasan yang didukung data (*Explainable AI*).

---

### 🌐 7. Sistem Pencernaan Eksternal (`TOOLS/online_researcher`)
* **Target dari Repo:** GitHub MCP Agent atau AI Competitor Intelligence Agent.
* **Apa yang DICURI (Pola):** Kemampuan menjelajahi repositori atau artikel, memahami konteksnya, dan mengekstrak parameter (bukan kode).
* **Apa yang DIBUANG:** Kemampuan untuk menulis atau mengubah file di repositori target atau repositori sendiri (*Self-modifying code dilarang keras*).
* **Integrasi ke ARE:** Buat skrip terisolasi di folder `TOOLS/`. Skrip ini membaca sumber eksternal, lalu menghasilkan file `hypothesis_candidate.json` (misal: "Coba kombinasi MA 20 dan RSI 14"). File ini kemudian "dimakan" oleh `ingestion.py` untuk diuji oleh Backtest Harness (Otak) dan dihakimi oleh `Governor` (Sistem Kekebalan).

---

# 🗺️ ROADMAP EKSEKUSI: DARI POLA CANNIBALIZATION KE REALITAS SISTEM

Sumber Referensi: [https://github.com/Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)  
Prinsip Utama: Eksekusi bertahap (*Phased Execution*). Fondasi harus 100% terkunci sebelum fitur kognitif tingkat tinggi diaktifkan. Protokol 12-Langkah Audit Forensik diterapkan pada setiap fase.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ MASTER ROADMAP EKSEKUSI AHFMES-ARE                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ [FASE 1: PENGUNCIAN DASAR & ISOLASI] ────────────────────────── [SELESAI]   │
│  ├─ ✅ DELEGASI_025: Safety & Governor Property-Based Invariant Testing     │
│  ├─ ✅ DELEGASI_026: Async MT5 Bridge & Non-Blocking Isolation              │
│  ├─ ✅ DELEGASI_027: High-Performance Chunked Feature Ingestion             │
│  └─ ✅ DELEGASI_028: Isolated Vectorized Backtest Harness (polars)           │
│                                                                             │
│ [FASE 2: IMUNITAS DATA, KEBENARAN & KESELAMATAN LOKAL] ─────── [TARGET KITA]│
│  ├─ 📋 DELEGASI_029 : The Windows Vault Protocol (Immutable Shadow Witness) │
│  ├─ 📋 DELEGASI_029b: Data Cleansing & Gap-Alignment Engine (Anti-GIGO)     │
│  └─ 📋 DELEGASI_033 : Local Health Monitoring & Circuit Breaker (CCTV)      │
│                                                                             │
│ [FASE 3: INTERAKSI AHLI & EKSPANSI TERKONTROL] ─────────────── [MASA DEPAN] │
│  ├─ 📋 DELEGASI_030 : Explainable AI (XAI Text-to-Query Copilot)            │
│  ├─ 📋 DELEGASI_024 : Token Auth Gateway (Hanya setelah 7x24h lokal stabil) │
│  ├─ 📋 DELEGASI_031 : LLM-Assisted Hypothesis Generator (Tree of Thoughts)  │
│  └─ 📋 DELEGASI_032 : Multimodal External Alpha Pipeline (TOOLS/)           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ FASE 1: PENGUNCIAN DASAR & ISOLASI (STATUS: SELESAI / 328 TESTS PASS)
**Fokus:** Membangun organ dasar agar berfungsi dengan cepat, aman, dan tanpa dependensi berat.

1. **DELEGASI 025: Property-Based Safety & Governor Invariant Testing**
   * **Organ Sasaran:** 🛡️ Sistem Kekebalan (`are/safety.py`, `are/governor.py`).
   * **Capaian:** Fuzzing berbasis Hypothesis untuk fail-closed invariants, eliminasi NaN/Inf, pencegahan modifikasi kandidat oleh Governor, dan enforcement SoD.
2. **DELEGASI 026: MT5 Async Bridge & Non-Blocking Isolation**
   * **Organ Sasaran:** 💪 Otot (`are/mt5_feed.py`, `are/mt5_gateway.py`, `are/mt5_runner.py`).
   * **Capaian:** Jembatan asynchronous non-blocking berbasis `ThreadPoolExecutor` dengan circuit breaker latensi heartbeat (<5000ms).
3. **DELEGASI 027: High-Performance Chunked Feature Ingestion**
   * **Organ Sasaran:** 👁️👂 Indra (`are/features.py`).
   * **Capaian:** Streaming chunk-based ingestion berdaya tampung memori konstan O(1) berbasis pure Python standard library.
4. **DELEGASI 028: Isolated Vectorized Backtest Harness**
   * **Organ Sasaran:** 🧠 Otak & 🗄️ Memori (`are/backtest.py`, `tests/are/test_backtest_invariants.py`).
   * **Capaian:** Vectorized computation berbasis `polars` yang diisolasi penuh (*Architectural Firewall* + AST import scanner), serialisasi deterministik `df.to_dicts()`, dan penyimpanan bukti kriptografis ke `EvidenceLedger`.

---

## 🎯 FASE 2: IMUNITAS DATA, KEBENARAN & KESELAMATAN LOKAL (TARGET SAAT INI)
**Fokus:** Mengunci Memori, membersihkan bahan bakar data, dan memasang "CCTV" sebelum sistem diizinkan terekspos ke luar.

1. **DELEGASI 029: The Windows Vault Protocol (True Immutable Storage)**
   * **Organ Sasaran:** 🗄️ Memori & DNA (`are/evidence.py`, `are/storage.py`, `are/hasher.py`).
   * **Konsep yang Diambil:** Hash-chained audit trail + Dual-Layer Witness.
   * **Yang Dibuang:** Asumsi bahwa `chmod` atau SQLite default aman di Windows.
   * **Aksi Eksekusi:** Menerapkan 3 Lapisan Pertahanan:
     1. *Layer 1:* SQLite Primary Store (cepat, queryable, terstruktur).
     2. *Layer 2:* JSONL Shadow Witness (append-only parallel stream dengan cryptographic linking).
     3. *Layer 3:* Windows ACL Lockdown via `icacls` untuk memblokir hak tulis langsung di level OS.
     * Implementasi `verify_full_chain_integrity()` dan simulasi serangan *user-level tampering*.
2. **DELEGASI 029b: Data Cleansing & Gap-Alignment Engine**
   * **Organ Sasaran:** 👁️👂 Indra (Input).
   * **Konsep yang Diambil:** Mencegah "Garbage In, Garbage Out".
   * **Yang Dibuang:** Pipeline download mentah tanpa filter yang menghasilkan Sharpe Ratio palsu.
   * **Aksi Eksekusi:** Engine otomatis yang menolak data kotor, mengisi missing ticks dengan interpolasi matematis, dan menormalisasi anomali spread SEBELUM data diizinkan masuk ke Backtest Harness (DELEGASI 028).
3. **DELEGASI 033: Local Health Monitoring & Circuit Breaker**
   * **Organ Sasaran:** Sistem Saraf Otonom.
   * **Konsep yang Diambil:** Pasang CCTV sebelum buka pintu.
   * **Yang Dibuang:** Menunda monitoring ke Fase 3.
   * **Aksi Eksekusi:** Memantau integritas Vault, memory leak di `AREServerState`, heartbeat MT5, dan latensi eksekusi secara lokal. Wajib stabil sebelum izin *Internet Exposure* dibuka.

---

## 🔭 FASE 3: INTERAKSI AHLI & EKSPANSI TERKONTROL (MASA DEPAN)
**Fokus:** Mengaktifkan kemampuan "berdialog" dan "belajar dari luar", dengan batasan isolasi yang ketat.

1. **DELEGASI 030: Explainable AI (XAI) Conscious Bridge**
   * **Organ Sasaran:** 🗣️ Pusat Bahasa & Antarmuka Sadar (`are/web_ui.py`, `are/copilot.py`).
   * **Konsep yang Diambil:** Pola "Text-to-Query" (Mengubah pertanyaan alami menjadi kueri database terstruktur).
   * **Yang Dibuang:** Fitur web search fallback yang lambat dan berisiko kebocoran data.
   * **Aksi Eksekusi:** Mengupgrade `copilot.py`. Saat ditanya "Mengapa?", sistem menerjemahkannya menjadi kueri ke `EvidenceLedger`, mengambil payload JSON yang hash-nya terverifikasi, dan menyajikannya sebagai jawaban berbasis data (bukan halusinasi LLM).
2. **DELEGASI 024: Token Auth Gateway & Secure AI Tunnel**
   * **Organ Sasaran:** 🗣️ Antarmuka Eksternal.
   * **Syarat Mutlak:** HANYA dieksekusi jika Fase 2 (terutama DELEGASI 033) telah terbukti stabil berjalan minimal 7x24 jam di lingkungan lokal.
   * **Aksi Eksekusi:** Proteksi akses dashboard dari internet menggunakan token auth middleware dan secure tunnel.
3. **DELEGASI 031: LLM-Assisted Hypothesis Generator (Tree of Thoughts)**
   * **Organ Sasaran:** 🧠 Otak (`are/alpha_generator.py`).
   * **Konsep yang Diambil:** Pemecahan masalah besar menjadi hipotesis kecil via LLM.
   * **Aksi Eksekusi:** LLM hanya diizinkan mengusulkan parameter JSON. `SearchTree` & `Governor` tetap menjadi hakim mutlak yang menguji dan meratifikasi.
4. **DELEGASI 032: Multimodal External Alpha Pipeline**
   * **Organ Sasaran:** 🌐 Sistem Pencernaan Eksternal (`TOOLS/online_researcher`).
   * **Konsep yang Diambil:** Menelan berita/transkrip YouTube dan memuntahkan parameter terstruktur.
   * **Aksi Eksekusi:** Skrip terisolasi di `TOOLS/` menghasilkan `hypothesis_candidate.json` yang kemudian "dimakan" oleh Data Cleansing Engine (029b) dan diuji oleh Backtest Harness.
