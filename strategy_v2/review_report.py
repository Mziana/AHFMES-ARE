"""C2 — Review report (Analyst Desk v2.5, plan C2).

Mengubah output review() menjadi laporan markdown + USULAN perubahan hipotesis
(H-SCORE-DESK-01 tier/H-VOL-01) dalam FILE terpisah — TIDAK auto-applied
(experiment freeze Pagar 1: perubahan = hipotesis baru + keputusan owner).

PURE: builder string dari data. I/O hanya tulis laporan di driver, bukan di sini.
"""
from __future__ import annotations

from .journal import review, review_by_tier

MIN_N_RECOMMEND = 20   # plan §C2: usulan hanya untuk band dengan n >= 20


def _fmt(v, nd=2) -> str:
    return f"{v:.{nd}f}" if isinstance(v, (int, float)) else "n/a"


def build_review_report(buckets: dict, per_tier: dict | None = None,
                        min_n: int = MIN_N_RECOMMEND) -> str:
    """Laporan markdown dari review buckets. Deterministik: urutan key sorted."""
    lines = ["# Journal Review — paper trades (Analyst Desk v2.5)", "",
             "Sumber: `data/research/v2_replay/journal_*.jsonl` (append-only).",
             "Semua angka = deskriptif dari data paper; BUKAN rekomendasi otomatis.", ""]
    if not buckets:
        lines.append("_Journal kosong — belum ada paper trade yang ditutup._")
        return "\n".join(lines) + "\n"

    lines += ["| Bucket | n | Win rate | Avg RR | Expectancy (USD/trade) |",
              "|---|---|---|---|---|"]
    for key in sorted(buckets):
        b = buckets[key]
        lines.append(f"| `{key}` | {b['n']} | {_fmt(b.get('win_rate', 0) * 100, 1)}% "
                     f"| {_fmt(b.get('avg_rr'))} | {_fmt(b.get('expectancy', 0.0), 4)} |")
    lines.append("")

    if per_tier:
        lines += ["## Expectancy per tier (kontrak plan §Risiko-4)", "",
                  "Kalau expectancy tier PAPER <= 0 pada n memadai → usulan "
                  "nonaktifkan tier PAPER (keputusan owner).", "",
                  "| Tier | n | Win rate | Expectancy |", "|---|---|---|---|"]
        for t in sorted(per_tier):
            d = per_tier[t]
            lines.append(f"| {t} | {d['n']} | {_fmt(d.get('win_rate', 0) * 100, 1)}% "
                         f"| {_fmt(d.get('expectancy', 0.0), 4)} |")
        lines.append("")

    lines += _proposals(buckets, per_tier, min_n)
    return "\n".join(lines) + "\n"


def _proposals(buckets: dict, per_tier: dict | None, min_n: int) -> list[str]:
    """USULAN (file, bukan auto-apply): perubahan hipotesis = identity baru +
    keputusan owner (experiment freeze tetap berlaku)."""
    out = ["## Usulan perubahan hipotesis (USULAN — TIDAK auto-applied)", ""]
    made = []
    for key in sorted(buckets):
        b = buckets[key]
        if b["n"] < min_n:
            continue
        exp = b.get("expectancy", 0.0)
        band = b.get("band", "")
        if exp > 0 and band == "PAST":
            made.append(f"- `H-SCORE-DESK-01`: band PAST bucket `{key}` positif "
                        f"(n={b['n']}, exp={_fmt(exp, 4)}) → usulkan turunkan "
                        f"tiers.watch (baru = hipotesis child, bukan edit diam-diam).")
        elif exp < 0 and band in ("PAPER", "TRADE"):
            made.append(f"- `H-SCORE-DESK-01`: band {band} bucket `{key}` negatif "
                        f"(n={b['n']}, exp={_fmt(exp, 4)}) → usulkan naikkan "
                        f"tiers.paper / evaluasi ulang bobot (hipotesis child).")
    if per_tier:
        p = per_tier.get("PAPER") or {}
        if p.get("n", 0) >= min_n and p.get("expectancy", 0.0) <= 0:
            made.append(f"- Tier PAPER expectancy <= 0 (n={p['n']}, "
                        f"exp={_fmt(p.get('expectancy', 0.0), 4)}) → usulkan "
                        f"NONAKTIFKAN tier PAPER (plan §Risiko-4).")
    if not made:
        out.append(f"_Belum ada usulan: tidak ada bucket dengan n >= {min_n} "
                   f"yang sinyalnya cukup kuat. Kumpulkan lebih banyak paper trade._")
    else:
        out += made
    out += ["", "> Semua usulan HANYA file. Penerapan = hipotesis BARU di registry "
            "(parent tercatat) + persetujuan owner — experiment freeze v2.3 tetap."]
    return out


def build_review_report_from_journal(path) -> str:
    """Convenience: baca journal file → laporan markdown penuh."""
    return build_review_report(review(path), review_by_tier(path))
