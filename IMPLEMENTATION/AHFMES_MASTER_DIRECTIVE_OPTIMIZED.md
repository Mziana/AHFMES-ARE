# AHFMES — MASTER AUTONOMOUS ENGINEERING DIRECTIVE
## FINALIZATION → RESEARCH-GRADE BACKTEST READINESS

Anda bekerja pada repository:

**`https://github.com/Mziana/AHFMES-ARE`**

Tujuan Anda bukan sekadar memperbaiki beberapa bug.

Tujuan Anda adalah membawa repository ini dari kondisi aktual saat Anda mulai bekerja menjadi:

> **RESEARCH-GRADE BACKTEST ENGINE YANG DAPAT MENJALANKAN BACKTEST SECARA REPRODUCIBLE, LEAKAGE-RESISTANT, STATISTICALLY HONEST, EVIDENCE-BINDING, FAIL-CLOSED, DAN DAPAT DIAUDIT END-TO-END.**

Anda bekerja sebagai **senior quantitative systems engineer + adversarial auditor + software architect**.

Jangan menjadi yes-man.

---

# 0. ATURAN MUTLAK

## 0.1 Audit kode aktual, bukan dokumentasi

Pada awal pekerjaan:

1. checkout/fetch repository terbaru;
2. identifikasi HEAD aktual;
3. baca struktur repository;
4. inventory seluruh source Python;
5. inventory seluruh test;
6. inventory konfigurasi;
7. inventory artifact/data directory;
8. baca dependency files;
9. baca CI;
10. baca README dan governance hanya sebagai konteks.

Dokumentasi **BUKAN source of truth**.

Jika dokumentasi mengatakan:

> RESOLVED

tetapi kode mengatakan belum resolved:

**anggap BELUM RESOLVED.**

Jika test mengatakan PASS tetapi test tidak membuktikan kontrak:

**anggap BELUM TERBUKTI.**

Jika commit message mengatakan fixed:

**verifikasi implementasinya sendiri.**

---

# 0.2 Jangan mengejar test count

Jangan gunakan:

> "500 tests passed"

sebagai bukti kesiapan.

Target utama:

> Tidak boleh ada jalur yang menghasilkan PASS/GO ketika evidence yang mendasarinya salah, hilang, korup, berasal dari dataset berbeda, parameter berbeda, split berbeda, atau perhitungan yang tidak dapat direproduksi.

Test count hanyalah indikator sekunder.

---

# 0.3 Tidak boleh silent failure

Cari dan eliminasi pola seperti:

```python
except:
    pass
```

```python
except Exception:
    pass
```

```python
return True
```

ketika operasi kritis sebenarnya gagal.

Untuk operasi non-critical boleh graceful degradation jika kontraknya memang demikian.

Untuk operasi berikut, failure HARUS terlihat dan mempengaruhi verdict:

- dataset loading
- dataset hashing
- split creation
- WFO
- parameter selection
- OOS evaluation
- DSR
- holdout evaluation
- evidence generation
- evidence persistence
- evidence verification
- final gate
- critical risk calculation

---

# 0.4 Jangan membuat fake implementation

Dilarang menyelesaikan requirement dengan:

- boolean flag;
- timestamp saja;
- placeholder;
- mock yang tidak menguji komponen;
- hardcoded success;
- synthetic result yang dipresentasikan sebagai real result;
- metadata yang menyatakan evaluation selesai tanpa computation;
- test yang hanya memeriksa bahwa function dipanggil.

Setiap status `PASS`, `VALID`, `EVALUATED`, `VERIFIED`, `GO` harus memiliki evidence aktual.

---

# 0.5 Jangan mengubah scientific meaning demi membuat test pass

Jika test bertentangan dengan kontrak ilmiah:

1. identifikasi masalah;
2. tentukan kontrak yang benar;
3. ubah test dan implementasi secara konsisten;
4. dokumentasikan alasan.

Jangan melakukan patch kosmetik agar CI hijau.

---

# 0.6 FAKTA AUDIT AKTUAL (HEAD `db2c39f`, hasil clone + grep langsung — BUKAN dari README/governance)

Ini bukan starting point kosong. Berikut hasil audit nyata yang sudah dilakukan terhadap
`https://github.com/Mziana/AHFMES-ARE` pada HEAD `db2c39f`. Gunakan sebagai entri awal
remediation queue di Phase 1 (Section 2). Jangan mulai dari nol, dan jangan percaya angka di
dashboard governance repo ini sampai Anda re-derive sendiri dari kode:

```text
Python source files : 161
Test files           : 73
Markdown governance  : 427   <-- risiko integritas tersendiri, lihat 0.9

except Exception: <blok kosong berikutnya>  : 80 kemunculan di are/
bare `pass`                                  : 42 kemunculan di are/
`return True` (gaya hardcoded)                : 44 kemunculan di are/
TODO / FIXME literal                          : 0 (jangan berhenti di sini — cek juga kata seperti
                                                    "sementara", "placeholder", "belum", "simplified")
```

File dengan `except Exception:` diikuti blok kosong yang WAJIB diverifikasi manual dulu (bukan
diasumsikan aman) karena namanya menyentuh area critical-path menurut Section 0.3 di atas:

```text
are/scientific.py      <- kandidat kuat rumah DSR/statistical validation. SILENT EXCEPT DI FILE
                            INI berarti kegagalan perhitungan DSR berpotensi tidak kelihatan —
                            pelanggaran langsung Section 0.3 jika benar.
are/coordinator.py
are/copilot.py
are/dashboard.py        <- UI; cek apakah dashboard menjadi sumber kebenaran (dilarang Section 49)
are/health_monitor.py   (3 lokasi terpisah pada file yang sama)
are/mt5_server.py       <- live execution bridge; silent-except di sini = risiko silent order failure
are/reliability.py
are/runner.py
```

Perintah audit berikut adalah LANGKAH LITERAL PERTAMA Phase 1 — jalankan sebelum membaca dokumen
governance apa pun:

