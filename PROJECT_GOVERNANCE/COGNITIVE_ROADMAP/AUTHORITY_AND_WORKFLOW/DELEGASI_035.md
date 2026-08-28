# MANDAT RESMI: DELEGASI_035 — COMPREHENSIVE HARDENING & E2E COGNITIVE GAUNTLET

Status: **IMPLEMENTATION AUTHORITY CHARTER / RATIFIED BY LEAD ARCHITECT & ADVISORY ARCHITECT**  
Kategori: **COGNITIVE_ROADMAP / FASE 4 ENTRY / CROSS-CUTTING HARDENING**  
Baseline: `8977939` on `main` (352 tests pass, Phase 3 Certified)  
Ratified: **2026-08-28**  

---

## 1. PERAN

Kamu adalah **SENIOR QUANTITATIVE SYSTEMS & RELIABILITY ENGINEER** (Engineering AI).  
GERBANG: **DELEGASI_035 — COMPREHENSIVE HARDENING & E2E GAUNTLET — AUTHORIZED**.  
HANYA untuk lingkup di bawah. Luar lingkup = **DILARANG**.

---

## 2. FILOSOFI ARSITEKTUR (Hasil Audit Silang 3-Pihak)

```text
PRINSIP 1: STATISTICAL RIGOR FIRST
   Governor tidak boleh mempromosikan kandidat dari batch pengujian massal
   (462+ Alpha Seeds) tanpa koreksi Benjamini-Hochberg (FDR) dan Deflated
   Sharpe Ratio (DSR). Ini prasyarat mutlak, bukan fitur opsional.

PRINSIP 2: EVIDENCE-BOUND COGNITION
   Jalur Ollama di Copilot WAJIB menerima fakta bit-for-bit dari EvidenceLedger
   dan EventStore sebelum prompt dikirim. Zero hallucination = zero tebakan.

PRINSIP 3: HUMAN-IN-THE-LOOP FOR CRITICAL
   HealthMonitor yang mendeteksi CRITICAL (MT5 silence, vault corruption,
   latency spike, memory exhaustion) WAJIB memberitahu user via webhook
   eksternal minimum (Telegram/Email). Sistem tidak boleh "tuli dan bisu"
   saat user tidur.

PRINSIP 4: DISASTER RECOVERY WITHOUT BLOAT
   Vault (SQLite + JSONL) WAJIB direplikasi ke lokasi sekunder (USB/NAS/
   cloud folder) dengan verifikasi hash. Bukan kdb+, bukan TimescaleDB,
   bukan Kubernetes — hanya shutil.copy + hashlib.sha256.

PRINSIP 5: STRESS TEST WITH REAL HISTORY
   Sistem WAJIB diuji pada dataset krisis historis nyata (2008 GFC,
   COVID 2020 flash crash, CHF 2015 depeg) yang diunduh gratis dari
   Yahoo Finance / FRED, dipurifikasi via DataPurifier, dan disimpan
   di `data/historical_crises/`.

PRINSIP 6: ZERO FRAMEWORK BLOAT
   Dilarang keras: LangChain, CrewAI, AutoGen, ChromaDB, Weaviate,
   Kubernetes, Docker (untuk produksi), Prometheus, Grafana, PagerDuty,
   kdb+, TimescaleDB, satellite data ingestion. Semua solusi harus
   100% Python Standard Library + Polars (boundary layer) + urllib.
```

---

## 3. RINGKASAN RUANG LINGKUP (6 Bagian)

| Bagian | Target File | Fokus | Status Target |
|---|---|---|---|
| A | `are/validation.py` | FDR Correction + Deflated Sharpe Ratio + Probabilistic Sharpe | **AUTHORIZED** |
| B | `are/copilot.py` | Evidence Pre-Injection + Multi-Step Sub-Querying RAG + Hallucination Detector | **AUTHORIZED** |
| C | `tests/are/test_e2e_cognitive_pipeline.py` | 7-Organ E2E Gauntlet (Happy Path + Rejection + Circuit Breaker + Vault Healing) | **AUTHORIZED** |
| D | `are/storage.py` + `are/health_monitor.py` | Vault Replication & Disaster Recovery | **AUTHORIZED** |
| E | `are/health_monitor.py` | External Alerting Webhook (Telegram/Email) untuk CRITICAL | **AUTHORIZED** |
| F | `data/historical_crises/` + `are/backtest.py` | Historical Crisis Dataset Ingestion & Replay | **AUTHORIZED** |

