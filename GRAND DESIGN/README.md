# GRAND DESIGN — AHFMES Autonomous Research Engine (ARE)

Folder ini berisi **konsolidasi non-normatif** dari desain menyeluruh ARE yang
sebelumnya tersebar di 228 file `PROJECT_GOVERNANCE/`.

## Isi

| File | Isi |
|---|---|
| `AHFMES_ARE_GRAND_DESIGN_V1.md` | Dokumen tunggal grand design ARE: identitas, konstitusi, arsitektur, model objek, otoritas, evidence, budget pencarian, promotion, tata kelola audit, status. |
| `percakapan.md` | Arsip percakapan awal pembangunan ARE (2026-08-19/20) — sumber historis desain; dipetakan ke dokumen final di Lampiran C. |

Lampiran dalam `AHFMES_ARE_GRAND_DESIGN_V1.md`:
- **Lampiran A** — peta dokumen sumber per bab
- **Lampiran B** — filosofi fail-closed
- **Lampiran C** — traceability percakapan awal → desain final
- **Lampiran D** — alur flowchart: versi percakapan awal vs final ARE

## Status dokumen ini

```text
STATUS = KONSOLIDASI ORIENTASI / NON-NORMATIF / ZERO AUTHORITY
SUMBER = ekstraksi setia dari PROJECT_GOVERNANCE (repo ini)
         + penelusuran repo sumber Mziana/AHFMES-CHATGPT
         branch codex/current-authority-docs
```

- Dokumen ini **bukan** anggota manifest normatif dan **tidak** memiliki
  otoritas machine/closure/audit-rule apa pun.
- Otoritas normatif tetap pada closed-set Manifest **V36**
  (`PROJECT_GOVERNANCE/ARE0/MANIFEST/AHFMES_ARE_0_NORMATIVE_AUTHORITY_MANIFEST_V36.md`,
  generation 36, namespace S1). Angka regresi permanen kini **369**
  (R7=26, R8=40, R9=X001..X303); angka 365 di dalam dokumen konsolidasi
  adalah snapshot historis saat penulisan dan telah disupersesi.
- Tidak ada satu pun kalimat di sini yang mengotorisasi implementasi,
  riset P001, produksi, atau trading.

## Catatan provenance penting

Setelah ditelusuri, **repo sumber tidak pernah memiliki file "grand design"
tunggal untuk ARE**. Desain ARE memang sejak awal lahir terpecah menjadi
dokumen-dokumen governance berversi. File bernama *Grand Design* yang ada di
repo sumber (`MD/AHFMES_MASTER/GRAND_DESIGN_v1.0.md`) adalah rencana
penyelesaian **sistem operasional AHFMES (bot trading)**, bukan desain ARE.

Dokumen di folder ini karenanya adalah **rekonstruksi/konsolidasi** yang dibuat
setia terhadap isi 228 file governance — bukan pengganti, bukan revisi, dan
tidak mengubah satu pun aturan normatif.
