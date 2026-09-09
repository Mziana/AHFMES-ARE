"""Track B (B2–B6) — infrastruktur eksekusi shadow-only, strategy-agnostic.

Kontrak final yang dijaga di sini (disepakati owner & reviewer):

- STRATEGI INDEPENDEN, KAPITAL DEPENDEN: kuota per profil (slot/risk/daily
  loss) di-enforce oleh CSK via csk_risk_budget_for(); adapter konsultasi
  SEBELUM emit intent. CSK global tetap satu kebenaran (evaluate_action).
- REAL ORDER = OFF ARSITEKTURAL: modul ini tidak mengimpor gateway order-real
  engine lama; ShadowGateway satu-satunya implementasi gateway di dependency
  graph. MT5 data-in BOLEH (harga/snapshot), pengiriman order TIDAK ADA.
- Kill switch + flatten_all() DI GATEWAY LAYER (interface yang sama nanti
  dipakai gateway real).
- Latency first-class: rantai t_signal→t_decision→t_risk→t_intent→t_submit→
  t_ack→t_fill; hard-fail >= 1 bar M5 (sampel dibuang dari parity), viability
  gate P99 decision→ack <= LATENCY_VIABILITY_P99_S (5 detik).
- Parity: toleransi harga max(1 point, tick_size snapshot broker).

Fail-closed di setiap state; tanpa exception tersimpan diam-diam.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from are.safety import CapitalSafetyKernel, SafetyLimits, SafetyDecision  # noqa: E402

STRATEGY_ROOT = "strategy_v2"
STRATEGY_VERSION = "strategy_v2/0.4.2-b2"
ONE_BAR_M5_S = 300
LATENCY_VIABILITY_P99_S = 5.0
PARITY_TICK_FLOOR = 0.01  # 1 point XAUUSD (0.01 harga) — floor, bukan pengganti tick_size broker


# ─────────────────────────────────────────────────────────────────────────────
# CSK: risk budget per profil (WAJIB #10) — di-enforce oleh CSK, bukan adapter
# ─────────────────────────────────────────────────────────────────────────────
PROFILE_RISK_BUDGET_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "MICRO_V2": {"max_open_positions": 1, "max_risk_usd_per_trade": 30.0, "max_daily_loss_usd": 90.0},
    "SCALP_V2": {"max_open_positions": 1, "max_risk_usd_per_trade": 45.0, "max_daily_loss_usd": 120.0},
}


class CskProfileBudgetDenied(Exception):
    """Fail-closed: profil tak dikenal / budget tidak ditemukan."""


def csk_risk_budget_for(csk: CapitalSafetyKernel, profile_id: str) -> Dict[str, Any]:
    """Kuota per profil DI BAWAH CSK — satu titik kebenaran (fungsi CSK-bound).

    Budget per profil membaca limits CSK (bukan angka bebas), lalu membagi
    quota dengan konvensi terdokumentasi (MICRO:SCALP = 60:40 dari max lot CSK).
    """
    budget = PROFILE_RISK_BUDGET_DEFAULTS.get(profile_id)
    if budget is None:
        raise CskProfileBudgetDenied(f"profil '{profile_id}' tidak terdaftar di risk budget CSK")
    out = dict(budget)
    out["csk_max_position_size"] = float(csk.limits.max_position_size)
    out["csk_max_drawdown_pct"] = float(csk.limits.max_drawdown_pct)
    out["csk_max_order_rate_per_min"] = int(csk.limits.max_order_rate_per_min)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# B2 — ExecutionIntent + Decision Adapter (murni, deterministik)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ExecutionIntent:
    """Kontrak eksekusi: satu-satunya bentuk yang lintas layer (B2→B6).

    field `profile_id` sejak hari pertama (kuota per profil, aktivasi Fase 2).
    """
    intent_id: str
    profile_id: str
    symbol: str
    direction: str              # "BUY" | "SELL"
    lot: float
    entry_est: float
    sl_points: float
    tp_points: float
    signal_ts: int
    decision_ts: int
    config_hash: str
    dataset_hash: str
    strategy_version: str
    hypothesis_registry_id: str
    provenance: Dict[str, Any] = field(default_factory=dict)


def _require_finite(x: Any, name: str) -> float:
    v = float(x)
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{name} tidak finite: {x}")
    return v


def decision_to_intent(record: Dict[str, Any], profile_id: str,
                       symbol: str = "XAUUSD", tick_size: float = PARITY_TICK_FLOOR) -> ExecutionIntent:
    """B2 — StrategyDecision record (replay) -> ExecutionIntent. Murni.

    Fail-closed: hanya decision BUY/SELL dengan SL valid yang menjadi intent;
    selain itu ValueError (dipanggil adapter loop yang menangkapnya).
    """
    decision = str(record.get("decision", "")).upper()
    if decision not in ("BUY", "SELL"):
        raise ValueError(f"decision '{decision}' bukan order intent")
    sl_pts = _require_finite(record.get("sl_points"), "sl_points")
    tp_pts = _require_finite(record.get("tp_points"), "tp_points")
    lot = _require_finite(record.get("lot"), "lot")
    if sl_pts <= 0 or tp_pts <= 0 or lot <= 0:
        raise ValueError("sl/tp/lot wajib positif")
    signal_ts = int(record.get("signal_ts") or record.get("evaluation_timestamp"))
    decision_ts = int(record.get("evaluation_timestamp"))
    if decision_ts < signal_ts:
        raise ValueError("decision_ts < signal_ts — sinyal dari masa depan?")
    entry_est = record.get("entry_est")
    entry = _require_finite(entry_est, "entry_est") if entry_est is not None else 0.0
    return ExecutionIntent(
        intent_id="I-" + hashlib.sha256(
            json.dumps([signal_ts, decision, sl_pts, tp_pts, lot, profile_id],
                       sort_keys=True).encode()).hexdigest()[:16],
        profile_id=profile_id, symbol=symbol, direction=decision,
        lot=round(lot, 2), entry_est=entry,
        sl_points=sl_pts, tp_points=tp_pts,
        signal_ts=signal_ts, decision_ts=decision_ts,
        config_hash=str(record.get("config_hash", "")),
        dataset_hash=str(record.get("dataset_hash", "")),
        strategy_version=str(record.get("strategy_version", "")),
        hypothesis_registry_id=str(record.get("hypothesis_registry_id", "")),
        provenance={"quality_score": (record.get("quality_score") or {}).get("final_score")
                    if isinstance(record.get("quality_score"), dict) else None,
                    "first_veto_reason": record.get("first_veto_reason"),
                    "bias": record.get("bias")},
    )


# ─────────────────────────────────────────────────────────────────────────────
# B2 — adapter loop dengan konsultasi CSK (slot + budget per profil)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ProfileRuntimeState:
    open_positions: int = 0
    daily_loss_usd: float = 0.0


class DecisionAdapter:
    """Loop adapter: record -> consult CSK -> intent (atau ditolak terlog)."""

    def __init__(self, csk: CapitalSafetyKernel, tick_size: float = PARITY_TICK_FLOOR):
        self.csk = csk
        self.tick_size = float(tick_size)
        self.state: Dict[str, ProfileRuntimeState] = {}
        self.rejections: List[Dict[str, Any]] = []

    def submit(self, record: Dict[str, Any], profile_id: str,
               budget: Optional[Dict[str, Any]] = None) -> Optional[ExecutionIntent]:
        try:
            intent = decision_to_intent(record, profile_id, tick_size=self.tick_size)
        except Exception as e:
            self.rejections.append({"reason": "ADAPTER_INVALID", "detail": str(e),
                                    "ts": record.get("evaluation_timestamp")})
            return None
        budget = budget or csk_risk_budget_for(self.csk, profile_id)
        st = self.state.setdefault(profile_id, ProfileRuntimeState())
        if st.open_positions >= int(budget["max_open_positions"]):
            self.rejections.append({"reason": "PROFILE_SLOT_FULL", "profile_id": profile_id,
                                    "ts": intent.signal_ts})
            return None
        if st.daily_loss_usd >= float(budget["max_daily_loss_usd"]):
            self.rejections.append({"reason": "PROFILE_DAILY_LOSS_CAP", "profile_id": profile_id,
                                    "ts": intent.signal_ts})
            return None
        if intent.lot * self.tick_size * 100 > budget["max_risk_usd_per_trade"] * 100:
            self.rejections.append({"reason": "PROFILE_RISK_CAP", "profile_id": profile_id,
                                    "ts": intent.signal_ts})
            return None
        return intent


# ─────────────────────────────────────────────────────────────────────────────
# B3 — Execution State Machine (transisi eksplisit, fail-closed)
# ─────────────────────────────────────────────────────────────────────────────
STATES = ("IDLE", "INTENT_VALIDATED", "CSK_CHECKED", "SUBMITTED",
          "ACKNOWLEDGED", "FILLED", "MANAGING", "CLOSED", "REJECTED", "ABORTED")


class ExecutionStateMachine:
    """Transisi eksplisit; state ilegal -> ValueError (fail-closed)."""

    TRANSITIONS: Dict[str, tuple] = {
        "IDLE": ("INTENT_VALIDATED",),
        "INTENT_VALIDATED": ("CSK_CHECKED", "REJECTED"),
        "CSK_CHECKED": ("SUBMITTED", "REJECTED"),
        "SUBMITTED": ("ACKNOWLEDGED", "REJECTED"),
        "ACKNOWLEDGED": ("FILLED", "ABORTED"),
        "FILLED": ("MANAGING", "CLOSED"),
        "MANAGING": ("CLOSED",),
        "CLOSED": ("IDLE",),
        "REJECTED": ("IDLE",),
        "ABORTED": ("IDLE",),
    }
    TERMINAL = ("CLOSED", "REJECTED", "ABORTED")

    def __init__(self, intent_id: str):
        self.intent_id = intent_id
        self.state = "IDLE"
        self.history: List[Dict[str, Any]] = [{"state": "IDLE", "ts": time.time()}]

    def transition(self, to: str, detail: Optional[Dict[str, Any]] = None) -> str:
        if to not in STATES:
            raise ValueError(f"state '{to}' tidak dikenal")
        if to not in self.TRANSITIONS[self.state]:
            raise ValueError(f"transisi ilegal {self.state} -> {to} (intent {self.intent_id})")
        self.state = to
        self.history.append({"state": to, "ts": time.time(), "detail": detail or {}})
        return self.state

    def is_terminal(self) -> bool:
        return self.state in self.TERMINAL


# ─────────────────────────────────────────────────────────────────────────────
# B4 — ShadowGateway (satu-satunya gateway; kill switch + flatten_all di sini)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ShadowFill:
    intent_id: str
    fill_ts: int                 # epoch sim (bar-based, bukan wall-clock)
    fill_price: float
    submitted_price: float
    slippage_points: float
    latency: Dict[str, float]    # segmen rantai latency (detik, simulasi)


class ShadowGateway:
    """Gateway bayangan: simulated submit/fill terhadap data pasar nyata.

    - TIDAK ADA order ke broker (tidak ada import gateway real di modul ini).
    - fill sim: bar berikutnya (kontrak next-bar-open), harga = open bar berikut
      +- slippage poin; spread/slip dilaporkan, bukan disembunyikan.
    - flatten_all() + kill switch tersedia di interface yang sama dengan
      gateway real masa depan.
    """

    def __init__(self, m5_bars: List[Dict[str, Any]], point_size: float = 0.01,
                 kill_switch_active: bool = False):
        self._bars = sorted(m5_bars, key=lambda b: int(b["time"]))
        self._times = [int(b["time"]) for b in self._bars]
        self.point = float(point_size)
        self.kill_switch_active = bool(kill_switch_active)
        self.open_shadows: Dict[str, ShadowFill] = {}
        self.flatten_log: List[Dict[str, Any]] = []

    def _next_bar_open(self, ts: int) -> Optional[Dict[str, Any]]:
        lo, hi, idx = 0, len(self._times) - 1, None
        while lo <= hi:
            mid = (lo + hi) // 2
            if self._times[mid] > ts:
                idx = mid
                hi = mid - 1
            else:
                lo = mid + 1
        return self._bars[idx] if idx is not None else None

    def submit(self, intent: ExecutionIntent, latency: Optional[Dict[str, float]] = None
               ) -> ShadowFill:
        """submit: simulated submit -> simulated fill (next bar open)."""
        if self.kill_switch_active:
            raise RuntimeError("KILL_SWITCH_ACTIVE — submit ditolak (fail-closed)")
        bar = self._next_bar_open(intent.decision_ts)
        if bar is None:
            raise ValueError("tidak ada bar berikutnya untuk fill simulasi")
        open_px = float(bar["open"])
        slip = 0.0
        fill_px = open_px
        if intent.direction == "BUY":
            fill_px = open_px + slip * self.point
        else:
            fill_px = open_px - slip * self.point
        fill = ShadowFill(
            intent_id=intent.intent_id, fill_ts=int(bar["time"]),  # fill di OPEN bar berikutnya
            fill_price=round(fill_px, 2), submitted_price=intent.entry_est or open_px,
            slippage_points=slip,
            latency=latency or {"decision": 0.0, "risk": 0.0, "submit": 0.0,
                                "ack": 0.0, "fill": 0.0},
        )
        self.open_shadows[intent.intent_id] = fill
        return fill

    def flatten_all(self, reason: str = "OPERATOR") -> Dict[str, Any]:
        """Kill switch path: tutup semua posisi bayangan — tersedia selalu."""
        n = len(self.open_shadows)
        self.flatten_log.append({"ts": time.time(), "reason": reason, "closed": n})
        self.open_shadows.clear()
        self.kill_switch_active = True
        return {"flattened": n, "kill_switch_active": True, "reason": reason}

    def resume(self) -> None:
        self.kill_switch_active = False


# ─────────────────────────────────────────────────────────────────────────────
# B6 — latency instrumentation (distribusi P50/P95/P99/MAX per segmen)
# ─────────────────────────────────────────────────────────────────────────────
def percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = max(0, min(len(sorted_vals) - 1, int(round(p / 100.0 * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


def latency_report(samples: List[Dict[str, float]]) -> Dict[str, Any]:
    """samples: [{decision, risk, submit, ack, fill}...] — detik per segmen."""
    segs = ("decision", "risk", "submit", "ack", "fill")
    rep: Dict[str, Any] = {"n": len(samples), "segments": {}, "validity": {}}
    totals: List[float] = []
    for s in samples:
        totals.append(sum(float(s.get(k, 0.0)) for k in segs))
    totals.sort()
    for seg in segs:
        vals = sorted(float(s.get(seg, 0.0)) for s in samples)
        rep["segments"][seg] = {"p50": round(percentile(vals, 50), 6),
                                "p95": round(percentile(vals, 95), 6),
                                "p99": round(percentile(vals, 99), 6),
                                "max": round(vals[-1] if vals else 0.0, 6)}
    rep["total"] = {"p50": round(percentile(totals, 50), 6),
                    "p95": round(percentile(totals, 95), 6),
                    "p99": round(percentile(totals, 99), 6),
                    "max": round(totals[-1] if totals else 0.0, 6)}
    decision_to_ack = sorted(float(s.get("decision", 0.0)) + float(s.get("risk", 0.0))
                             + float(s.get("submit", 0.0)) + float(s.get("ack", 0.0))
                             for s in samples)
    p99_da = percentile(decision_to_ack, 99)
    rep["validity"] = {
        "hard_fail_bar_limit_s": ONE_BAR_M5_S,
        "samples_over_hard_limit": sum(1 for t in totals if t >= ONE_BAR_M5_S),
        "decision_to_ack_p99_s": round(p99_da, 6),
        "viability_gate": "PASS" if p99_da <= LATENCY_VIABILITY_P99_S else "FAIL",
        "viability_threshold_s": LATENCY_VIABILITY_P99_S,
    }
    return rep


# ─────────────────────────────────────────────────────────────────────────────
# B5 — parity replay vs shadow
# ─────────────────────────────────────────────────────────────────────────────
def parity_tolerance(tick_size: float) -> float:
    return max(PARITY_TICK_FLOOR, float(tick_size))


def parity_check(replay_trades: List[Dict[str, Any]], shadow_trades: List[Dict[str, Any]],
                 tick_size: float = PARITY_TICK_FLOOR) -> Dict[str, Any]:
    """Urutan trade harus identik (signal_ts, arah, lot); harga toleransi tick.

    Ketentuan: sampel dengan total latency >= 1 bar dibuang dari parity
    (dilakukan penelepon saat membangun shadow_trades — kolom `parity_valid`).
    """
    tol = parity_tolerance(tick_size)
    a = [t for t in replay_trades if not t.get("parity_valid", True) is False]
    b = [t for t in shadow_trades if not t.get("parity_valid", True) is False]
    report: Dict[str, Any] = {"tolerance_price": tol, "n_replay": len(a), "n_shadow": len(b)}
    if len(a) != len(b):
        report["match"] = False
        report["reason"] = f"jumlah trade beda: replay={len(a)} shadow={len(b)}"
        return report
    mismatches = []
    for i, (ta, tb) in enumerate(zip(a, b)):
        diffs = {}
        if int(ta.get("signal_ts", 0)) != int(tb.get("signal_ts", 0)):
            diffs["signal_ts"] = [ta.get("signal_ts"), tb.get("signal_ts")]
        if str(ta.get("direction")) != str(tb.get("direction")):
            diffs["direction"] = [ta.get("direction"), tb.get("direction")]
        if abs(float(ta.get("lot", 0)) - float(tb.get("lot", 0))) > 1e-9:
            diffs["lot"] = [ta.get("lot"), tb.get("lot")]
        if ta.get("entry") is not None and tb.get("entry") is not None:
            if abs(float(ta["entry"]) - float(tb["entry"])) > tol:
                diffs["entry"] = [ta.get("entry"), tb.get("entry")]
        if diffs:
            mismatches.append({"index": i, "diffs": diffs})
    report["match"] = not mismatches
    report["mismatches"] = mismatches[:20]
    return report


def results_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True,
                                     default=str).encode()).hexdigest()