```bash
grep -rn -B2 "except Exception:" are/ | grep -B2 "pass$"
grep -rn "return True" are/*.py
grep -c "" are/*.py | sort -t: -k2 -n -r   # file terbesar duluan, biasanya paling berisiko
```

---

# 0.7 PEMETAAN NAMA GENERIK → FILE NYATA (WAJIB DIVERIFIKASI, JANGAN DITEBAK)

Section 1–56 di dokumen ini menyebut konsep generik (dataset canonical, split manifest, WFO engine,
DSR, holdout engine, evidence, independent verifier). Nama file aktual di repo TIDAK memakai istilah
itu secara langsung. Sebelum menyentuh kode apa pun di Phase 1, buat tabel pemetaan aktual — tabel
di bawah ini cuma kandidat awal untuk mempercepat pencarian, BUKAN kesimpulan:

```text
KONSEP DIREKTIF               KANDIDAT FILE (VERIFIKASI ISI, JANGAN PERCAYA NAMA SAJA)
------------------------      ----------------------------------------------------
dataset identity/hash         are/canonical.py, are/hasher.py, are/data_loader.py
data purification             are/data_pipeline.py
split manifest / WFO          are/strategy_engine.py, are/backtest.py, are/backtest_enhanced.py
                               (TIDAK ADA file bernama wfo.py — cari fungsi/class di dalam file di
                               atas)
parameter selection/champion  are/champion.py, are/opportunity_engine.py, are/evolution.py
OOS evaluation                are/backtest.py / are/backtest_enhanced.py (verifikasi terpisah dari IS)
DSR / statistical validation  are/scientific.py, are/validation.py
crisis / stress replay        are/replay.py
holdout engine                CARI DI DALAM are/validation.py atau are/evidence.py — TIDAK ADA nama
                               file eksplisit "holdout" di top-level are/. Kemungkinan besar titik
                               lemah nyata (bandingkan dengan tuntutan Section 17).
evidence / provenance         are/evidence.py, are/hasher.py
independent verifier          BELUM TERIDENTIFIKASI di inventory top-level. Jika setelah pencarian
                               menyeluruh memang tidak ada implementasi terpisah dari producer
                               (lihat larangan common-mode bug di Section 21), ini otomatis P0,
                               bukan P2.
preflight / fail-closed gate  are/preflight.py
execution / MT5 bridge        are/mt5_feed.py, are/mt5_gateway.py, are/mt5_runner.py, are/mt5_server.py
```

Output wajib Phase 1: isi ulang tabel di atas dengan nama fungsi/class aktual + nomor baris, bukan
hanya nama file. Setiap konsep direktif yang tidak punya implementasi sama sekali naik jadi temuan
P0 di remediation queue, tidak boleh didiamkan sampai fase belakang.

---

# 0.8 JANGAN PERCAYA GOVERNANCE DASHBOARD REPO INI — ALASAN SPESIFIK

`README.md` dan `PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md` menyatakan 7 "organ" berstatus
`SOFTWARE_VERIFIED`, Fase 1–4 `FULLY_CLOSED` (@400 tests), dan hanya Fase 5 (live/paper) yang
`LOCKED`. Perlakukan seluruh klaim ini sebagai hipotesis belum terbukti, dengan alasan konkret,
konsisten dengan prinsip Section 0.1 di atas (dokumentasi bukan source of truth):

1. Repo punya riwayat 204 commit dan 9 dokumen `DELEGASI_00X` di folder `ENGINEERING/` — pola ini
   konsisten dengan siklus berulang "audit → klaim selesai → audit lagi menemukan masalah baru"
   yang belum pernah konvergen ke status produksi. `ENGINEERING/ARE1_SELF_AUDIT_REPORT.md` dan
   `ENGINEERING/ARCH_DEBT_REGISTER.md` yang sudah ada berarti audit sebelumnya SUDAH menemukan
   utang teknis — cek apakah utang itu benar-benar ditutup atau cuma dipindah status ke dokumen lain.
2. `PROJECT_GOVERNANCE/RED_TEAM_HARDENING` masih berstatus ACTIVE dengan residu `RES-COG-03`
   di-GATE menunggu stability run 7×24 jam — klaim "FULLY_CLOSED" untuk fase-fase sebelumnya berdiri
   di atas asumsi yang belum divalidasi ulang setelah temuan red-team baru.
3. Silent-except di `are/scientific.py` (kandidat rumah DSR, lihat 0.6) berkontradiksi langsung
   dengan klaim "Organ 2 (Sistem Kekebalan): SOFTWARE_VERIFIED (DSR, WFA, Corr Gate)" — kalau
   perhitungan DSR bisa gagal diam-diam, ia bukan "verified", ia "belum terbukti gagal-tertutup".

Jangan menghapus dashboard ini secara sepihak di awal. Audit dulu, buktikan/bantah tiap barisnya
dengan evidence dari kode (ikuti Section 0.1–0.5), baru revisi dashboard sesuai Section 50.

---

# 0.9 KONSOLIDASI DOKUMENTASI ADALAH BAGIAN DARI SCOPE, BUKAN OPSIONAL

Repo ini punya 427 file markdown governance. Ini sendiri adalah risiko integritas: semakin banyak
tempat untuk menulis "selesai" atau "verified", semakin mudah audit berikutnya keliru percaya pada
salah satu dari file-file tersebut alih-alih kode. Perlakukan ini sebagai bagian eksplisit dari
Phase 16 (Documentation Reconciliation, Section 50) dan Execution Protocol (Section 52):

- Inventarisasi seluruh 427 file markdown; klasifikasikan: (a) canonical/masih relevan, (b)
  historis/arsip, (c) kontradiktif dengan kode aktual, (d) duplikat.
- Konsolidasikan menjadi SATU file status kanonik, misalnya `PROJECT_GOVERNANCE/CURRENT_STATUS.md`,
  dengan setiap klaim status merujuk langsung ke evidence artifact atau commit hash — bukan ke
  dokumen lain.
