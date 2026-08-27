# YYYY-MM-DD — <JUDUL SINGKAT>

Status: **JURNAL HARIAN ARE-1 / EVIDENCE-CHRONOLOGY / ZERO AUTHORITY**  
Kategori: `ARE1`  
Subjek: `<commit range>` (`file:line`)

---

## Keputusan

```text
TANGGAL  : YYYY-MM-DD
SUBJEK   : <commit> (code <hash>)
DELEGASI : <nomor> <judul> — <DONE/DEFERRED>
AUDITOR  : <4 otak / red-team / ...>
OWNER    : <ratifikasi>
PRINSIP  : perbaiki yang bisa, tunda yang harus, catat biar tidak lupa
```

### FIX — Perbaiki yang bisa (sebelum freeze)

```text
RES-XX — are/file.py:NN
  SEBELUM: <1 baris>
  SESUDAH: <1 baris>
  BUKTI  : git diff --stat 1 file, pytest N passed, TRIGGER N, manifest X
  DAMPAK : <apa yang kini DENY/PASS>
```

### DEFERRED — Tunda yang harus (justified)

```text
ID — SUMBER file:line — DEFERRED
  ALASAN: <butuh tabel baru / breaking migration / generasi baru — bukan hygiene>
  CATAT : wajib <Slice-X ACC / generasi baru> — ticket
  JEJAK : GLOBAL_PROGRESS_DIARY.md YYYY-MM-DD + file ini + debt G07/G18
```

### Pencatatan (agar tidak PR lupa)

```text
JURNAL HARIAN : file ini (ARE1/DIARY/YYYY-MM-DD-*.md)
GLOBAL DIARY  : PROJECT_JOURNAL/DIARY/GLOBAL_PROGRESS_DIARY.md YYYY-MM-DD (mirror)
DELEGASI      : ENGINEERING/DELEGASI_*.md (jejak by-data)
QAO           : <ledger>
DEBT          : <G07/G18 persist>
NEXT          : <Final Consistency → candidate → binder>
```

---

## Snapshot status saat entry ini

```text
ARE-0 CLOSED              = YES @03aec99 (ROOT 3affbbf0)
ARE-1 Scientific Kernel   = IN PROGRESS — <status>
ARE-2 Experience Intel    = LOCKED
ARE-3 Autonomous Science  = LOCKED
ARE-4 Governed Evolution  = LOCKED
IMPLEMENTATION(ARE-1)     = AUTHORIZED (22c585b)
P001                      = NOT AUTHORIZED
PRODUCTION                = CLOSED
```

> Copy template ini → isi → commit di main — jangan ubah histori entri lama.
