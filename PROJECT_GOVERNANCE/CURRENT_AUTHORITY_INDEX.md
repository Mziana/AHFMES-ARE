# AHFMES Current Authority Index

Status: **ORIENTATION ONLY / NON-NORMATIVE / PRE-S0**

This isolated repository runs the **generation-38 qualification wave** under the S1
path namespace. The source repository's historical candidate claims, audit
records, commit identities, and qualification credit do not transfer.

## 🎛️ Cockpit Governance Dashboard

| Sistem & Dimensi Operasional | Status Kualifikasi | Baseline / Bukti Verifikasi | Catatan & Gatekeeping |
| :--- | :---: | :---: | :--- |
| **Organ 1 (Otak / Kognisi)** | 🟢 SOFTWARE_VERIFIED | 462 Alpha Seeds, Tree of Thoughts | `are/alpha_generator.py`, `are/search_tree.py` |
| **Organ 2 (Sistem Kekebalan)** | 🟢 SOFTWARE_VERIFIED | Governor, Critic, CSK Firewall | DSR, PSR, MC, WFA, Correlation Gate |
| **Organ 3 (Indra / Input)** | 🟢 SOFTWARE_VERIFIED | DataPurifier, LOCF Micro-gap | Anti-GIGO, Toxic Spread Neutralization |
| **Organ 4 (Otot / Eksekusi)** | 🟢 SOFTWARE_VERIFIED | MT5 Bridge & Gateway | Zero-LLM, Deterministic Sub-millisecond |
| **Organ 5 (Memori & DNA)** | 🟢 SOFTWARE_VERIFIED | The Windows Vault Protocol | Dual-Layer Witness + Replicator DR |
| **Organ 6 (Pusat Bahasa)** | 🟢 SOFTWARE_VERIFIED | Evidence RAG Copilot, XAI | Text-to-Query, Hallucination Detector |
| **Organ 7 (Pencernaan Eksternal)** | 🟢 SOFTWARE_VERIFIED | Scraper, Seed Extractor, Crisis Data | `TOOLS/` strictly isolated from core |
| **FASE 1: Dasar & Isolasi** | 🟢 FULLY_CLOSED | 328 tests pass (`@962e06b`) | Property Fuzzing, Async MT5, Backtest |
| **FASE 2: Imunitas & Vault** | 🟢 FULLY_CLOSED | 340 tests pass (`@fc4540e`) | Vault Witness, Data Cleansing, Watchdog |
| **FASE 3: Penelitian & XAI** | 🟢 FULLY_CLOSED | 352 tests pass (`@a93ab98`) | XAI, Alpha Ingestion, Monte Carlo, Scraper |
| **FASE 4: Rigor, Crisis & WFA** | 🟢 FULLY_CLOSED | 400 tests pass (`@61f54c9`) | FDR, DSR, RAG, Vault DR, Crisis Replay, WFA |
| **GELOMBANG RED TEAM HARDENING** | 🟢 FULLY_CLOSED | 416 tests pass (`@1857269`) | 12/12 Residu Terkatalog Tuntas (`RES-RED-01..12`) |
| **Residu Keamanan RES-COG-03** | 🟡 GATED | DELEGASI_024 Token Auth | Prasyarat: 7x24 Jam Daemon Stability Run |
| **FASE 5: Live / Paper Readiness** | 🔴 LOCKED | `PHASE_5_READINESS_MANIFESTO.md` | Gatekeeping Active: 7 Pre-Flight Checkpoints |
| **Status Lingkungan Produksi** | 🔴 CLOSED | Production Hard Gate Active | `PRODUCTION = CLOSED` |
| **Status Live / Paper Trading** | 🟡 DEMO_ONLY | Demo MT5 Feed & Web UI Only | `DEMO_TESTING_ONLY_AUTHORIZED` |

Current manifest binding: Generation 41
(`PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V41.md`).

The next commit containing V36 normative integration (Matrix V30, Inventory
V30, Correction V35, Protocol V36, Policy V9), this binding, and this index is
intended to become S0. This index must be finalized at S0 and is not writable
post-S0.

This index does not grant authority.

## Struktur folder (STRUCTURAL_GENERATION_S3, 2026-08-28)