- Pindahkan sisanya ke folder `ARCHIVE/` dengan catatan tanggal. Jangan dihapus (audit trail tetap
  berguna), tapi jangan lagi diperlakukan sebagai source of truth oleh siapa pun di pekerjaan
  berikutnya.

---

# 0.10 PROGRESS LEDGER — MEKANISME KELANGSUNGAN PEKERJAAN

Scope pekerjaan ini besar: 161 file produksi, 16 fase (Section 52), matriks adversarial penuh
(Section 31/33). Supaya pekerjaan benar-benar bisa "jalan sampai selesai" tanpa kehilangan jejak
di titik mana pun ia berhenti (baik karena batas resource, baik karena menunggu keputusan
arsitektur), pelihara SATU file state tunggal — bukan bagian dari 427 file di 0.9 — bernama
`PROGRESS_LEDGER.md` di root repository:

```yaml
head_commit: <hash>
current_phase: <1-16, mengacu ke Execution Protocol Section 52>
phase_status: IN_PROGRESS | BLOCKED | DONE

remediation_queue:
  - id: P0-001
    file: are/scientific.py
    finding: "except Exception: pass di baris 136, membungkus perhitungan DSR"
    severity: P0
    status: OPEN | FIXED | VERIFIED
    evidence_of_fix: <commit hash / nama test yang membuktikan>

verified_mappings:      # hasil Section 0.7, diisi progresif
  wfo_engine: <file:baris atau "BELUM DITEMUKAN">
  holdout_engine: <file:baris atau "BELUM DITEMUKAN">
  independent_verifier: <file:baris atau "BELUM DITEMUKAN">

regression_baseline:
  last_known_good_commit: <hash>
  test_count_at_baseline: <angka — indikator sekunder saja, lihat Section 0.2>

blocked_reason: "<jika phase_status BLOCKED, kenapa, dan keputusan apa yang dibutuhkan>"
next_action: "<instruksi eksplisit satu-dua kalimat untuk melanjutkan>"
```

Aturan wajib, tunduk pada prinsip evidence-binding yang sama seperti seluruh dokumen ini:

1. Ledger dibaca di awal setiap unit kerja, sebelum dokumen governance mana pun — ledger ini,
   bukan 427 file di 0.9, adalah satu-satunya sumber kebenaran tentang "sedang di mana".
2. Ledger ditulis ulang setiap kali ada perubahan status berarti — jangan biarkan status berubah
   di kepala tanpa tercatat; itu setara "partial run" tak tercatat di Section 42.
3. Entri `FIXED`/`VERIFIED` di ledger WAJIB punya `evidence_of_fix` yang menunjuk ke commit/test
   nyata — ledger tunduk pada Section 0.4 (jangan fake implementation) sama seperti evidence
   ilmiah lainnya di sistem ini.
4. Jika ledger mengklaim sesuatu `VERIFIED` tapi kode tidak mendukung klaim itu, ini prioritas
   tertinggi berikutnya: perbaiki ledger DAN cari kenapa klaim itu bisa masuk tanpa bukti.

Ini adalah implementasi konkret dari Section 53 (Autonomous Loop) dan Section 54 (Stop Conditions)
di bawah — loop AUDIT→FIND→CLASSIFY→FIX→TEST→ATTACK→FIX→REGRESSION→NEXT FINDING berjalan dengan
ledger ini sebagai pencatat state-nya, bukan sebagai ingatan implisit.

---

# 1. MISSION

Bangun dan verifikasi pipeline berikut:

```text
DATA SOURCE
    ↓
DATA INGESTION
    ↓
DATA PURIFICATION
    ↓
CANONICAL DATASET IDENTITY
    ↓
SPLIT MANIFEST
    ↓
TRAIN / PURGE / WFO
    ↓
PARAMETER SELECTION
    ↓
OOS EVALUATION
    ↓
POOLED OOS RETURNS
    ↓
DSR / STATISTICAL VALIDATION
    ↓
CRISIS / ROBUSTNESS / SENSITIVITY
    ↓
LOCKED HOLDOUT
    ↓
HOLDOUT EVALUATION
    ↓
INDEPENDENT VERIFICATION
    ↓
FINAL GATE
    ↓
IMMUTABLE BACKTEST ARTIFACT
    ↓
REPRODUCIBILITY / REPLAY
```

Tidak boleh ada stage yang hanya ada secara nominal.

---

# 2. PHASE 1 — COMPLETE REPOSITORY RECONNAISSANCE

Sebelum mengubah kode, lakukan audit:

### Source inventory

Identifikasi:

- backtest engine
- WFO
- validation
- DSR
- preflight
- holdout
- orchestrator
- integrity
- artifact management
- dataset management
- strategy interface
- execution model
- Monte Carlo
- crisis replay
- risk model
- persistence
- independent verifier
- tests
- CLI/API
- configuration

### Cari secara global:

```text
TODO
FIXME
pass
except Exception
except:
hardcoded
time.time
random
np.random
seed
NaN
Inf
json.dumps
hash
sha256
assert
mock
MagicMock
patch
return True
return False
is_valid
evaluated
verified
passed
GO
NO_GO
INVALID
```

Audit setiap hasilnya.

---

# 3. PHASE 2 — DEFINE CANONICAL DATA CONTRACT

Buat satu canonical representation untuk dataset.

Dataset identity HARUS mencakup seluruh informasi yang relevan terhadap backtest.

Minimal:

```text
schema
column names
column order
dtypes
row order
all relevant values
timeframe
symbol
source identity
data range
purification version
dataset protocol version
```

Jangan menggunakan:

```python
hash(str(len(data)))
```

Jangan menggunakan hanya:

```text
timestamp + price + volume
```

jika strategy/execution membutuhkan:

```text
bid
ask
spread
tick volume
real volume
execution fields
```

Gunakan canonical serialization → bytes → SHA-256.

Harus deterministic lintas execution.

Tambahkan test:

