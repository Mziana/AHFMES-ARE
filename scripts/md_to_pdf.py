"""Konversi laporan markdown -> PDF tanpa dependensi eksternal.

Jalur: markdown di-parse minimalis (heading/tabel/list/blockquote/inline)
-> HTML ter-styling print-friendly (A4) -> PDF via Microsoft Edge headless
(--print-to-pdf). Read-only terhadap repo; hanya menulis file output.

Usage:
    python scripts/md_to_pdf.py <input.md> <output.pdf>
"""
from __future__ import annotations

import html as H
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EDGE_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)

CSS = """
@page { size: A4; margin: 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.45; color: #1a1a1a; margin: 0; }
h1 { font-size: 17pt; border-bottom: 2.5px solid #222; padding-bottom: 6px;
     margin: 0 0 10px; }
h2 { font-size: 13.5pt; margin: 20px 0 8px; padding: 4px 10px;
     background: #eef1f5; border-left: 4px solid #2b5aa0; }
h3 { font-size: 11.5pt; margin: 14px 0 6px; color: #2b5aa0; }
p { margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px;
        font-size: 9.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #b9c2cf; padding: 4px 8px; text-align: left;
         vertical-align: top; }
th { background: #e8ecf3; font-weight: 600; }
tr:nth-child(even) td { background: #f7f9fb; }
code { font-family: Consolas, monospace; font-size: 9pt;
       background: #f0f2f5; padding: 1px 4px; border-radius: 3px; }
blockquote { margin: 8px 0; padding: 6px 12px; background: #fff8e1;
             border-left: 4px solid #e6a817; }
blockquote p { margin: 3px 0; }
ul { margin: 4px 0 10px; padding-left: 22px; }
li { margin: 3px 0; }
strong { color: #000; }
hr { border: none; border-top: 1.5px solid #c8d0da; margin: 14px 0; }
"""


def _inline(s: str) -> str:
    s = H.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
    return s


def _cell(s: str) -> str:
    """Cell markdown: bold + kode + escape (tanpa em agar kolom rapi)."""
    s = H.escape(s.strip(), quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def _split_row(line: str) -> list[str]:
    parts = line.strip().strip("|").split("|")
    return [p.strip() for p in parts]


def _is_sep_row(line: str) -> bool:
    row = _split_row(line)
    return bool(row) and all(re.fullmatch(r":?-+:?", c) for c in row if c)


def md_to_html(md: str) -> str:
    out: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            out.append("<pre><code>")
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                out.append(H.escape(lines[i]))
                i += 1
            out.append("</code></pre>")
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        if line.strip() == "---":
            out.append("<hr>")
            i += 1
            continue

        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>" +
                       "".join(f"<p>{_inline(b)}</p>" for b in buf if b) +
                       "</blockquote>")
            continue

        if line.strip().startswith("|") and i + 1 < len(lines) \
                and _is_sep_row(lines[i + 1]):
            header = _split_row(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            out.append("<table><thead><tr>" +
                       "".join(f"<th>{_cell(c)}</th>" for c in header) +
                       "</tr></thead><tbody>")
            for r in rows:
                out.append("<tr>" +
                           "".join(f"<td>{_cell(c)}</td>"
                                   for c in r[:len(header)]) +
                           "</tr>")
            out.append("</tbody></table>")
            continue

        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" +
                       "".join(f"<li>{_inline(it)}</li>" for it in items) +
                       "</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" +
                       "".join(f"<li>{_inline(it)}</li>" for it in items) +
                       "</ol>")
            continue

        if line.strip():
            buf = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() \
                    and not re.match(r"^(#|\||>|-|\d+\.|```|---)", lines[i + 1].strip()):
                i += 1
                buf.append(lines[i])
            out.append(f"<p>{_inline(' '.join(buf))}</p>")
        i += 1

    return "\n".join(out)


def find_edge() -> str:
    for p in EDGE_CANDIDATES:
        if Path(p).exists():
            return p
    raise SystemExit("msedge.exe tidak ditemukan — pasang Edge atau Chrome.")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if not src.exists():
        print(f"GAGAL: sumber tidak ada: {src}")
        return 1
    html_doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{H.escape(src.stem)}</title>"
        f"<style>{CSS}</style></head><body>"
        + md_to_html(src.read_text(encoding="utf-8"))
        + "</body></html>"
    )
    # tmp di system temp DGN nama unik — jangan bertabrakan antar-render
    tmp_html = Path(tempfile.gettempdir()) / f"md2pdf_{os.getpid()}_{src.stem}.html"
    tmp_html.write_text(html_doc, encoding="utf-8")
    edge = find_edge()
    dst_old = (dst.stat().st_size, dst.stat().st_mtime_ns) if dst.exists() else None
    if dst.exists():
        try:
            dst.unlink()   # cegah "OK" palsu dari file lama (bug 14 Sep)
        except PermissionError:
            print(f"PERINGATAN: {dst.name} terkunci (sedang dibuka di "
                  f"viewer?) — render kemungkinan gagal menimpanya")
    # user-data-dir unik: Edge menolak headless dgn profil yang sedang dipakai
    # instance lain (exit diam-diam tanpa output).
    cmd = [edge, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--user-data-dir={tempfile.mkdtemp(prefix='edge_pdf_')}",
           "--no-first-run", "--disable-extensions",
           f"--print-to-pdf={dst.absolute()}", tmp_html.absolute().as_uri()]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    # msedge.exe bisa detach (launcher exit lebih dulu dari penulisan PDF):
    # tunggu file muncul maks ~10 dtk sebelum menyatakan gagal.
    deadline = time.time() + 10
    while not dst.exists() and time.time() < deadline:
        time.sleep(0.5)
    tmp_html.unlink(missing_ok=True)   # hanya SETELAH PDF (atau gagal) final
    cur = (dst.stat().st_size, dst.stat().st_mtime_ns) if dst.exists() else None
    if cur is None:
        print(f"GAGAL: {dst.name} tidak dibuat Edge (pdf lama "
              f"{dst_old[0] // 1024} KB sudah dihapus — render ulang perlu)")
        return 1
    if cur == dst_old:
        print(f"GAGAL: {dst.name} TIDAK tertimpa — masih file lama. "
              f"Tutup PDF viewer yang membukanya, lalu jalankan ulang.")
        return 1
    data = dst.read_bytes()
    n_pages = data.count(b"/Type /Page") or data.count(b"/Type/Page")
    if not data.startswith(b"%PDF") or len(data) < 20_000:
        print(f"GAGAL: {dst.name} bukan PDF valid "
              f"({len(data)} B, pages~{n_pages})")
        dst.unlink(missing_ok=True)
        return 1
    print(f"OK  {dst}  ({len(data)/1024:.0f} KB, ~{n_pages} halaman)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
