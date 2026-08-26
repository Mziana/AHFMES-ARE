# IMPLEMENTATION — Kode Runtime Terotorisasi

```text
STATUS   = KOSONG / TERKUNCI
TANGGAL  = 2026-08-26
ISI      = TIDAK ADA — dan TIDAK BOLEH diisi
```

## Aturan folder ini

1. Folder ini adalah rumah **kode implementasi runtime** (ARE-1 dst.)
   apabila dan hanya apabila otoritasnya telah diterbitkan.
2. Syarat pengisian:

```text
IMPLEMENTATION_AUTHORITY_CHARTER = DITERBITKAN PEMILIK PROYEK
   - eksplisit, tertulis, commit khusus
   - cakupan fase disebut namanya (awalnya: ARE-1 Scientific Kernel saja)
   - charter tidak bisa diterbitkan oleh diary, LLM, council, atau dokumen
     mana pun lainnya
```

3. Sampai kondisi tersebut: **dilarang menaruh file apa pun** di folder ini —
   termasuk draft, prototipe, cuplikan, atau kode "sementara". Draft alat
   verifikasi milik `../TOOLS/`, bukan sini.
4. Struktur internal (package layout, penamaan modul) akan ditetapkan oleh
   Lead Architect + engineering lead SAAT charter aktif, mengacu pada:
   - Source Reuse Map (Grand Design Bab 27) — reuse AHFMES modules,
     dilarang orchestrator kedua;
   - Workflow GitHub-first — local checkout adalah replica test,
     bukan source authority.
5. Riwayat = Git. Dilarang `_v2/_final/_backup/_copy`.

## Status saat ini

```text
IMPLEMENTATION_AUTHORITY_CHARTER = BELUM ADA
FOLDER                           = KOSONG (README ini satu-satunya isi)
PELANGGAN ATURAN #3              = BLOCKER kelas A bila terjadi
```