- satu row berubah → hash berubah;
- volume berubah → hash berubah;
- bid/ask berubah → hash berubah;
- dtype berubah → hash berubah;
- column order berubah → canonical contract menangani sesuai policy;
- row order berubah → hash berubah jika order merupakan bagian contract;
- dataset identik → hash identik.

---

# 4. PHASE 3 — CANONICAL SPLIT MANIFEST

Buat split manifest immutable.

Manifest minimal:

```text
run_id
dataset_hash
symbol
timeframe
train_start
train_end
purge_start
purge_end
oos_start
oos_end
holdout_start
holdout_end
warmup_bars
purge_bars
label_horizon_bars
split_protocol_version
split_hash
```

Invariant:

```text
purge_bars >= label_horizon_bars
```

Tidak boleh overlap antara:

```text
TRAIN
PURGE
OOS
HOLDOUT
```

Warmup boleh mengambil history sebelum OOS, tetapi warmup tidak boleh masuk ke OOS metric.

Tambahkan test untuk boundary:

- exact boundary;
- one-bar overlap;
- purge terlalu kecil;
- holdout contamination;
- warmup contamination;
- duplicate timestamps;
- non-monotonic timestamps.

---

# 5. PHASE 4 — STRATEGY CONTRACT

Strategy tidak boleh bergantung pada magic DataFrame columns seperti:

```text
_param_x
```

Parameter harus explicit.

Gunakan contract seperti:

```python
strategy_factory(params)
```

atau:

```python
strategy.run(data, params)
```

WFO candidate:

```text
candidate params
      ↓
strategy instance
      ↓
train evaluation
```

Bukan:

```text
candidate params
      ↓
inject dataframe
      ↓
semoga strategy membaca
```

Tambahkan invariant:

### Parameter sensitivity

Untuk parameter yang seharusnya memengaruhi strategy:

```text
params A != params B
       ↓
strategy behavior harus berbeda
```

Jika semua candidate menghasilkan output identik:

```text
WFO INVALID
```

Jangan melakukan optimization palsu.

---

# 6. PHASE 5 — WFO ENGINE

Audit WFO secara matematis.

Pastikan setiap fold memiliki:

```text
TRAIN
PURGE
OOS
```

dan:

```text
OOS_i ∩ OOS_j = ∅
```

untuk fold non-overlapping.

Pastikan:

```text
selection menggunakan IS saja
```

Tidak boleh ada informasi OOS masuk ke selection.

Per candidate simpan:

```text
params
IS metrics
IS Sharpe
IS DD
IS turnover
```

Winner:

```text
winner_params
winner_IS_score
```

Runner-up:

```text
runner_up_params
runner_up_IS_score
```

Tie:

```text
tie_count
tie_break_rule
```

Tie-breaking harus deterministic.

---

# 7. CRITICAL WFO EQUITY RULE

Jangan menghitung pooled equity dengan reset capital pada setiap fold.

Salah:

```text
fold 1 → capital 10000
fold 2 → capital 10000
fold 3 → capital 10000
```

Benar:

```text
initial capital
     ↓
OOS fold 1
     ↓
ending equity fold 1
     ↓
OOS fold 2
     ↓
ending equity fold 2
     ↓
...
```

Pooled returns:

```text
concatenate OOS return series
```

Pooled equity:

```text
compound continuously
```

Tambahkan invariant dengan fixture deterministic yang dapat menghitung expected result secara manual.

---

# 8. WFO EVIDENCE

Buat canonical:

```text
WFOFoldEvidence
WFOEvidence
```

`WFOEvidence` minimal harus memuat:

```text
run_id
dataset_hash
strategy_hash
data boundaries

folds[]

parameter_family_size
evaluation_count
effective_trial_count
trial_count_method

warmup_bars
purge_bars
label_horizon_bars
timeframe_seconds

training_overlap_ratio
oos_overlap_ratio

pooled_oos_returns
pooled_oos_equity
pooled_oos_sharpe
pooled_oos_return
pooled_oos_max_drawdown

mean_fold_oos_sharpe
median_fold_oos_sharpe
worst_fold_oos_sharpe
std_fold_oos_sharpe

mean_is_sharpe
wfe_ratio

provenance_hash
```

Jika field risk-bearing ada di evidence, field tersebut harus masuk provenance.

---

# 9. PROVENANCE HASH

Hash tidak boleh hanya mencakup:

```text
winner_params
oos_sharpe
pooled_sharpe
```

Hash HARUS mencakup seluruh risk-bearing evidence:

```text
dataset identity
strategy identity
parameter selection
fold boundaries
purge
OOS boundaries
returns
equity
Sharpe
return
max DD
trial count
WFE
timeframe
protocol version
```

Gunakan canonical JSON/bytes.

Reject:

```text
NaN
Infinity
non-finite values
non-canonical types
```

jika field tersebut tidak secara eksplisit didukung contract.

---

# 10. EVIDENCE PERSISTENCE

Evidence persistence adalah critical path.

Flow:

```text
compute evidence
      ↓
canonical serialize
      ↓
write atomically
      ↓
read back
      ↓
recompute hash
      ↓
compare
      ↓
PASS
```

Jika persistence gagal:

```text
INVALID
```

Tidak boleh:

```python
except Exception:
    pass
```

Pisahkan:

```text
summary artifact
```

dan:

```text
canonical evidence artifact
```

Jangan menamai summary sebagai full evidence.

---

# 11. OOS EVALUATION

OOS harus menggunakan:

```text
winner_params
```

dari WFO.

Tidak boleh melakukan re-optimization di OOS.

Pastikan OOS evaluation menghasilkan raw:

```text
returns
equity
trades
turnover
costs
```

dan metrics dihitung dari raw evidence.

Test:

> mutasi OOS data tidak boleh mengubah winner parameters.

---

# 12. DSR

DSR harus terikat langsung ke canonical WFOEvidence.

Observed Sharpe:

```text
pooled_oos_sharpe
```

Observations:

```text
len(pooled_oos_returns)
```

Trials:

```text
effective_trial_count
```

