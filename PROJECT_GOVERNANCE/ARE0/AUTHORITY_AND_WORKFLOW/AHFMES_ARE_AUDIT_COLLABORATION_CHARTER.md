# AHFMES ARE-0 — Audit Collaboration Charter (V36 Wave)

Status: **NON-NORMATIF / PIAGAM KOLABORASI / ZERO AUTHORITY**  
Tanggal: 2026-08-26

## 1. Pihak & peran

| Peran | Pemegang | Wewenang | Larangan keras |
|---|---|---|---|
| OWNER | pemilik proyek | keputusan akhir; gate F6; ratifikasi charter/DoD | — |
| LEAD ARCHITECT | arsitek desain | desain, konsolidasi, triage temuan | self-acceptance; coding; klaim closure |
| RED-TEAM INTERNAL | agen serang paralel | menyerang sebelum auditor | mengubah file; klaim PASS |
| EXTERNAL AUDITOR | pendamping owner | audit by-data pada exact SHA; temuan = input adversarial | menerima kata "selesai" tanpa reproduksi |

## 2. Aturan bukti

```text
1. By-data only: setiap klaim disertai perintah/output yang dapat
   direproduksi (git rev-parse, hash-object, hitungan baris).
2. Exact-SHA binding: audit selalu pada subjek beku, tidak pada moving head.
3. Temuan wajib format: ID / SEVERITY / PRECONDITION / PATH / WHY /
   CONSEQUENCE / MINIMAL_CORRECTION_CLASS.
4. Temuan auditor = adversarial input; difilter arsitek (reproduksi ->
   disposisi) lalu diratifikasi owner. Tidak ada pihak yang bulat-bulat
   menerima atau menolak.
5. Semua kronologi material masuk JQO_LOCAL + mirror JQO_GLOBAL.
```

## 3. Disiplin subjek & re-mint

- Subjek eksekusi = HEAD saat dispatch SA-11; berubah hanya lewat
  re-mint pra-dispatch yang tercatat (alasan + supersedee + approval).
- Default maksimum 2 re-mint per gelombang tanpa persetujuan eksplisit
  tambahan owner (menutup celah Run S1 Addendum 2).
- Dilarang menyebut subjek "final" sebelum binder; gunakan
  "subjek eksekusi SA-11 saat ini".

## 4. Kosakata

Kata `PASS/CLOSED/READY` hanya sah sebagai nilai disposisi formal pada
record yang memang memilikinya. Di diary/JQO dipakai bentuk faktual:
"tereksekusi", "terverifikasi pada <SHA>", "disupersede oleh <SHA>".

## 5. Non-goals absolut

Charter ini tidak memberi otoritas implementasi, riset P001, produksi,
broker/trading, merge, maupun penutupan ARE-0. Otoritas tetap pada
closed-set Manifest V36.