---

## 4. BAGIAN A — `are/validation.py` (STATISTICAL RIGOR ENHANCEMENT)

### 4.1 Benjamini-Hochberg FDR Correction
```python
def apply_fdr_correction(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    """
    Benjamini-Hochberg (1995) False Discovery Rate correction.
    100% Python Standard Library. Zero external dependency.
    Returns list of bool: True if hypothesis i survives FDR correction.
    """
```
- Urutkan p-values ascending: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
- Cari indeks terbesar $k$ di mana $p_{(k)} \le \frac{k}{m} \alpha$.
- Kembalikan threshold $p_{(k)}$; semua p-value $\le p_{(k)}$ lolos.

### 4.2 Deflated Sharpe Ratio (DSR) & Probabilistic Sharpe (PSR)
```python
def calculate_deflated_sharpe_ratio(
    sharpe_ratio: float,
    num_trials: int,
    skewness: float,
    kurtosis: float,
    num_observations: int,
    benchmark_sharpe: float = 0.0,
) -> tuple[float, float]:
    """
    Bailey-Lopez de Prado Deflated Sharpe Ratio.
    Returns (deflated_sharpe, p_value).
    100% Python Standard Library via math.erf CDF.
    """

def calculate_probabilistic_sharpe_ratio(
    observed_sharpe: float,
    benchmark_sharpe: float,
    num_observations: int,
    skewness: float,
    kurtosis: float,
) -> float:
    """
    Probabilistic Sharpe Ratio (PSR) — Lopez de Prado (2012).
    100% Python Standard Library.
    """
```

### 4.3 Integrasi ke Governor
Di `are/governor.py`, modifikasi `GovernorEngine.evaluate_promotion()`:
- Terima `candidate_p_values: Optional[list[float]] = None`.
- Lakukan screening FDR terlebih dahulu. Kandidat yang gugur dicatat di `EvidenceLedger` dengan `REJECTED: FDR_MULTIPLE_COMPARISON_BIAS`.

---

## 5. BAGIAN B — `are/copilot.py` (EVIDENCE-BOUND COGNITION)

### 5.1 Evidence Pre-Injection (Fix Blind Spot DELEGASI_030)
Di `ConversationalCopilot._get_current_context()` dan `build_prompt()`:
1. Ambil recent trade anomalies via `self.diagnostics.query_recent_anomalies(event_store=self.event_store, limit=5)`.
2. Ambil recent slippage reports via `self.diagnostics.fetch_all(event_store=self.event_store, limit=5)`.
3. Suntikkan `[EVIDENCE CONTEXT]` terstruktur ke dalam prompt Ollama SEBELUM `User: {message}`.
4. Fail-closed: jika event_store tidak tersedia / query gagal, fallback ke internal deterministic response.

### 5.2 Multi-Step Sub-Querying & Hallucination Detector
1. `generate_reasoned_response()`: Decompose user query $\rightarrow$ query EventStore $\rightarrow$ format synthesis with `file:line` / evidence hash citations.
2. `_verify_factual_consistency()`: Verifikasi klaim angka dalam respon LLM terhadap bukti faktual. Jika angka melenceng $\rightarrow$ BLOCK dan fallback.

---

## 6. BAGIAN C — `tests/are/test_e2e_cognitive_pipeline.py` (7-ORGAN E2E GAUNTLET)

6 skenario pengujian komprehensif:
1. `test_full_7_organ_happy_path_lifecycle`: Scraper $\rightarrow$ Validate $\rightarrow$ Purify $\rightarrow$ Backtest $\rightarrow$ FDR $\rightarrow$ MC $\rightarrow$ Promote $\rightarrow$ Trade $\rightarrow$ Copilot Explain $\rightarrow$ Health OK.
2. `test_copilot_ollama_prompt_includes_evidence`: Membuktikan prompt Ollama memuat detail anomali slippage dan hash evidence.
3. `test_fdr_rejects_noise_candidates`: Membuktikan 100 kandidat dengan p-hacking disaring oleh Benjamini-Hochberg.
4. `test_overfitted_alpha_killed_by_monte_carlo_e2e`: Lucky sequence (95 trade rugi + 1 trade untung) ditolak oleh Monte Carlo & Governor.
5. `test_toxic_market_and_csk_circuit_breaker_e2e`: Spread 10x dinetralisir, latensi 6000ms memicu EMERGENCY_FLAT.
6. `test_vault_self_healing_under_pipeline_load`: Database SQLite dirusak $0xDEADBEEF$, verify_and_heal() memulihkan 100% dari witness.