Pastikan definisi trial konsisten.

Jangan ada:

```text
num_trials = 10
```

Jangan ada secondary calculation yang diam-diam menggunakan:

```text
fold_count × grid_size
```

sementara canonical evidence menggunakan definisi lain.

Pilih satu scientifically defensible definition.

Expose:

```text
trial_count_method
```

dan pastikan DSR menggunakan field yang sama.

Test sensitivity:

```text
trial count berubah
→ DSR berubah sesuai formula
```

Test provenance:

```text
claimed Sharpe ≠ recomputed Sharpe
→ INVALID
```

---

# 13. STATISTICAL VALIDATION

Audit:

- Sharpe
- PSR
- DSR
- confidence interval
- ruin probability
- terminal ruin
- path ruin
- drawdown
- tail metrics
- sample size
- multiple testing

Pastikan:

```text
path ruin != terminal ruin
```

Jangan menggunakan integer truncation untuk percentile.

Gunakan definisi percentile/order statistic yang eksplisit dan deterministic.

Semua probability metrics harus memiliki uncertainty interval jika contract mengharuskannya.

---

# 14. MONTE CARLO

Current block bootstrap boleh digunakan jika contract mengizinkan.

Pastikan:

```text
block bootstrap
```

benar-benar mempertahankan urutan dalam block.

Boundary wrapping harus valid.

Tambahkan:

```text
seed
RNG algorithm
simulation count
method
block size
```

ke evidence.

RNG metadata harus benar-benar digunakan oleh engine.

Metadata seed tanpa actual deterministic RNG binding tidak dianggap reproducibility.

---

# 15. CRISIS / STRESS TEST

Audit seluruh crisis scenarios.

Pastikan crisis replay menggunakan:

```text
same strategy
same execution model
same cost model
same risk model
```

yang sesuai dengan production/backtest contract.

Jangan membuat crisis result dengan formula yang berbeda tanpa disclosure.

Setiap scenario:

```text
dataset identity
scenario identity
parameters
execution costs
returns
equity
DD
result
```

harus dapat diaudit.

---

# 16. MICROSTRUCTURE MODEL

Backtest harus memperhitungkan:

```text
spread
slippage
commission
turnover
```

Jika model dinamis:

```text
market condition
spread regime
volatility regime
```

harus dapat memengaruhi cost sesuai contract.

Reject negative friction.

Reject:

```text
NaN
Inf
```

pada parameter cost.

Pastikan:

```text
zero friction
```

tetap backward-compatible dengan gross return.

---

# 17. HOLDOUT — CRITICAL

Bangun `HoldoutEvaluationEngine` nyata.

Jangan hanya:

```python
holdout_evaluated = True
```

Jangan hanya mengubah state:

```python
state = EVALUATED
```

Evaluation harus benar-benar:

```text
locked holdout data
      ↓
selected strategy
      ↓
selected parameters
      ↓
execution simulation
      ↓
raw returns
      ↓
equity
      ↓
metrics
      ↓
HoldoutEvidence
```

Holdout TIDAK boleh:

```text
optimize
select parameters
tune threshold
modify strategy
```

Parameter harus berasal dari WFO dan sudah frozen.

---

# 18. HOLDOOUT EVIDENCE

Buat:

```text
HoldoutEvidence
```

minimal:

```text
run_id
dataset_hash
split_hash
strategy_hash
wfo_provenance_hash
selected_parameter_hash

returns
equity

Sharpe
return
max_drawdown

trade_count
turnover
costs

provenance_hash
```

Holdout harus terikat cryptographically/logically ke WFO.

Jika:

```text
selected parameters
```

berbeda dari WFO:

```text
INVALID
```

Jika:

```text
dataset hash
```

berbeda:

```text
INVALID
```

Jika:

```text
split hash
```

berbeda:

```text
INVALID
```

---

# 19. HOLDOUT LOCK

Holdout state harus persistent.

Jangan hanya:

```python
self._splits = {}
```

di memory.

Buat persistent manifest.

Restart process tidak boleh membuka kembali holdout secara diam-diam.

State minimal:

```text
CREATED
LOCKED
EVALUATED
VERIFIED
```

Tidak boleh:

```text
VERIFIED → MODIFY
```

Tidak boleh:

```text
EVALUATED → change params
```

---

# 20. LEAKAGE FIREWALL

Jangan menjadikan correlation sebagai proof.

Buat temporal contract.

Untuk setiap data dependency:

```text
feature_time
    <=
decision_time
    <
execution_time
```

Label:

```text
decision_time
<
label_end
```

Purge harus memutus overlap label.

Tambahkan adversarial fixtures:

- future feature;
- future label;
- future close;
- future-derived indicator;
- future volume;
- future spread;
- future execution price.

Semua harus ditolak.

---

# 21. INDEPENDENT VERIFIER

Verifier harus independen secara semantic.

Ia harus membaca artifact, kemudian menghitung ulang:

```text
Sharpe
return
equity
max DD
trade count
turnover
cost
trial count
DSR
```

Jangan hanya memeriksa:

```text
claimed == claimed
```

Idealnya critical metric menggunakan implementation path yang tidak identik 100% dengan producer agar common-mode bugs lebih sulit lolos.

Verifier harus mendeteksi:

```text
tampered returns
tampered equity
tampered DD
tampered Sharpe
tampered trial count
tampered params
tampered dataset hash
```

---

# 22. FINAL GATE

Final Gate tidak boleh menerima raw scalar injection seperti:

```text
wf_score=0.80
num_trials=10
```

Final Gate harus menerima evidence.

Minimal:

```text
WFOEvidence
OOS evidence
StatisticsEvidence
CrisisEvidence
HoldoutEvidence
VerificationEvidence
```

Gate harus mempunyai empat disposition:

```text
INVALID
FAIL
BORDERLINE
PASS
```

## INVALID

Evidence chain rusak:

```text
missing
corrupt
hash mismatch
purge violation
missing OOS
missing holdout
missing DSR
verification failure
```

