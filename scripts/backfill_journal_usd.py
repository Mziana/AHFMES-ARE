"""Backfill/verifikasi pnl_usd journal demo dari deal history bridge (satu sumber kebenaran).

Revisi 5 (2026-09-11, setelah screenshot broker owner): jurnal tidak hanya kehilangan
  PnL — bisa kehilangan SELURUH PASANGAN open+close saat driver mati/restart di
  sekitar eksekusi (kasus nyata: SCALP 429141720 +18.04, comment deal IN `R1-SCALP`,
  tak pernah masuk jurnal). Rev5 menambah tahap rekonstruksi OPEN hilang: deal IN
  ber-comment `R1-MICRO`/`R1-SCALP` yang position_id-nya tidak dirujuk jurnal mana
  pun (ticket open, position_id open, ticket close, close_position_id) dipasangkan
  ke deal OUT eksak via position_id; bila OUT ada → pasangan event open+closed_
  detected ditulis dengan flag `reconstructed:true` (bila OUT belum ada → posisi
  masih hidup/belum tuntas, dilaporkan INFO, tidak dikarang). Hanya comment `R1-*`
  yang dipakai — deal IN main bot tanpa comment R1 tidak disentuh.

Revisi 4 (2026-09-10 malam, setelah backfill rev3 terbukti salah pasang):
  FIFO penuh rev3 mencuri deal milik posisi MAIN BOT (bukan R1): deal
  +18.04 (pid 429141720, posisi 0.02 non-R1) terpakai utk ticket jurnal
  429196842. Verifikasi empiris 2026-09-10: deal close R1 selalu membawa
  position_id == ticket order entry (akun netting, 1 posisi/order).
  Rev4: tahap eksak = position_id == open.position_id ATAU == open.ticket.
  FIFO hanya utk data lama tanpa kecocokan eksak. Event close backfilled
  rev3 yang kontradiksi dgn deal eksak dikoreksi in-place (flag
  corrected:true) — perbaikan terdokumentasi, backup .bak-backfill
  tetap mencerminkan isi SEBELUM backfill pertama.

Revisi 3 (2026-09-10 malam) — setelah bug revisi 1 & 2 ditemukan di lapangan:
  R1: min-per-close-independen; R2: FIFO hanya atas close-null → keduanya bisa
  mencuri deal milik close yang SUDAH terisi (deal +12.22/+18.04 diambil untuk
  429196842/429235206 padahal milik 428858312/428442810). Akar masalahnya sama:
  pairing hanya melihat sebagian open.

Revisi 3 mem-pair SEMUA open sekaligus, berurutan entry-ts:
  1. position_id EKSAK — deal close membawa position_id = ticket posisi
     (terverifikasi empiris 2026-09-10: deal 430200326 → position_id
     429235206 = ticket SCALP; bridge ≥ revisi ini expose field-nya).
  2. FIFO penuh sebagai fallback (deal OUT terakhir-unused ≥ entry_ts-60,
     lot disamakan bila diketahui) — untuk data lama tanpa position_id.

Close yang SUDAH terisi tidak diubah diam-diam: dicocokkan ulang ke deal
pairing-nya, dan hanya ditandai mismatch (perbaikan isi tetap keputusan
owner — jurnal tidak boleh berubah diam-diam).

Open yang TIDAK punya event close sama sekali (driver melewatkan deteksi,
mis. SCALP 428419669 — posisi masih ada saat observer lama menganggapnya
tutup) direkonstruksi dari deal history dengan flag "reconstructed": true;
tanpa pasangan di history → tetap dilaporkan, tidak dikarang.

Jurnal hanya ditulis ulang bila ada perubahan; backup .bak-backfill selalu
mencerminkan isi SEBELUM penulisan (idempotent — dijalankan ulang aman).
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "data" / "research" / "r1" / "demo" / "demo_journal.jsonl"
BRIDGE = "http://127.0.0.1:18888"


def bridge_get(path: str) -> dict:
    tok_file = ROOT / "data" / "bridge_token.txt"
    tok = tok_file.read_text().strip() if tok_file.exists() else ""
    req = urllib.request.Request(f"{BRIDGE}{path}",
                                 headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def is_out(d: dict) -> bool:
    return d.get("entry") not in (0, "0", None, 0.0)


def pair_deal(opens: list, deals: list) -> dict:
    """Pair tiap open {ticket, ts, lot, position_id?} ke satu deal close.

    Return {ticket: deal}. Urutan proses = entry-ts naik; satu deal max satu
    pasangan. Eksak via position_id dulu, sisanya FIFO penuh."""
    used: set = set()
    result: dict = {}
    for o in sorted(opens, key=lambda x: x.get("ts") or 0):
        lot = o.get("lot")
        pid = o.get("position_id")
        ticket = o.get("ticket")
        best = None
        # 1) eksak — position_id deal == position_id open ATAU == ticket open
        #    (empiris R1 2026-09-10: bridge MT5 netting, position_id = ticket
        #    order entry; rev3 gagal karena ticket tidak dicoba sebagai pid)
        if pid is not None or ticket is not None:
            exact = [d for d in deals
                     if d.get("ticket") not in used and is_out(d)
                     and str(d.get("position_id") or "") in
                     {str(pid) if pid is not None else None,
                      str(ticket) if ticket is not None else None} - {None}]
            if exact:
                best = max(exact, key=lambda d: float(d.get("time") or 0))
        # 2) FIFO penuh
        if best is None:
            cands = []
            for d in deals:
                try:
                    if d.get("ticket") in used or not is_out(d):
                        continue
                    t = float(d.get("time") or 0)
                    if t < float(o.get("ts") or 0) - 60:
                        continue
                    if lot and d.get("volume") not in (None, 0, 0.0) and \
                            abs(float(d.get("volume")) - float(lot)) > 1e-9:
                        continue
                    cands.append(d)
                except Exception:
                    continue
            if cands:
                best = min(cands, key=lambda d: float(d.get("time") or 0))
        if best is not None:
            used.add(best.get("ticket"))
            result[o["ticket"]] = best
    return result


def main() -> int:
    fix = "--fix" in sys.argv
    if not JOURNAL.exists():
        print("journal tidak ada")
        return 1
    events = [json.loads(l) for l in
              JOURNAL.read_text(encoding="utf-8").splitlines() if l.strip()]
    before = [dict(e) for e in events]

    deals = bridge_get("/deals?days=7").get("deals", [])
    print(f"journal events: {len(events)}, deals: {len(deals)}")

    opens = [e for e in events if e.get("evt") == "open" and e.get("ticket")]
    close_by_ticket = {}
    for e in events:
        if e.get("evt") == "closed_detected" and e.get("ticket") is not None:
            close_by_ticket.setdefault(e["ticket"], e)

    # open tanpa event close → rekonstruksi (jangan karang tanpa bukti)
    reconstructed = []
    missing_close = [e for e in opens if e["ticket"] not in close_by_ticket]

    pair = pair_deal(opens, deals)

    # 1) isi close-null
    filled = 0
    for t, d in sorted(pair.items(), key=lambda kv: kv[1].get("time") or 0):
        c = close_by_ticket.get(t)
        if c is None or c.get("pnl_usd") is not None:
            continue
        c["pnl_usd"] = float(d.get("profit") or 0.0)
        c["pnl"] = c["pnl_usd"]          # nilai lama 0.0/None tidak dipercaya
        c["close_usd"] = d.get("price")
        c["vol"] = d.get("volume")
        c["close_deal_ts"] = d.get("time")
        c["close_position_id"] = d.get("position_id")
        c["matched_by"] = ("position_id" if d.get("position_id") else "fifo")
        c["backfilled"] = True
        filled += 1
        print(f"  ISI      {c.get('arm')} {t}: pnl_usd={c['pnl_usd']:.2f} "
              f"@ {d.get('price')} (deal_ts {d.get('time')}, {c['matched_by']})")

    # 2) verifikasi silang close yang sudah terisi
    #    rev4: kecocokan EKSAK (position_id) yang kontradiksi dgn nilai
    #    backfilled lama = SALAH PAIRING → dikoreksi in-place bila --fix
    #    (flag corrected:true); tanpa --fix hanya dilaporkan.
    mismatch = 0
    corrected = 0
    for t, d in pair.items():
        c = close_by_ticket.get(t)
        if c is None or c.get("pnl_usd") is None:
            continue
        j = float(c.get("pnl_usd") or 0.0)
        p = float(d.get("profit") or 0.0)
        exact_match = d.get("position_id") is not None and \
            str(d.get("position_id")) == str(t)
        if abs(j - p) > 0.005:
            mismatch += 1
            if exact_match and fix and (c.get("backfilled") or c.get("matched_by") != "position_id"):
                c["pnl_usd"] = p
                c["pnl"] = p
                c["close_usd"] = d.get("price")
                c["vol"] = d.get("volume")
                c["close_deal_ts"] = d.get("time")
                c["close_position_id"] = d.get("position_id")
                c["matched_by"] = "position_id"
                c["corrected"] = True
                corrected += 1
                print(f"  KOREKSI  {c.get('arm')} {t}: {j:.2f} -> {p:.2f} "
                      f"@ {d.get('price')} (deal eksak position_id, deal_ts {d.get('time')})")
            else:
                tag = "deal eksak" if exact_match else "deal pairing"
                print(f"  MISMATCH {t}: journal {j:.2f} vs {tag} {p:.2f} "
                      f"(deal_ts {d.get('time')}) — TIDAK diubah, keputusan owner")
        else:
            # enrich metadata bila belum ada, isi tetap
            c.setdefault("close_deal_ts", d.get("time"))
            c.setdefault("close_position_id", d.get("position_id"))

    # 3) rekonstruksi close hilang dari deal pairing
    for o in missing_close:
        d = pair.get(o["ticket"])
        if d is None:
            print(f"  PERHATIAN: open {o.get('arm')} {o['ticket']} TIDAK punya "
                  f"event close DAN deal pairing tidak ketemu — tidak dikarang")
            continue
        events.append({
            "evt": "closed_detected", "arm": o.get("arm"), "ticket": o["ticket"],
            "pnl": float(d.get("profit") or 0.0),
            "pnl_usd": float(d.get("profit") or 0.0),
            "close_usd": d.get("price"), "vol": d.get("volume"),
            "close_deal_ts": d.get("time"),
            "close_position_id": d.get("position_id"),
            "matched_by": "position_id" if d.get("position_id") else "fifo",
            "reconstructed": True,
            "ts": d.get("time"),
        })
        reconstructed.append(o["ticket"])
        print(f"  REKONSTRUKSI {o.get('arm')} {o['ticket']}: pnl_usd="
              f"{float(d.get('profit') or 0.0):.2f} @ {d.get('price')} "
              f"(deal_ts {d.get('time')}) — close event hilang dari driver lama")

    # 4) rev5: rekonstruksi OPEN hilang — deal IN ber-comment R1-* yang
    #    position_id-nya tidak dirujuk jurnal mana pun. Kasus: driver mati/
    #    restart tepat saat eksekusi → event open+close tak pernah ditulis.
    known = set()
    for e in opens:
        for k in ("ticket", "position_id"):
            if e.get(k) is not None:
                known.add(str(e[k]))
    for c in close_by_ticket.values():
        for k in ("ticket", "close_position_id"):
            if c.get(k) is not None:
                known.add(str(c[k]))
    reconstructed_open = 0
    ins = [d for d in deals if not is_out(d)
           and str(d.get("comment") or "").startswith("R1-")]
    for d in sorted(ins, key=lambda x: float(x.get("time") or 0)):
        pid = d.get("position_id")
        if pid is None or str(pid) in known:
            continue
        arm = str(d.get("comment")).split("-", 1)[1]
        if arm not in ("MICRO", "SCALP"):
            continue
        outs = [x for x in deals if is_out(x)
                and str(x.get("position_id") or "") == str(pid)]
        if not outs:
            print(f"  INFO     {arm} {pid}: deal IN tercatat tapi OUT belum ada "
                  f"(posisi masih hidup/belum tuntas) — tidak dikarang")
            continue
        out = max(outs, key=lambda x: float(x.get("time") or 0))
        direction = "BUY" if d.get("type") == 0 else "SELL"
        in_px, out_px = float(d.get("price") or 0.0), float(out.get("price") or 0.0)
        o_evt = {"evt": "open", "arm": arm, "ts": d.get("time"),
                 "decision": direction, "pattern": None, "score": None,
                 "lot": d.get("volume"), "ticket": pid, "entry_usd": d.get("price"),
                 "reconstructed": True,
                 "note": "open hilang (driver restart saat eksekusi) — "
                         "direkonstruksi dari deal IN history (rev5, eksak position_id)"}
        # sl_points/tp_points: level yang tersentuh bisa diturunkan eksak dari
        # harga OUT (SL utk loser, TP utk winner); sisi lain tidak diketahui.
        pts = abs(out_px - in_px) / 0.01 if in_px and out_px else None
        if pts is not None:
            if float(out.get("profit") or 0.0) >= 0:
                o_evt["tp_points"] = round(pts, 1)
            else:
                o_evt["sl_points"] = round(pts, 1)
        c_evt = {"evt": "closed_detected", "arm": arm, "ticket": pid,
                 "pnl": float(out.get("profit") or 0.0),
                 "pnl_usd": float(out.get("profit") or 0.0),
                 "close_usd": out.get("price"), "vol": out.get("volume"),
                 "close_deal_ts": out.get("time"),
                 "close_position_id": pid,
                 "matched_by": "position_id", "reconstructed": True,
                 "ts": out.get("time")}
        events.append(o_evt)
        events.append(c_evt)
        known.add(str(pid))
        reconstructed_open += 1
        print(f"  REKONSTRUKSI-OPEN {arm} {pid}: {direction} {in_px} "
              f"(deal_ts {d.get('time')}) -> OUT pnl={float(out.get('profit') or 0.0):.2f} "
              f"@ {out_px} (deal_ts {out.get('time')}) — pasangan open+close hilang")

    if events == before:
        print("Tidak ada perubahan — journal sudah sinkron (idempotent).")
        return 0

    # backup mencerminkan isi SEBELUM penulisan (idempotent: run ke-2 tidak
    # menimpa backup asli dgn versi backfilled)
    bak = JOURNAL.with_suffix(".jsonl.bak-backfill")
    if not bak.exists():
        cur = JOURNAL.read_text(encoding="utf-8")
        prev = json.loads("[" + ",".join(
            l for l in [x.strip() for x in cur.splitlines() if x.strip()]) + "]") \
            if cur.strip() else []
        bak.write_text("\n".join(json.dumps(e, ensure_ascii=True) for e in prev) + "\n",
                       encoding="utf-8")
    JOURNAL.write_text("\n".join(json.dumps(e, ensure_ascii=True) for e in events) + "\n",
                       encoding="utf-8")
    print(f"SELESAI: {filled} diisi, {len(reconstructed)} close direkonstruksi, "
          f"{reconstructed_open} open+close direkonstruksi (rev5), "
          f"{corrected} dikoreksi, {mismatch} mismatch dilaporkan (backup: {bak.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