Seluruh dokumen ARE kini berada di `ARE0/`, `ARE1/`, `ARE2/`, dan `ARE3/` per kategori
(`GRAND_DESIGN`, `CONTRACTS`, `MACHINE`, `MANIFEST`, dst — lihat
`GOVERNANCE_FOLDER_STRUCTURE_RULES.md`). Relokasi dilakukan byte-identical;
blob SHA tidak berubah. **Generasi manifest berikutnya wajib memakai path
baru** sesuai tabel routing pada aturan tersebut. Path lama di dokumen beku
tetap valid sebagai sitasi historis.

Catatan kredit: seluruh rekaman CLEAN_PASS/PASS pra-V36 di ARE0/QUALIFICATION adalah bukti historis QAO ber-kredit NOL; tidak menetapkan status saat ini. Diary khusus ARE0: `ARE0/DIARY/`. Diary ARE-1: `ARE1/DIARY/`. Diary ARE-2: `ARE2/DIARY/`. Diary ARE-3: `ARE3/DIARY/`. Indeks progres global:
`PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md`.

## Catatan Audit Historis & Penutupan Delegasi

| Delegasi / Milestone | Commit | Status Uji | Disposisi Audit |
| :--- | :--- | :---: | :--- |
| **ARE-0 FORMAL DESIGN** | `@03aec99` | Design Pass | CLOSED |
| **ARE-1 SCIENTIFIC KERNEL** | `@a6711d6` | 172 tests | CLOSED (Manifest V41) |
| **ARE-2 EXPERIENCE INTELLIGENCE** | `@7f57d12` | 214 tests | CLOSED (Manifest V41) |
| **ARE-3 AUTONOMOUS SCIENCE** | `@4cd22bf` | 246 tests | CLOSED (Manifest V41) |
| **ARE-4 GOVERNED EVOLUTION** | `@c65e793` | 260 tests | CLOSED (Manifest V41, 100% Pass) |
| **P001 ALPHA RESEARCH & TOOLING** | `@850c63b` | 281 tests | CLOSED (Manifest V41, 100% Pass) |
| **MT5 BRIDGE & GATEWAY** | `@74e2a01` | 289 tests | CLOSED (Manifest V41, 100% Pass) |
| **WEB CONTROL CENTER & UI** | `@9d0f5d3` | 295 tests | CLOSED (Manifest V41, 100% Pass) |
| **DELEGASI_025 SAFETY INVARIANTS** | `@b9e9531` | 321 tests | CLOSED (Property Fuzzing Pass) |
| **DELEGASI_026 ASYNC MT5 ISOLATION** | `@623b08e` | 325 tests | CLOSED (Async Bridge Pass) |
| **DELEGASI_028 VECTORIZED BACKTEST** | `@962e06b` | 328 tests | CLOSED (Polars Engine & AST Pass) |
| **DELEGASI_029 WINDOWS VAULT PROTOCOL** | `@0f8f4e5` | 331 tests | CLOSED (Dual-Layer Witness Pass) |
| **DELEGASI_029b DATA CLEANSING** | `@4b9fe90` | 336 tests | CLOSED (LOCF & Toxic Spread Pass) |
| **DELEGASI_033 LOCAL HEALTH MONITOR** | `@fc4540e` | 340 tests | CLOSED (Watchdog & Circuit Breaker) |
| **DELEGASI_030 XAI SHADOW DIAGNOSTICS** | `@4033c86` | 343 tests | CLOSED (Text-to-Query & Slippage) |
| **DELEGASI_031 ALPHA SEED INGESTION** | `@6ff7920` | 346 tests | CLOSED (Strict Schema Validation) |
| **DELEGASI_031b MONTE CARLO VALIDATION** | `@b2a3ab7` | 349 tests | CLOSED (Walk-Forward & Permutation) |
| **DELEGASI_032 EXTERNAL ALPHA PIPELINE** | `@a93ab98` | 352 tests | CLOSED (Multimodal Ingestion Pass) |
| **DELEGASI_035A STATISTICAL RIGOR** | `@ed2f438` | 364 tests | CLOSED (Acklam Probit, FDR, PSR, DSR) |
| **DELEGASI_035B COPILOT RAG & RESILIENCE** | `@3039fd1` | 386 tests | CLOSED (Evidence RAG, Vault DR, Alert) |
| **DELEGASI_035C CRISIS REPLAY ENGINE** | `@0c26c4f` | 390 tests | CLOSED (Black Swan Bankruptcy Veto) |
| **DELEGASI_036 WFA & PORTFOLIO GATE** | `@61f54c9` | 400 tests | CLOSED (WFA, Correlation, Sizing) |