## FAIL

Evidence valid tetapi performance tidak memenuhi threshold.

## BORDERLINE

Evidence valid dan minimum threshold tercapai tetapi robustness/stability belum cukup.

## PASS

Semua required gates memenuhi kontrak.

Tidak boleh:

```text
missing evidence → PASS
```

---

# 23. FINAL GATE MUST BE DERIVATIVE

Jangan simpan verdict sebagai truth.

Truth:

```text
raw evidence
```

Derived:

```text
PASS/FAIL
```

Jika evidence berubah:

```text
verdict harus berubah / menjadi INVALID
```

Test ini wajib.

---

# 24. BACKTEST ARTIFACT

Setiap backtest harus menghasilkan immutable artifact bundle:

```text
run.json
dataset_manifest.json
split_manifest.json

wfo_evidence.json
oos_evidence.json
statistics_evidence.json
crisis_evidence.json
holdout_evidence.json
verification_evidence.json

final_gate.json

metrics.json
trades.json
returns.json

provenance.json
```

Tambahkan:

```text
artifact_manifest.json
```

yang berisi hash setiap artifact.

---

# 25. REPRODUCIBILITY

Satu run harus dapat direproduksi.

Record:

```text
git commit
code version
dataset hash
split hash
strategy hash
parameter hash
random seed
RNG algorithm
Python version
dependency versions
protocol versions
configuration
```

Run kedua dengan input sama harus menghasilkan:

```text
same evidence
same metrics
same provenance
same final gate
```

Jika timestamp memang bukan bagian scientific identity:

> timestamp tidak boleh mengubah result hash.

---

# 26. DETERMINISM

Jalankan minimal:

```text
same dataset
same strategy
same params
same seed
same config
```

dua kali.

Bandingkan:

```text
raw returns
equity
trades
metrics
evidence
hash
final verdict
```

Harus identik.

Test telemetry ON/OFF tidak boleh mengubah scientific state.

---

# 27. TIMEOUT / RESOURCE CONTROL

Audit timeout.

Post-hoc check seperti:

```python
result = function()
if elapsed > timeout:
```

bukan hard timeout.

Untuk operation berat seperti WFO:

gunakan worker/process isolation bila diperlukan sehingga parent dapat benar-benar menghentikan computation yang melewati budget.

Pastikan:

```text
timeout
→ terminate
→ cleanup
→ INVALID/FAILED
```

bukan:

```text
timeout
→ tetap bekerja
→ akhirnya selesai
```

---

# 28. MEMORY / SCALE

Audit:

- dataset besar;
- WFO grid besar;
- Monte Carlo besar;
- raw return persistence;
- artifact serialization.

Cari:

```text
list raksasa
string conversion
duplicate dataframe
unbounded memory
```

Optimalkan hanya jika tidak mengubah semantics.

Untuk artifact besar:

gunakan streaming/chunking bila diperlukan.

---

# 29. NUMERICAL ROBUSTNESS

Semua critical calculation harus menangani:

```text
NaN
Inf
-Inf
None
empty series
single observation
zero variance
zero denominator
negative equity
100% loss
return <= -100%
```

Tidak boleh menghasilkan silent NaN lalu tetap PASS.

Definisikan policy:

```text
invalid input
→ INVALID
```

jika metric tidak meaningful.

---

# 30. TEST ARCHITECTURE

Jangan hanya menambah unit tests.

Buat empat lapisan:

## Layer 1 — Unit

Formula dan primitive.

## Layer 2 — Invariant

Contract internal.

## Layer 3 — End-to-End

```text
dataset → gate
```

## Layer 4 — Adversarial corruption

Sengaja rusakkan evidence dan pastikan gate menolak.

---

# 31. REQUIRED ADVERSARIAL TEST MATRIX

Wajib ada test untuk:

```text
missing dataset
corrupt dataset
dataset hash mutation
split mutation
future data
future label
purge violation

parameter mutation
parameter ignored by strategy

OOS mutation
OOS overlap
OOS missing

trial count mutation
DSR mutation
Sharpe mutation

equity mutation
DD mutation

holdout mutation
holdout parameter mutation
holdout dataset mutation

evidence deletion
evidence persistence failure
evidence hash mismatch

NaN
Inf
None
zero variance

RNG mutation
seed mutation

timeout
crash
partial artifact
```

Expected behavior harus eksplisit.

---

# 32. GOLDEN DATASET

Buat dataset fixture kecil yang seluruh expected result-nya diketahui.

Pipeline:

```text
Golden Dataset
 ↓
Split
 ↓
WFO
 ↓
Selection
 ↓
OOS
 ↓
DSR
 ↓
Crisis
 ↓
Holdout
 ↓
Verifier
 ↓
Final Gate
```

Gunakan golden dataset untuk regression.

---

# 33. CORRUPTION QUALIFICATION

Setelah golden pipeline PASS, lakukan deliberate corruption.

Wajib:

| Attack | Expected |
|---|---|
| mutate dataset | INVALID |
| mutate split | INVALID |
| mutate winner params | INVALID |
| mutate OOS returns | INVALID |
| mutate OOS Sharpe | INVALID |
| mutate OOS DD | INVALID |
| mutate pooled equity | INVALID |
| mutate trial count | INVALID |
| mutate DSR | INVALID |
| mutate holdout returns | INVALID |
| mutate holdout params | INVALID |
| delete evidence | INVALID |
| break evidence persistence | INVALID |
| alter provenance | INVALID |
| future feature | INVALID |
| purge violation | INVALID |
| ignored parameter | INVALID |

---

# 34. BACKTEST DATA INGESTION

Siapkan interface untuk real historical data.

Harus mendukung:

```text
CSV
Parquet
database / future provider
```

dengan canonical normalization.

Data ingestion harus menghasilkan:

```text
dataset manifest
dataset hash
data quality report
```

Quality checks:

```text
duplicate timestamp
missing timestamp
timezone
sorting
gaps
invalid price
negative volume
spread anomalies
NaN
Inf
```