---

## 7. BAGIAN D — `are/storage.py` (VAULT REPLICATION & DISASTER RECOVERY)

1. `VaultReplicator`:
   - Copy `primary_db_path` dan `witness_jsonl_path` ke `backup_dir`.
   - Hitung SHA-256 dan tulis `manifest_{timestamp}.json`.
   - Verifikasi read-back check.
   - Retention policy: 7 snapshot harian + 4 snapshot mingguan.

---

## 8. BAGIAN E — `are/health_monitor.py` (EXTERNAL ALERTING MINIMUM)

1. `send_critical_alert()`:
   - Mengirim alert via Telegram Bot API / Webhook via `urllib.request`.
   - Trigger HANYA untuk `CRITICAL`, `EMERGENCY_FLAT`, `Vault Mismatch`, atau `MT5 Heartbeat Silence > 60s`.
   - Konfigurasi via `AHFMES_ALERT_WEBHOOK_URL`. Fail-closed (jika tidak diset, hanya log ke EventStore).

---

## 9. BAGIAN F — HISTORICAL CRISIS REPLAY ENGINE

1. `TOOLS/fetch_historical_crises.py`:
   - Download data krisis historis: 2008 GFC, COVID 2020, CHF 2015 Depeg.
   - Purifikasi via `DataPurifier`, simpan di `data/historical_crises/purified/`.
2. `BacktestEngine.run_crisis_replay()`:
   - Jika drawdown strategi $> 50\%$ pada salah satu krisis historis $\rightarrow$ Governor REJECT.

---

## 10. KRITERIA TERIMA (Fail-Closed, Semuanya Wajib)

```text
□ 1.  FDR Benjamini-Hochberg terimplementasi murni stdlib — PASS
□ 2.  Deflated Sharpe Ratio terimplementasi murni stdlib — PASS
□ 3.  Probabilistic Sharpe Ratio terimplementasi murni stdlib — PASS
□ 4.  Governor menolak batch noise via FDR — PASS
□ 5.  Copilot prompt memuat fakta EvidenceLedger — PASS
□ 6.  Hallucination Detector berfungsi — PASS
□ 7.  6 skenario E2E Gauntlet 100% PASS
□ 8.  Vault Replication berfungsi — PASS
□ 9.  Vault Self-Healing berfungsi — PASS
□ 10. External Alerting tertrigger pada CRITICAL — PASS
□ 11. Crisis Dataset tersedia (min. 3 krisis) — PASS
□ 12. Crisis Replay menolak strategi bangkrut — PASS
□ 13. 352 test baseline tetap 100% PASS (Zero Regression)
□ 14. Total test suite >= 364+ PASS
□ 15. Commit: "feat(hardening): DELEGASI_035 — FDR, DSR, Evidence RAG, E2E Gauntlet, Vault DR, Alerting, Crisis Replay (364+ tests)"
□ 16. Push ke origin/main, working tree clean
```

---

## 11. RESOLUSI IAQ (IMPLEMENTABILITY QUESTIONS)

| ID | Pertanyaan | Resolusi Resmi Lead Architect |
|---|---|---|
| IAQ-035-01 | Apakah `yfinance` diizinkan di `TOOLS/`? | **YA, HANYA di `TOOLS/` untuk one-time seeding dataset**. Modul inti `are/` tetap 100% stdlib. |
| IAQ-035-02 | Di mana token Telegram disimpan? | **Environment Variable `AHFMES_ALERT_WEBHOOK_URL` / `TELEGRAM_BOT_TOKEN`**. Fail-closed. |
| IAQ-035-03 | Format penyimpanan data krisis? | **`.parquet` (Polars) dengan fallback `.jsonl`**. |
| IAQ-035-04 | Akurasi DSR via `math.erf`? | **`math.erf` 100% eksak untuk standard normal CDF ($\Phi(z) = 0.5 \times (1 + \text{erf}(z/\sqrt{2}))$)**. Zero scipy dependency. |
