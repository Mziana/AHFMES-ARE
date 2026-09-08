"""F2 — Evidence repair: build multi-session dataset + archived calendar artifact
and re-run strategy v2 replay (both profiles) with valid B1 evidence.

Honest window rule (P0-01 provenance): a replay window may only use calendar
information whose `information_available_at` <= every evaluation timestamp T.
The only real FF snapshot available (calendar_5c4a51d0.json, fetched
2026-09-07T18:59:42Z) therefore bounds the replay to M5 sessions with
close_ts >= 1788807582 → session 2026-09-07 22:00 → 2026-09-08 08:25
(125 bars). Earlier sessions are excluded — NOT fabricated.

Outputs (runtime, gitignored):
  data/research/v2_replay/dataset_f2_m5.json     (session 6, 125 bars)
  data/research/v2_replay/dataset_f2_m15.json    (full M15 warmup Aug 19–Sep 8)
  data/research/v2_replay/calendar_multiday.json (archived artifact, real fetch ts)
  data/research/v2_replay/f2_multiday/summary_{micro,scalp}.json
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from strategy_v2 import broker_meta as bm
from strategy_v2 import registry
from strategy_v2.replay import (DEFAULT_OUT, calendar_artifact_hash, load_calendar,
                                qualify_dataset, run_profile,
                                save_calendar_artifact)

INFO_AT = 1788807582  # 2026-09-07T18:59:42Z — REAL fetch time, bukan karangan


def segment_sessions(m5: list) -> list[list]:
    sessions = [[m5[0]]]
    for a, b in zip(m5, m5[1:]):
        if int(b["time"]) - int(a["time"]) != 300:
            sessions.append([b])
        else:
            sessions[-1].append(b)
    return sessions


def main() -> int:
    out = DEFAULT_OUT
    m5 = json.load(open(out / "multiday_m5_raw.json", encoding="utf-8"))["candles"]
    m15 = json.load(open(out / "multiday_m15_raw.json", encoding="utf-8"))["candles"]

    sessions = segment_sessions(m5)
    honest = [s for s in sessions if int(s[-1]["time"]) + 300 >= INFO_AT]
    assert len(honest) == 1, f"ekspekt 1 session honest, dapat {len(honest)}"
    m5_f2 = honest[0]
    print(f"F2 M5 window: {m5_f2[0]['time']} -> {m5_f2[-1]['time'] + 300} "
          f"({len(m5_f2)} bars)")

    qual = qualify_dataset(m5_f2, m15)
    print("qualification:", json.dumps(qual))
    assert qual["m5"]["valid"] and qual["m15"]["valid"], "dataset F2 tidak valid"

    (out / "dataset_f2_m5.json").write_text(
        json.dumps({"candles": m5_f2}, ensure_ascii=True), encoding="utf-8")
    (out / "dataset_f2_m15.json").write_text(
        json.dumps({"candles": m15}, ensure_ascii=True), encoding="utf-8")

    # Archived calendar artifact with REAL provenance (source artifact fetch ts).
    src = out.parent / "calendar" / "calendar_5c4a51d0.json"
    raw = json.loads(src.read_text(encoding="utf-8"))
    art = save_calendar_artifact(raw, src, out, fetched_at=INFO_AT)
    cal_path = out / "calendar_multiday.json"
    shutil.copyfile(art, cal_path)
    print("calendar artifact:", cal_path.name,
          "hash:", calendar_artifact_hash(cal_path)[:12],
          "info_at:", load_calendar(cal_path)["information_available_at"])

    meta = bm.load_broker_meta({})
    print("broker meta:", meta["source"],
          "point_value_usd_per_lot:", bm.point_value_usd_per_lot(meta))

    f2dir = out / "f2_multiday"
    for profile in ("micro", "scalp"):
        res = run_profile(profile, out / "dataset_f2_m5.json",
                          out / "dataset_f2_m15.json", str(cal_path), f2dir)
        f = res["summary"]["funnel"]
        print(f"\n=== {profile.upper()} ===")
        print("config_hash:", res["summary"]["config_hash"][:12])
        print("opportunities:", f["evaluation_opportunities"],
              "| B1 veto:", f["veto_by_gate"].get("B1", 0),
              "| B2 veto:", f["veto_by_gate"].get("B2", 0))
        print("final_signals:", f["final_signals"],
              "| executed:", f["executed_trades"],
              "| gross/net:", f["gross_usd"], f["net_usd"])
        print("rejected_execution_reasons:", f["rejected_execution_reasons"])
    return 0


if __name__ == "__main__":
    sys.exit(main())