Jangan otomatis "memperbaiki" data tanpa recording transform.

---

# 35. DATA PURIFICATION

Setiap transformation harus tercatat:

```text
input hash
output hash
transformation
version
parameters
row count before
row count after
```

Jangan membuat:

```text
cleaned_data.csv
```

tanpa provenance.

---

# 36. BACKTEST CONFIGURATION

Buat satu canonical config.

Minimal:

```text
symbol
timeframe
dataset
date range

initial capital

strategy
parameter grid

WFO configuration
warmup
purge
label horizon

cost model
spread
slippage
commission

risk model

Monte Carlo
seed
simulation count
block size

thresholds
```

Config harus di-hash.

Config hash harus masuk artifact.

---

# 37. NO HIDDEN DEFAULTS

Cari semua default yang dapat memengaruhi scientific outcome.

Jangan ada hidden:

```text
timeframe = 60
initial_capital = 10000
num_trials = 10
spread = ...
seed = ...
```

yang berbeda dari config canonical.

Defaults boleh ada sebagai API convenience, tetapi final research run HARUS menghasilkan resolved config yang lengkap dan immutable.

---

# 38. STRATEGY IDENTITY

Buat deterministic strategy hash dari:

```text
strategy implementation/version
strategy configuration
parameter schema
```

Jika source strategy berubah:

```text
strategy_hash berubah
```

Run lama tidak boleh dianggap sama.

---

# 39. CONFIG IDENTITY

Resolved config harus diserialisasi canonical:

```text
config_hash
```

Masukkan ke:

```text
run artifact
WFO evidence
holdout evidence
verification
```

---

# 40. ERROR TAXONOMY

Jangan gunakan semua error sebagai `Exception`.

Pisahkan semantic category:

```text
DataError
ConfigurationError
LeakageError
EvidenceError
ValidationError
VerificationError
TimeoutError
PersistenceError
StrategyContractError
HoldoutError
```

Final Gate harus mengetahui apakah error:

```text
retryable
fatal
invalid evidence
```

---

# 41. CLI / RUNNER

Sediakan command yang jelas:

```text
validate-data
create-split
run-wfo
evaluate-oos
evaluate-statistics
evaluate-crisis
evaluate-holdout
verify
run-backtest
run-qualification
```

Idealnya:

```text
run-backtest
```

menjalankan pipeline lengkap.

Dan:

```text
run-qualification
```

menjalankan golden dataset + corruption matrix.

---

# 42. RESUME / CRASH RECOVERY

Jika backtest mati:

```text
partial run
```

tidak boleh dianggap successful.

Artifact state:

```text
CREATED
RUNNING
COMPLETED
FAILED
INVALID
VERIFIED
```

Jangan pernah:

```text
partial → PASS
```

Resume harus memverifikasi artifact sebelumnya.

---

# 43. ATOMIC ARTIFACT WRITES

Gunakan:

```text
temp file
 ↓
fsync bila relevan
 ↓
atomic rename
```

Jangan meninggalkan file half-written yang dianggap valid.

---

# 44. LOGGING

Logging tidak boleh menjadi scientific source of truth.

Truth:

```text
evidence artifacts
```

Logs:

```text
observability
```

Jika log hilang tetapi evidence valid:

```text
research result tetap valid
```

Jika evidence hilang:

```text
research result INVALID
```

---

# 45. SECURITY / INPUT HARDENING

Audit:

- arbitrary path;
- malicious JSON;
- oversized input;
- malformed parameter grid;
- invalid numeric input;
- path traversal;
- corrupted artifact;
- pickle/deserialization risk.

Jangan menggunakan unsafe deserialization untuk research artifact.

---

# 46. PERFORMANCE

Setelah semantics benar:

benchmark:

```text
small
medium
large
```

Catat:

```text
runtime
memory
artifact size
WFO candidate count
MC simulations
```

Optimisasi tidak boleh mengubah result.

---

# 47. CI

CI minimal harus menjalankan:

```text
lint/static checks
unit tests
invariant tests
integration tests
qualification tests
```

Tambahkan timeout.

CI tidak boleh hanya menjalankan sebagian test lalu mengklaim full green.

Exit code harus berasal langsung dari test runner.

Jangan gunakan shell pipeline yang dapat mengubah exit status sehingga test failure terlihat success.

---

# 48. TEST COUNT INTEGRITY

Pastikan CI output mencerminkan:

```text
collected
passed
failed
skipped
xfailed
duration
exit code
```

Jika test hang:

```text
FAIL
```

bukan success.

---

# 49. UI

UI boleh tetap di luar scope jika belum terintegrasi.

Namun:

- jangan membuat UI sebagai source of truth;
- API harus membaca canonical artifacts;
- UI tidak boleh membuat/mengubah scientific verdict;
- UI tidak boleh menyimpan backtest result sebagai satu-satunya persistence;
- UI harus mampu menampilkan `INVALID / FAIL / BORDERLINE / PASS` jika sudah terintegrasi.

---

# 50. REMOVE FALSE CLAIMS

Setelah implementasi selesai:

audit:

```text
README
docs
governance
comments
CLI output
test output
```

Hapus klaim seperti:

```text
production ready
zero debt
100% proven
statistically validated
```

jika evidence belum mendukung.

Dokumentasi harus mencerminkan kondisi aktual.

---

# 51. ACCEPTANCE CRITERIA

Anda TIDAK BOLEH menyatakan pekerjaan selesai sebelum seluruh kondisi berikut terpenuhi.

## Architecture

```text
[ ] dataset canonical
[ ] split canonical
[ ] strategy parameter contract explicit
[ ] WFO valid
[ ] OOS valid
[ ] DSR bound
[ ] crisis valid
[ ] holdout real
[ ] verifier independent
[ ] final gate evidence-driven
```

## Evidence

```text
[ ] complete WFO evidence
[ ] complete OOS evidence
[ ] statistics evidence
[ ] crisis evidence
[ ] holdout evidence
[ ] verification evidence
[ ] provenance hashes
[ ] artifact manifest
```

