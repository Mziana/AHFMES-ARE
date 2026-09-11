"""R1 DEMO DRIVER v4 — 2 arm: MICRO & SCALP (owner spec rev 2026-09-10).

Perubahan v5 (owner toggle):
  - arm AKTIF/NONAKTIF per arm (toggle UI): arm nonaktif TIDAK dievaluasi
    dan TIDAK order — posisi terbuka tetap dikelola broker SL/TP. Perintah
    lewat FILE TERPISAH arm_toggle.json (UI tulis → driver baca → apply →
    hapus) — TIDAK lewat driver_state.json, karena state itu ditulis ulang
    driver tiap poll (perintah UI bisa tertimpa sebelum terbaca — race).
    Toggle berlaku tanpa restart (<2 detik). Kill override UI dipindah ke
    mekanisme yang sama (bug laten v4: override hanya di-sync saat start).

Perubahan v4 (fix "P&L +0.00 di jurnal"):
  - deal close sering TELAT masuk /deals (history broker) — rev3 menulis
    event closed_detected seketika dengan pnl null → agregat UI +0.00 dan
    tidak pernah diperbaiki. rev4: close masuk pending_close dan di-retry
    tiap poll sampai deal ketemu (maks 15 menit → null + unresolved:true).
    Event close ditulis SEKALI, saat pnl sudah diketahui.
  - dedupe: ticket yang sudah punya event closed_detected tidak pernah
    ditulis ulang (aman setelah restart/backfill).

Perubahan v3 (owner rules):
  - MICRO eksekusi di bar close M1: driver poll 1s, trigger saat bar M1 close.
    M5 & M15 dievaluasi saat bar masing-masing TF close (cache keputusan).
  - MULTI-TF transparansi: checklist per TF (M1/M5/M15 pola+poin) + RSI tiap TF
    ditampilkan di UI via driver_state.json.
  - SCALP tetap trigger di close M5.
  - pnl tracking FIX rev3: PnL real dari /deals (deal close di-match via
    `order` — bridge /order mengembalikan order id deal entry, terverifikasi
    di jurnal 428326048). /history TIDAK ADA di bridge (respons
    "unknown endpoint" dibaca kosong diam-diam) → pnl selalu 0.0 dan kill
    switch tak pernah menyala. PnL tak ketemu → NETRAL (streak tak diubah),
    tidak pernah mengarang 0.0.
  - close confirm 2 poll: posisi hilang 1x dari /positions (gagal-baca
    sesaat) TIDAK dianggap close — butuh hilang 2 poll berturut-turut.
  - persist rev3: open_orders + last_entry_ts (cooldown) + kill streak
    disimpan di driver_state.json — restart tidak lagi lupa posisi terbuka.
  - SL/TP MICRO = ATR M1 clamp 130-210/200-300 pts (owner), TP dibatasi swing
    berlawanan terdekat (tidak menembus resistance).
  - H4 asli dari bridge (fallback proxy M15 bila kosong).
  - Kill switch per arm: 3 lose streak → jeda 30 menit (toggle UI, tetap).
  - Eksekusi: bridge /order market dengan SL/TP (akun DEMO fail-closed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "research" / "r1" / "demo"
STATE_FILE = OUT / "driver_state.json"
LOG_TEE = OUT / "driver_log.txt"  # rev6: teelog permanen (observability spawn WMI)
TOGGLE_FILE = OUT / "arm_toggle.json"  # rev5: perintah UI → driver (bukan state file)
TOKEN_FILE = ROOT / "data" / "bridge_token.txt"
BASE = "http://127.0.0.1:18888"
UI_NEWS = "http://127.0.0.1:4028/api/are/news"
ARMS = ("MICRO", "SCALP")
POLL_S = 1  # owner: respon per 1 detik (CPU masih kuat)

from strategy_v2 import simple_variants as SV  # noqa: E402
from strategy_v2 import candle_scoring as CS  # noqa: E402
from strategy_v2 import micro_v2 as MICRO_V2  # noqa: E402  (MICRO v2.1, 2026-09-11)


def get(path: str) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def post(path: str, body: dict) -> dict:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def log(line: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {line}", flush=True)
    # rev6: duplikasi ke file tetap — saat driver di-spawn detached penuh
    # (WMI, kebal penutupan Freebuff) stdout tidak tersambung ke pipa mana
    # pun; file ini satu-satunya jejak operasional. UTC sama dgn print.
    try:
        LOG_TEE.parent.mkdir(parents=True, exist_ok=True)
        if LOG_TEE.exists() and LOG_TEE.stat().st_size > 2_000_000:  # rotasi ~2MB
            LOG_TEE.replace(LOG_TEE.with_suffix(".log.1"))
        with open(LOG_TEE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now(timezone.utc).strftime('%m-%d %H:%M:%S')}] {line}\n")
    except Exception:
        pass


def write_state(open_orders: dict, last_T: int, equity: float,
                arm_state: dict, interval: int, rsi: dict = None,
                last_entry_ts: dict = None, pending_close: dict = None,
                arm_enabled: dict = None) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({
            "pid": os.getpid(),
            "last_poll_ts": int(time.time()),
            "last_bar_T": int(last_T),
            "open_orders": {a: {"ticket": o.get("ticket"), "direction": o.get("direction"),
                                "entry_ts": o.get("entry_ts") or 0, "lot": o.get("lot"),
                                "entry_usd": o.get("entry_usd"),
                                "position_id": o.get("position_id")}
                            for a, o in open_orders.items()},
            "pending_close": {a: {"ticket": o.get("ticket"), "direction": o.get("direction"),
                                  "entry_ts": o.get("entry_ts") or 0, "lot": o.get("lot"),
                                  "entry_usd": o.get("entry_usd"),
                                  "position_id": o.get("position_id")}
                              for a, o in (pending_close or {}).items()},
            "last_entry_ts": last_entry_ts or {},
            "equity": round(equity, 2),
            "interval_s": interval,
            "poll_s": interval,
            "rsi": rsi or {},
            "arms": {a: {**arm_state[a], "enabled": arm_enabled.get(a, True)}
                     for a in arm_state},
        }, ensure_ascii=True), encoding="utf-8")
    except Exception:
        pass


def fetch_news_events() -> list:
    """Kalender dari UI (read-only); gagal → [] (fail-open utk demo, dicatat)."""
    try:
        with urllib.request.urlopen(UI_NEWS, timeout=8) as r:
            return json.loads(r.read().decode()).get("calendar", {}).get("events", [])
    except Exception:
        return []


def tf_candles(tf: str, count: int) -> list:
    return get(f"/candles?symbol=XAUUSD&timeframe={tf}&count={count}").get("candles", [])


def deals_index(days: int = 7) -> list:
    """Deals dari bridge /deals (sudah memuat profit real deal close).
    Gagal → [] (matcher akan mengembalikan None = tidak ketemu)."""
    try:
        return get(f"/deals?days={days}").get("deals", [])
    except Exception:
        return []


def match_close_deal(ticket: int, deals: list, entry_ts: float = None,
                     lot: float = None, used_deals: set = None,
                     position_id: int = None) -> Optional[dict]:
    """Deal close (OUT) untuk posisi `ticket`, dengan PEMILIHAN YANG BENAR.

    Aturan pairing (bug 2026-09-10 diperbaiki):
      1. position_id eksak bila tersedia — deal close membawa position_id
         = ID posisi (= ticket order entry). TIDAK ada ambiguitas.
      2. Tanpa position_id: FIFO kronologis antara entry dan exit — deal
         OUT TERAKHIR PADA ATAU SETELAH ts posisi yang dibuka paling awal
         yang belum ter-pair (lot disamakan bila diketahui). Kandidat deal
         time = waktu server broker (bisa LEBIH MAJU dari epoch lokal
         hingga ~3 jam; toleransi -60s dipertahankan).

    return deal dict eksak (bukan hanya pnl) — pemanggil mencatat profit,
    volume, price, position_id ke journal. None bila belum ketemu —
    pemanggil WAJIB memperlakukan None sebagai "tidak diketahui" (netral).
    """
    used = used_deals if used_deals is not None else set()

    def _cands(pool: list) -> list:
        c = []
        for d in pool:
            try:
                if d.get("ticket") in used:
                    continue  # deal sudah jadi pasangan posisi lain
                if d.get("entry") in (0, "0", None, 0.0):
                    continue  # hanya deal close (OUT/INOUT/OUT_BY)
                t = float(d.get("time") or 0)
                if entry_ts and t and t < float(entry_ts) - 60:
                    continue  # sebelum posisi ini dibuka — bukan pasangannya
                if lot and d.get("volume") not in (None, 0, 0.0) \
                        and abs(float(d.get("volume")) - float(lot)) > 1e-9:
                    continue  # volume beda — posisi lain (mis. noise ARE-TEST 0.01)
                c.append(d)
            except Exception:
                continue
        return c

    # 1) position_id eksak
    if position_id:
        exact = [d for d in _cands(deals)
                 if str(d.get("position_id") or "") == str(position_id)]
        if exact:
            best = max(exact, key=lambda d: float(d.get("time") or 0))
            if used_deals is not None:
                used_deals.add(best.get("ticket"))
            return best

    # 2) FIFO antar-semua-kandidat: deal OUT kandidat paling awal menjadi
    # pasangan posisi yang dibuka paling awal (pemanggil memproses posisi
    # berurutan entry-ts; used_deals mencegah deal dipakai dua kali).
    cands = sorted(_cands(deals), key=lambda x: float(x.get("time") or 0))
    best = cands[0] if cands else None
    if best is not None:
        if used_deals is not None:
            used_deals.add(best.get("ticket"))
    return best


def close_pnl_for_ticket(ticket: int, deals: list, entry_ts: float = None,
                         lot: float = None, used_deals: set = None,
                         position_id: int = None) -> Optional[float]:
    """PnL REAL posisi tertutup — tipis di atas match_close_deal.

    (Docstring sejarah dipertahankan: MT5 TIDAK menghubungkan deal close ke
    order entry lewat field `order`; bridge dulu tidak expose position_id —
    kini expose, dan matcher memakainya bila ada.)
    """
    d = match_close_deal(ticket, deals, entry_ts, lot, used_deals,
                         position_id=position_id)
    if d is None:
        return None
    return float(d.get("profit") or 0.0)


def journal_closed_tickets(path: Path) -> set:
    """Ticket yang sudah punya event closed_detected di journal (dedupe v4)."""
    out: set = set()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("evt") == "closed_detected" and e.get("ticket") is not None:
                    out.add(int(e["ticket"]))
            except Exception:
                continue
    except Exception:
        pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=POLL_S)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    journal = OUT / "demo_journal.jsonl"

    log("== R1 DEMO DRIVER v5 (MICRO M1 / SCALP M5, poll 1s) ==")
    health = get("/health")
    if not health.get("mt5_connected"):
        log("FATAL: MT5 tidak connected")
        return 1
    acc = get("/account")
    if not acc.get("connected"):
        log("FATAL: /account tidak connected")
        return 1
    server = str(acc.get("server") or "")
    if "demo" not in server.lower():
        log(f"FATAL: akun bukan DEMO — driver menolak jalan: login={acc.get('login')} server={server}")
        return 1
    equity = float(acc.get("equity") or acc.get("balance") or 0)
    balance = float(acc.get("balance") or 0)
    log(f"akun DEMO OK: login={acc.get('login')} equity={equity:.2f}")

    kills = {a: SV.KillSwitch() for a in ARMS}

    arm_enabled: dict = {a: True for a in ARMS}  # rev5: toggle AKTIF/NONAKTIF per arm (owner)

    def sync_owner_flags() -> None:
        """Proses perintah owner dari arm_toggle.json (rev5).

        Kontrak: UI menulis {arm, enabled?/kill_override?, ts}; driver yang
        SATU-SATUNYA pembaca — apply lalu hapus file. File terpisah dari
        driver_state.json karena state itu ditulis ulang driver tiap poll
        (tulisan UI bisa hilang sebelum terbaca — race rev5 pertama).
        Dipanggil tiap iterasi loop → toggle berlaku <2 detik, tanpa restart.
        File yang tersisa saat driver mati tetap diproses saat start berikutnya.
        """
        try:
            if TOGGLE_FILE.exists():
                t = json.loads(TOGGLE_FILE.read_text(encoding="utf-8"))
                arm = str(t.get("arm") or "").upper()
                if arm in ARMS:
                    if t.get("enabled") is not None:
                        new_v = bool(t["enabled"])
                        if arm_enabled.get(arm, True) != new_v:
                            log(f"{arm}: {'AKTIF' if new_v else 'NONAKTIF'} (toggle owner)")
                        arm_enabled[arm] = new_v
                    ko = t.get("kill_override")
                    if ko is not None:
                        kills[arm].manual_override = bool(ko)
                        if not ko:  # KS nyala kembali → reset streak & cooldown
                            kills[arm].lose_streak = 0
                            kills[arm].until = 0.0
                            log(f"{arm}: kill switch ON kembali (streak reset)")
                        else:
                            log(f"{arm}: kill switch OVERRIDE (dimatikan owner)")
                try:
                    TOGGLE_FILE.unlink()
                except Exception:
                    pass
        except Exception:
            return
        # fallback lama: kill override yang ditulis langsung ke state file
        # (versi < rev5) tetap dibaca — sekali di sini tiap iterasi, murah.
        try:
            s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            for arm in ARMS:
                k = ((s.get("arms") or {}).get(arm) or {}).get("kill") or {}
                if k.get("manual_override") and not kills[arm].manual_override:
                    kills[arm].manual_override = True
        except Exception:
            pass

    sync_owner_flags()
    # persist rev3: restore posisi terbuka, cooldown, dan streak dari state
    open_orders: dict = {}
    last_entry_ts: dict = {a: None for a in ARMS}  # cooldown antar entri (MICRO 5m)
    # rev4: close menunggu deal muncul di /deals — di-retry tiap poll
    pending_close: dict = {}
    pending_since: dict = {}
    closed_tickets = journal_closed_tickets(journal)
    try:
        _s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        for arm, o in (_s.get("open_orders") or {}).items():
            if arm in ARMS and o.get("ticket"):
                open_orders[arm] = {"ticket": o["ticket"], "direction": o.get("direction"),
                                    "entry_ts": o.get("entry_ts") or 0,
                                    "lot": o.get("lot"), "missing": 0,
                                    "position_id": o.get("position_id")}
        le = _s.get("last_entry_ts") or {}
        for arm in ARMS:
            if le.get(arm):
                last_entry_ts[arm] = le[arm]
        # rev5: toggle AKTIF/NONAKTIF persisten antar restart — arm yang
        # dinonaktifkan owner TIDAK menyala diam-diam setelah restart.
        for arm in ARMS:
            en = ((_s.get("arms") or {}).get(arm) or {}).get("enabled")
            if en is not None and not bool(en):
                arm_enabled[arm] = False
                log(f"{arm}: restore NONAKTIF (toggle owner sebelum restart)")
        for arm, o in (_s.get("pending_close") or {}).items():
            if arm in ARMS and o.get("ticket"):
                pending_close[arm] = {"ticket": o["ticket"], "direction": o.get("direction"),
                                      "entry_ts": o.get("entry_ts") or 0, "lot": o.get("lot"),
                                      "entry_usd": o.get("entry_usd"),
                                      "position_id": o.get("position_id")}
                pending_since[arm] = int(time.time())  # restart → window retry penuh lagi
        for arm in ARMS:
            k = ((_s.get("arms") or {}).get(arm) or {}).get("kill") or {}
            kills[arm].lose_streak = int(k.get("lose_streak") or 0)
            kills[arm].until = float(k.get("until") or 0)
        if open_orders or any(last_entry_ts.values()):
            log(f"state restore: open_orders={ {a: o['ticket'] for a, o in open_orders.items()} } "
                f"last_entry={last_entry_ts}")
    except FileNotFoundError:
        pass
    except Exception as e:
        log(f"restore state gagal (mulai bersih): {e}")
    # konfirmasi close 2 poll: hitung poll berturut-turut posisi tak terlihat
    missing_count: dict = {a: 0 for a in ARMS}
    used_deals: set = set()  # ticket deal close yang sudah dipakai satu arm
    deals_cache: list = []
    deals_cache_ts: float = 0.0
    arm_state = {a: {"last_decision": None, "last_check_ts": 0,
                     "context": None,
                     "kill": {"lose_streak": 0, "until": 0, "manual_override": False}}
                 for a in ARMS}
    # last_T per TF: waktu bar FORMING saat ini. None → siklus pertama langsung
    # mengevaluasi bar close terakhir masing-masing TF.
    last_T: dict = {"M1": None, "M5": None, "M15": None}
    rsi_cache: dict = {}
    write_state(open_orders, 0, equity, arm_state, args.interval, rsi_cache, last_entry_ts, pending_close, arm_enabled)
    log(f"loop demo mulai (poll {args.interval}s) — CTRL-C untuk stop")

    while True:
        time.sleep(args.interval)
        now_epoch = int(time.time())

        # rev5: perintah owner (toggle arm / kill override) diproses TIAP
        # iterasi — toggle dari UI berlaku maksimal ~1-2 detik tanpa restart.
        sync_owner_flags()

        # ── fetch ringan tiap detik: M1 (trigger MICRO) ──
        try:
            m1_now = tf_candles("M1", 3)
        except Exception as e:
            log(f"bridge error: {e} — retry detik berikutnya")
            continue
        if not m1_now:
            continue

        news = fetch_news_events()
        m1_trigger = False
        newest_m1 = int(m1_now[-1]["time"])
        if last_T["M1"] is None or newest_m1 > last_T["M1"]:
            m1_trigger = True
            last_T["M1"] = newest_m1

        # trigger M5/M15/M1 lainnya dicek murah dari waktu epoch (bar boundaries
        # broker bisa bergeser dari epoch — dicek dari data, bukan asumsi)
        need_refresh = {"M1": m1_trigger, "M5": False, "M15": False}

        # M5 trigger: cek bar forming M5 (fetch 2 bar)
        try:
            m5_probe = tf_candles("M5", 2)
            newest_m5 = int(m5_probe[-1]["time"])
            if last_T["M5"] is None or newest_m5 > last_T["M5"]:
                need_refresh["M5"] = True
                last_T["M5"] = newest_m5
            m15_probe = tf_candles("M15", 2)
            newest_m15 = int(m15_probe[-1]["time"])
            if last_T["M15"] is None or newest_m15 > last_T["M15"]:
                need_refresh["M15"] = True
                last_T["M15"] = newest_m15
        except Exception as e:
            log(f"probe error: {e} — skip siklus")
            continue

        if not any(need_refresh.values()):
            # tulis ulang state dengan RSI TERAKHIR yang dihitung (cache) —
            # jangan kosongkan panel RSI UI antara dua bar close
            write_state(open_orders, last_T["M1"] or 0, equity, arm_state, args.interval, rsi_cache, last_entry_ts, pending_close, arm_enabled)
            continue

        # ── data penuh — BUANG bar forming (aturan owner: wajib close bar) ──
        try:
            m1_raw = tf_candles("M1", 400) if need_refresh["M1"] else None
            m5_raw = tf_candles("M5", 400) if (need_refresh["M5"] or need_refresh["M1"]) else None
            m15_raw = tf_candles("M15", 300) if (need_refresh["M15"] or need_refresh["M1"]) else None
            h4_raw = tf_candles("H4", 120)
        except Exception as e:
            log(f"candles error: {e} — skip bar")
            continue

        m1 = m1_raw[:-1] if m1_raw and len(m1_raw) >= 30 else None
        m5 = m5_raw[:-1] if m5_raw and len(m5_raw) >= 30 else None
        m15 = m15_raw[:-1] if m15_raw and len(m15_raw) >= 30 else None
        h4 = h4_raw[:-1] if h4_raw and len(h4_raw) >= 5 else []
        if m15 is None:
            log("data M15 terlalu pendek — skip")
            continue
        if m5 is None and not m1:
            log("data M5 terlalu pendek — skip")
            continue

        try:
            acc = get("/account")
            equity = float(acc.get("equity") or 0)
            balance = float(acc.get("balance") or equity)
        except Exception:
            pass

        # cek posisi tertutup → PnL REAL dari /deals → kill switch streak.
        # rev3: close butuh KONFIRMASI 2 poll (hilang 1x = gagal-baca sesaat,
        # bukan close). rev4: pnl tidak pernah ditulis null seketika — close
        # masuk pending_close dan di-retry sampai deal ketemu di /deals.
        if open_orders:
            try:
                pos = get("/positions")
                live_tickets = set()
                for p in pos.get("positions", []):
                    try:
                        live_tickets.add(int(p.get("ticket") or 0))
                    except Exception:
                        continue
                for arm in sorted(list(open_orders),
                                  key=lambda a: (open_orders[a].get("entry_ts") or 0)):
                    o = open_orders[arm]
                    if int(o.get("ticket") or 0) in live_tickets:
                        missing_count[arm] = 0
                        continue
                    missing_count[arm] = missing_count.get(arm, 0) + 1
                    if missing_count[arm] < 2:
                        continue  # tunggu poll berikutnya untuk konfirmasi
                    open_orders.pop(arm, None)
                    missing_count[arm] = 0
                    # rev4: JANGAN tulis event sekarang — deal close sering
                    # telat masuk /deals → pnl null selamanya (bug "+0.00").
                    # Pindah ke pending, di-retry di blok bawah.
                    pending_close[arm] = o
                    pending_since[arm] = now_epoch
            except Exception as e:
                log(f"position poll error: {e}")

        # resolve pending close: retry match deal sampai ketemu (maks 15
        # menit → null + unresolved:true, tetap netral). Event ditulis SEKALI
        # saat pnl sudah diketahui — journal tidak pernah diubah mundur.
        if pending_close:
            try:
                if not deals_cache or now_epoch - deals_cache_ts > 30:
                    deals_cache = deals_index(7)
                    deals_cache_ts = now_epoch
                for arm in sorted(list(pending_close),
                                  key=lambda a: pending_since.get(a, 0)):
                    o = pending_close[arm]
                    # MATCH SEKALI — deal pasangan eksak (position_id / FIFO);
                    # pnl diambil dari deal yang sama (bukan match kedua yang
                    # bisa mencuri deal arm lain via used_deals).
                    dj = match_close_deal(o["ticket"], deals_cache,
                                          o.get("entry_ts"), o.get("lot"),
                                          used_deals,
                                          position_id=o.get("position_id"))
                    timed_out = (now_epoch - pending_since.get(arm, now_epoch)) > 900
                    if dj is None and not timed_out:
                        continue  # deal belum tercatat — coba poll berikutnya
                    pnl = float(dj.get("profit") or 0.0) if dj else None
                    if pnl is None:
                        log(f"{arm}: posisi {o['ticket']} close tak ter-resolver "
                            f"15 menit — dicatat null (unresolved, netral)")
                    elif pnl < 0:
                        kills[arm].record_loss(time.time())
                        log(f"{arm}: LOSS {pnl:.2f} — streak {kills[arm].lose_streak}")
                        if kills[arm].blocked(time.time()):
                            log(f"{arm}: KILL SWITCH — jeda {kills[arm].remaining_min(time.time())} menit")
                    else:
                        kills[arm].record_win()
                        log(f"{arm}: WIN {pnl:.2f} — streak reset")
                    if int(o["ticket"]) not in closed_tickets:
                        closed_tickets.add(int(o["ticket"]))
                        ev = {"evt": "closed_detected", "arm": arm,
                              "ticket": o["ticket"],
                              "pnl": pnl,  # None = tidak diketahui (netral)
                              "pnl_usd": dj.get("profit") if dj else None,
                              "vol": (dj or {}).get("volume"),
                              "close_usd": (dj or {}).get("price"),
                              "close_position_id": (dj or {}).get("position_id"),
                              "entry_usd": o.get("entry_usd"),
                              "ts": now_epoch}
                        if pnl is None:
                            ev["unresolved"] = True
                        with open(journal, "a", encoding="utf-8") as f:
                            f.write(json.dumps(ev, ensure_ascii=True) + "\n")
                    else:
                        log(f"{arm}: close {o['ticket']} sudah ada di journal — skip (dedupe)")
                    pending_close.pop(arm, None)
                    pending_since.pop(arm, None)
            except Exception as e:
                log(f"pending close error: {e}")

        # ── MICRO: evaluasi tiap close M1 ──
        if need_refresh["M1"] and m1 and m5:
            _run_arm("MICRO", m1, m5, m15, h4, balance, news, now_epoch,
                     kills, open_orders, arm_state, journal, last_entry_ts,
                     arm_enabled)
        # ── SCALP: evaluasi tiap close M5 ──
        if need_refresh["M5"] and m5:
            _run_arm("SCALP", m1, m5, m15, h4, balance, news, now_epoch,
                     kills, open_orders, arm_state, journal, last_entry_ts,
                     arm_enabled)

        for a in ARMS:
            arm_state[a]["kill"] = kills[a].to_dict()
        # RSI per TF — SELALU dihitung & ditampilkan (owner request), terlepas
        # dari gate mana yang menolak. Nilai sama utk kedua arm (market sama).
        rsi_state = {}
        for tf_name, bars_tf in (("M15", m15), ("M5", m5), ("M1", m1)):
            if bars_tf and len(bars_tf) >= 15:
                v = CS.rsi([b["close"] for b in bars_tf], 14)
                if v is not None:
                    rsi_state[tf_name] = round(v, 1)
        if rsi_state:
            rsi_cache = rsi_state
        write_state(open_orders, last_T["M1"] or 0, equity, arm_state, args.interval, rsi_cache, last_entry_ts, pending_close, arm_enabled)
        if args.once:
            log("--once: satu siklus selesai, keluar")
            return 0


def _run_arm(arm: str, m1, m5, m15, h4, balance, news, now_epoch,
             kills, open_orders, arm_state, journal, last_entry_ts: dict,
             enabled: dict) -> None:
    """Satu evaluasi arm + order bila lolos.

    Pembacaan candle per TF (M1/M5/M15: pola + poin) SELALU dihitung dan
    disimpan — juga saat arm WAIT di gate awal — supaya panel MULTI-TF di UI
    tidak pernah kosong (owner: tampilkan juga di UI)."""
    # rev5: arm dinonaktifkan owner (toggle UI) — tidak dievaluasi, tidak
    # order. Posisi terbuka TIDAK disentuh (dikelola broker SL/TP).
    if not enabled.get(arm, True):
        arm_state[arm]["last_decision"] = {
            "ok": False, "reason": "NONAKTIF oleh owner (toggle arm)",
            "steps": [], "checklist": [], "score": 0.0,
            "direction": None, "pattern": None, "ts": now_epoch,
        }
        return
    try:
        if arm == "MICRO":
            # MICRO v2.1 "SCALP-M1 0.9/1.4" (owner 2026-09-11, hipotesis
            # MICRO-V2.1-0.9-1.4) — replika persis studi offline
            # (scripts/micro_v2_study.py varian v1.0|65_35|M0.9_T1.4).
            dec = MICRO_V2.decide(m5, m1, balance, now_epoch=now_epoch,
                                  kill=kills[arm],
                                  last_entry_ts=last_entry_ts.get(arm))
        else:
            dec = SV.decide(arm, m5, m15, h4, balance,
                            news_events=news, now_epoch=now_epoch, kill=kills[arm],
                            m1_bars=None,
                            last_entry_ts=last_entry_ts.get(arm))
    except Exception as e:
        log(f"{arm}: decide error: {e}")
        dec = {"ok": False, "reason": f"error: {e}", "steps": [], "checklist": []}
    arm_state[arm]["last_decision"] = {
        "ok": dec.get("ok", False), "reason": dec.get("reason", ""),
        "steps": dec.get("steps", []), "checklist": dec.get("checklist", []),
        "score": dec.get("score", 0.0), "direction": dec.get("direction"),
        "pattern": dec.get("pattern"),
        "ts": now_epoch,
    }
    ctx = dec.get("context")
    if not ctx:
        # fallback: hitung mandiri (tetap tampil saat WAIT di gate awal)
        ctx = {}
        if arm == "MICRO" and m1 and len(m1) >= 3:
            ctx["M1"] = CS.context_points(m1)
        if m5 and len(m5) >= 3:
            ctx["M5"] = CS.context_points(m5)
        if m15 and len(m15) >= 3:
            ctx["M15"] = CS.context_points(m15)
    arm_state[arm]["context"] = ctx
    arm_state[arm]["last_check_ts"] = now_epoch
    if not dec.get("ok"):
        return
    if arm in open_orders:
        return
    # order market
    try:
        resp = post("/order", {
            "symbol": "XAUUSD", "direction": dec["direction"],
            "lot": dec["lot"], "sl_points": dec["sl_points"],
            "tp_points": dec["tp_points"], "comment": f"R1-{arm}"})
        if not resp.get("success"):
            raise RuntimeError(resp.get("error") or str(resp))
        ticket = resp.get("ticket") or resp.get("order_ticket")
        log(f"{arm}: {dec['direction']} {dec['lot']} lot (skor {dec['score']:.0f}, "
            f"pola {dec.get('pattern')}, SL {dec['sl_points']} / TP {dec['tp_points']}) "
            f"-> ticket {ticket}")
        entry_usd = resp.get("price") or resp.get("price_open")
        # position_id: bridge kini mengembalikan ID posisi (verifikasi
        # positions_get) — fallback ticket (order entry = position id di MT5)
        position_id = resp.get("position_id") or ticket
        with open(journal, "a", encoding="utf-8") as f:
            f.write(json.dumps({"evt": "open", "arm": arm, "ts": now_epoch,
                                "decision": dec["direction"], "pattern": dec.get("pattern"),
                                "score": dec.get("score"), "lot": dec["lot"],
                                "sl_points": dec["sl_points"], "tp_points": dec["tp_points"],
                                "ticket": ticket, "entry_usd": entry_usd,
                                "checklist": dec.get("checklist", [])},
                               ensure_ascii=True) + "\n")
        open_orders[arm] = {"ticket": ticket, "direction": dec["direction"],
                            "entry_ts": now_epoch, "lot": dec.get("lot"),
                            "entry_usd": entry_usd, "position_id": position_id}
        last_entry_ts[arm] = now_epoch  # mulai hitung cooldown antar entri
    except Exception as e:
        log(f"{arm}: order GAGAL: {e}")
        with open(journal, "a", encoding="utf-8") as f:
            f.write(json.dumps({"evt": "order_failed", "arm": arm, "ts": now_epoch,
                                "error": str(e)}, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    sys.exit(main())