## Integrity

```text
[ ] no silent critical failure
[ ] no fake evaluation state
[ ] no hidden scientific defaults
[ ] no leakage path
[ ] no mutable holdout
[ ] no false PASS
```

## Determinism

```text
[ ] same input → same result
[ ] same seed → same stochastic result
[ ] telemetry does not alter result
[ ] artifact hash deterministic
```

## Qualification

```text
[ ] golden dataset passes
[ ] corruption matrix rejects all mutations
[ ] WFO selection leakage test passes
[ ] OOS mutation resistance passes
[ ] DSR provenance test passes
[ ] holdout mutation resistance passes
[ ] parameter binding test passes
[ ] persistence failure test passes
[ ] timeout test passes
```

## Regression

```text
[ ] full test suite passes
[ ] no hanging test
[ ] CI reproducible
[ ] exit code trustworthy
```

---

# 52. EXECUTION PROTOCOL

Kerjakan dalam urutan:

```text
PHASE 1
Repository reconnaissance

PHASE 2
Data + split contract

PHASE 3
Strategy parameter contract

PHASE 4
WFO correctness

PHASE 5
OOS correctness

PHASE 6
DSR/statistics

PHASE 7
Evidence/provenance

PHASE 8
Holdout engine

PHASE 9
Independent verifier

PHASE 10
Final gate

PHASE 11
Artifact/persistence

PHASE 12
Determinism

PHASE 13
Adversarial qualification

PHASE 14
CI

PHASE 15
Performance

PHASE 16
Documentation reconciliation
```

Setelah setiap phase:

```text
implement
→ test
→ adversarial review
→ fix
→ regression
→ continue
```

Jangan menunggu saya memberikan instruksi berikutnya.

---

# 53. AUTONOMOUS LOOP

Anda harus bekerja secara autonomous:

```text
AUDIT
 ↓
FIND
 ↓
CLASSIFY
 ↓
FIX
 ↓
TEST
 ↓
ATTACK
 ↓
FIX
 ↓
REGRESSION
 ↓
NEXT FINDING
```

Jika menemukan masalah baru saat memperbaiki masalah lama:

> jangan berhenti.

Masukkan masalah tersebut ke internal remediation queue dan lanjutkan.

Jika sebuah fix mematahkan invariant lama:

> jangan menghapus invariant untuk membuat test pass.

Perbaiki implementasinya.

---

# 54. STOP CONDITIONS

Jangan berhenti hanya karena:

```text
tests pass
```

Jangan berhenti karena:

```text
README says complete
```

Jangan berhenti karena:

```text
no TODO
```

Jangan berhenti karena:

```text
architecture looks good
```

Jangan berhenti karena:

```text
PROGRESS_LEDGER.md mencatat status DONE
```

tanpa memverifikasi setiap `evidence_of_fix` di dalamnya benar-benar menunjuk ke commit/test yang
ada dan valid (lihat Section 0.10). Ledger adalah alat pencatat state, bukan sumber kebenaran —
sama seperti dokumentasi lain, ia tunduk pada Section 0.1.

Anda boleh menyatakan **FINAL COMPLETE** hanya ketika acceptance criteria terpenuhi dan qualification pipeline berhasil.

---

# 55. FINAL REPORT

Pada akhir pekerjaan keluarkan laporan:

```text
HEAD:
FINAL COMMIT:

FILES MODIFIED:
FILES ADDED:
FILES REMOVED:

P0 FIXED:
P1 FIXED:
P2 FIXED:

TEST RESULT:
UNIT:
INVARIANT:
INTEGRATION:
QUALIFICATION:
CORRUPTION:

GOLDEN DATASET RESULT:

DETERMINISM RESULT:

REPRODUCIBILITY RESULT:

WFO RESULT:

OOS RESULT:

DSR RESULT:

HOLDOUT RESULT:

VERIFIER RESULT:

FINAL GATE RESULT:

REMAINING DEBT:

LEDGER RECONCILED: <yes/no — semua entri PROGRESS_LEDGER.md status VERIFIED memiliki evidence_of_fix
                     valid; semua entri OPEN/BLOCKED dipindahkan ke REMAINING DEBT>
GOVERNANCE CONSOLIDATED: <yes/no — status Section 0.9, jumlah file markdown sebelum/sesudah>
```

Untuk setiap remaining debt:

```text
ID
severity
why it remains
impact
whether it blocks backtest
```

Jangan menyembunyikan residual.

Jika masih ada blocker:

> status akhir harus `NOT READY`.

Jika semuanya terpenuhi:

> status akhir `BACKTEST READY`.

---

# 56. FINAL PRINCIPLE

Pegang prinsip ini selama seluruh pekerjaan:

> **Evidence > Opinion.**

Dan:

> **PASS bukan klaim. PASS adalah konsekuensi dari evidence yang dapat diverifikasi.**

AHFMES tidak dianggap siap karena bot dapat menjalankan backtest.

AHFMES dianggap siap ketika:

```text
input
 ↓
computation
 ↓
selection
 ↓
validation
 ↓
holdout
 ↓
verification
 ↓
gate
```

seluruhnya membentuk satu rantai bukti yang:

```text
deterministic
reproducible
auditable
tamper-evident
leakage-resistant
fail-closed
```

Dan yang paling penting:

> **JANGAN MENAMBAHKAN FITUR YANG TIDAK DIPERLUKAN UNTUK MENYELESAIKAN KONTRAK DI ATAS.**

Prioritaskan correctness → evidence integrity → reproducibility → qualification → performance → convenience.

Kerjakan sampai selesai tanpa meminta konfirmasi untuk setiap patch kecil.

Jika keputusan arsitektur diperlukan, pilih solusi yang paling konsisten dengan existing contracts AHFMES dan dokumentasikan keputusan tersebut.

**MULAI DARI REPOSITORY AKTUAL. AUDIT DAHULU. JANGAN BERASUMSI.**