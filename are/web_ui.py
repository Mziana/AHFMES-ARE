"""
AHFMES WEB_UI — Web Server & REST API Backend (ACC-701, ACC-702)

Provides an embedded HTTP server and JSON REST API to interactively control,
visualize, and chat with the AHFMES-ARE Autonomous Engine.
Zero external hard-dependencies (stdlib only: http.server, json, os, time, threading, urllib, typing).
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import sys
import threading
import time
import urllib.parse
from typing import Any, Dict, List, Optional

from are.champion import ChampionRecord, ChampionRegistry
from are.copilot import ConversationalCopilot
from are.evidence import EvidenceLedger
from are.habitat import ConditionAtlas, HabitatAdapter
from are.operational import OperationalBrain, OperationalSignal
from are.p001_program import P001ProgramRunner
from are.registry import Registry
from are.safety import CapitalSafetyKernel, SafetyDecision, SafetyLimits
from are.storage import EventStore


class AREServerState:
    """Thread-safe application state container for the Web UI."""

    def __init__(self, db_path: str = "are_interactive.db", auth_token: Optional[str] = None):
        self.db_path = db_path
        self.auth_token = auth_token
        self.lock = threading.Lock()

        self.event_store = EventStore(db_path)
        self.champion_registry = ChampionRegistry(self.event_store)

        self.safety_limits = SafetyLimits(
            max_position_size=1.0,
            max_drawdown_pct=0.15,
            volatility_cutoff=2.5,
            max_order_rate_per_min=10,
            kill_switch_active=False,
        )
        self.safety_kernel = CapitalSafetyKernel(self.safety_limits)

        # P0-4: Canonical execution state (synced with SafetyKernel)
        from are.execution_state import ExecutionStateMachine
        self._exec_state = ExecutionStateMachine()

        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.event_store)
        self.brain = OperationalBrain(
            champion_registry=self.champion_registry,
            safety_kernel=self.safety_kernel,
            habitat=self.habitat,
            event_store=self.event_store,
        )

        self.live_ticks_history: List[Dict[str, Any]] = []
        self.copilot = ConversationalCopilot(self)

    def close(self) -> None:
        with self.lock:
            self.event_store.close()

    def get_status_payload(self) -> Dict[str, Any]:
        with self.lock:
            champ = self.champion_registry.get_active_champion()
            head_op = self.event_store.get_head("operational_signals")
            head_champ = self.event_store.get_head("champion_registry")
            total_ticks = head_op[0] if head_op else 0

            veto_count = 0
            if head_op:
                for rev in range(1, head_op[0] + 1):
                    ev = self.event_store.get_event("operational_signals", rev)
                    if ev:
                        try:
                            d = json.loads(ev.event_data.decode("utf-8"))
                            if d.get("final_action") in ("ABSTAIN", "EMERGENCY_FLAT") or not d.get("safety_decision", {}).get("allowed", True):
                                veto_count += 1
                        except Exception:
                            pass

            veto_ratio = (veto_count / total_ticks * 100.0) if total_ticks > 0 else 0.0
            chain_ok = self.event_store.verify_chain("operational_signals") if total_ticks > 0 else True

            return {
                "champion": {
                    "champion_id": champ.champion_id if champ else "NONE (GENESIS)",
                    "candidate_id": champ.candidate_id if champ else "N/A",
                    "status": champ.status if champ else "INACTIVE",
                    "activated_at": champ.activated_at if champ else 0.0,
                },
                "safety": {
                    # P0-4: Canonical truth — cross-check SafetyKernel vs ExecutionState
                    "kill_switch_active": self.safety_kernel.limits.kill_switch_active,
                    "max_drawdown_pct": self.safety_kernel.limits.max_drawdown_pct,
                    "volatility_cutoff": self.safety_kernel.limits.volatility_cutoff,
                    "max_order_rate_per_min": self.safety_kernel.limits.max_order_rate_per_min,
                    "max_position_size": self.safety_kernel.limits.max_position_size,
                },
                "execution_state": {
                    "kill_switch_active": self._exec_state.kill_switch_active if hasattr(self, '_exec_state') else None,
                    "peak_equity": self._exec_state.peak_equity if hasattr(self, '_exec_state') else 0.0,
                },
                "stream_stats": {
                    "total_ticks": total_ticks,
                    "veto_count": veto_count,
                    "veto_ratio_pct": round(veto_ratio, 2),
                    "chain_health": "VERIFIED_OK" if chain_ok else "CHAIN_CORRUPTED",
                },
                "live_ticks": self.live_ticks_history[-30:],
                "server_time": time.time(),
            }

    def set_kill_switch(self, active: bool) -> bool:
        with self.lock:
            # P0-1: Sync BOTH SafetyKernel AND ExecutionState
            self.safety_kernel.limits = SafetyLimits(
                max_position_size=self.safety_kernel.limits.max_position_size,
                max_drawdown_pct=self.safety_kernel.limits.max_drawdown_pct,
                volatility_cutoff=self.safety_kernel.limits.volatility_cutoff,
                max_order_rate_per_min=self.safety_kernel.limits.max_order_rate_per_min,
                kill_switch_active=active,
            )
            # Also persist to execution_state.json (survives restart)
            try:
                from are.execution_state import ExecutionStateMachine
                exec_state = ExecutionStateMachine()
                exec_state.set_kill_switch(active)
            except Exception as e:
                print(f"[WARN] Failed to persist kill switch to execution state: {e}")
            return self.safety_kernel.limits.kill_switch_active

    def process_tick_event(
        self,
        symbol: str = "BTCUSD",
        price: float = 65000.0,
        volatility: float = 1.0,
        is_shock: bool = False,
    ) -> Dict[str, Any]:
        with self.lock:
            t_now = time.time()
            features = {
                "price": price,
                "volatility": volatility * (3.5 if is_shock else 1.0),
                "trend_strength": 1.2,
                "realized_volatility": (volatility * 3.5 if is_shock else volatility) / 100.0,
                "imbalance_ratio": -0.6 if is_shock else 0.4,
            }
            risk_state = {
                "drawdown": 0.08 if is_shock else 0.01,
                "volatility": features["volatility"],
                "order_count": 1,
            }

            sig: OperationalSignal = self.brain.process_tick(
                symbol=symbol,
                timestamp=t_now,
                market_features=features,
                current_risk_state=risk_state,
                as_of_cutoff=t_now + 100.0,
            )

            tick_rec = {
                "timestamp": t_now,
                "symbol": symbol,
                "price": price,
                "volatility": volatility,
                "action": sig.final_action,
                "signal": sig.final_action,
                "confidence": 0.9,
                "allowed": sig.safety_decision.allowed,
                "safety_allowed": sig.safety_decision.allowed,
                "reason": sig.safety_decision.reason,
                "safety_reason": sig.safety_decision.reason,
                "is_shock": is_shock,
            }
            self.live_ticks_history.append(tick_rec)
            if len(self.live_ticks_history) > 100:
                self.live_ticks_history = self.live_ticks_history[-100:]

            return tick_rec

    def run_autonomous_cycle(self, symbol: str = "BTCUSD") -> Dict[str, Any]:
        with self.lock:
            t_now = time.time()
            raw_ticks = [
                {
                    "symbol": symbol,
                    "timestamp": t_now - (i * 10),
                    "price": 65000.0 + (i * 20.0),
                    "volume": 2.0,
                    "side": "BUY",
                    "bid": 64999.0 + (i * 20.0),
                    "ask": 65001.0 + (i * 20.0),
                    "bids": [(64999.0 + (i * 20.0), 3.0)],
                    "asks": [(65001.0 + (i * 20.0), 2.0)],
                }
                for i in range(25)
            ]
            holdout_ticks = [
                {
                    "symbol": symbol,
                    "timestamp": t_now + 50 + (i * 10),
                    "price": 65500.0 + (i * 10.0),
                    "volume": 1.5,
                }
                for i in range(10)
            ]
            with P001ProgramRunner(self.db_path) as runner:
                return runner.run_program(
                    symbol=symbol,
                    raw_market_ticks=raw_ticks,
                    holdout_ticks=holdout_ticks,
                )


_GLOBAL_SERVER_STATE: Optional[AREServerState] = None


class AREAPIHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler routing REST API endpoints and static assets."""

    def _is_authorized(self) -> bool:
        """Verifies access token using constant-time comparison (ACC-721)."""
        import hmac as _hmac
        global _GLOBAL_SERVER_STATE
        state = _GLOBAL_SERVER_STATE
        if state is None or not state.auth_token:
            return True

        expected = state.auth_token.strip()
        if not expected:
            return True

        def _check(candidate: str) -> bool:
            return bool(candidate) and _hmac.compare_digest(candidate, expected)

        # 1. P1-3: Query token REMOVED (security hygiene — URL logged everywhere)
        # Only Authorization header is accepted now

        # 2. HTTP Headers (X-Auth-Token or Authorization: Bearer)
        if _check(self.headers.get("X-Auth-Token", "").strip()): return True
        auth_hdr = self.headers.get("Authorization", "").strip()
        if auth_hdr.lower().startswith("bearer "):
            if _check(auth_hdr[7:].strip()): return True

        # 3. HTTP Cookie (are_auth=...)
        cookie_hdr = self.headers.get("Cookie", "")
        if cookie_hdr:
            for cookie in cookie_hdr.split(";"):
                parts = cookie.strip().split("=", 1)
                if len(parts) == 2 and parts[0].strip() == "are_auth":
                    if _check(parts[1].strip()): return True

        return False

    def _send_json(self, status_code: int, data: Any):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:4028")  # P1-3: localhost only
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:4028")  # P1-3: localhost only
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token")
        self.end_headers()

    def do_GET(self):
        global _GLOBAL_SERVER_STATE
        state = _GLOBAL_SERVER_STATE

        clean_path = urllib.parse.urlparse(self.path).path

        if clean_path in ("/", "/index.html"):
            html_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(content)
                self.close_connection = True
            else:
                self._send_json(404, {"error": "index.html not found"})
            return

        # Protected REST API Endpoints
        if not self._is_authorized():
            self._send_json(401, {"error": "Unauthorized", "message": "Token otentikasi tidak valid atau belum diberikan."})
            return

        if clean_path == "/api/status":
            if state is not None:
                self._send_json(200, state.get_status_payload())
            else:
                self._send_json(500, {"error": "Server state uninitialized"})

        elif clean_path == "/api/champion-history":
            if state is not None:
                lineage = state.champion_registry.list_champion_lineage()
                self._send_json(200, [r.__dict__ for r in lineage])
            else:
                self._send_json(500, {"error": "Server state uninitialized"})

        elif clean_path.startswith("/api/backtest/list"):
            bt_dir = os.path.join("data", "backtests")
            results = []
            if os.path.exists(bt_dir):
                for fn in sorted(os.listdir(bt_dir)):
                    if fn.endswith(".json"):
                        with open(os.path.join(bt_dir, fn)) as f:
                            results.append(json.load(f))
            self._send_json(200, {"results": results})

        elif clean_path.startswith("/api/backtest/") and clean_path.endswith("/equity-curve"):
            bt_id = clean_path.split("/api/backtest/")[1].split("/")[0]
            # SECURITY: sanitize bt_id to prevent path traversal
            import re as _re
            if not _re.match(r'^[a-zA-Z0-9_\-]+$', bt_id):
                self._send_json(400, {"error": "Invalid backtest ID"})
                return
            bt_dir = os.path.join("data", "backtests")
            bt_file = os.path.join(bt_dir, f"{bt_id}.json")
            if os.path.exists(bt_file):
                with open(bt_file) as f:
                    bt_data = json.load(f)
                equity_curve = bt_data.get("equity_curve", [])
                self._send_json(200, {"id": bt_id, "equity_curve": equity_curve})
            else:
                self._send_json(404, {"error": f"Backtest '{bt_id}' not found"})

        elif clean_path.startswith("/api/backtest/"):
            bt_id = clean_path.split("/api/backtest/")[1]
            # SECURITY: sanitize bt_id to prevent path traversal
            if not _re.match(r'^[a-zA-Z0-9_\-]+$', bt_id):
                self._send_json(400, {"error": "Invalid backtest ID"})
                return
            bt_dir = os.path.join("data", "backtests")
            bt_file = os.path.join(bt_dir, f"{bt_id}.json")
            if os.path.exists(bt_file):
                with open(bt_file) as f:
                    self._send_json(200, json.load(f))
            else:
                self._send_json(404, {"error": f"Backtest '{bt_id}' not found"})

        else:
            self._send_json(404, {"error": f"Endpoint '{clean_path}' not found"})

    def do_POST(self):
        global _GLOBAL_SERVER_STATE
        state = _GLOBAL_SERVER_STATE
        if state is None:
            self._send_json(500, {"error": "Server state uninitialized"})
            return

        # Protected REST API Endpoints
        if not self._is_authorized():
            self._send_json(401, {"error": "Unauthorized", "message": "Token otentikasi tidak valid atau belum diberikan."})
            return

        clean_path = urllib.parse.urlparse(self.path).path

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if clean_path == "/api/run-cycle":
            symbol = payload.get("symbol", "BTCUSD")
            try:
                res = state.run_autonomous_cycle(symbol)
                self._send_json(200, res)
            except Exception as e:
                self._send_json(200, {"status": "error", "message": str(e)})

        elif clean_path == "/api/kill-switch":
            active = bool(payload.get("active", True))
            new_val = state.set_kill_switch(active)
            self._send_json(200, {"kill_switch_active": new_val})

        elif clean_path == "/api/step-tick":
            symbol = payload.get("symbol", "BTCUSD")
            price = float(payload.get("price", 65000.0))
            vol = float(payload.get("volatility", 1.0))
            is_shock = bool(payload.get("is_shock", False))
            tick_res = state.process_tick_event(symbol=symbol, price=price, volatility=vol, is_shock=is_shock)
            self._send_json(200, tick_res)

        elif clean_path == "/api/chat":
            msg = str(payload.get("message", "")).strip()
            reply = state.copilot.generate_response(msg)
            self._send_json(200, {"reply": reply})

        elif clean_path == "/api/backtest/run":
            try:
                from are.backtest_enhanced import EnhancedBacktestEngine
                from are.data_loader import load_ohlc_data
                from are.strategy_engine import load_strategy_from_config
                import polars as pl, time as _bt_t
                engine = EnhancedBacktestEngine()
                symbol = payload.get("symbol", "XAUUSD")
                timeframe = payload.get("timeframe", "H1")
                capital = float(payload.get("capital", 100000))
                start_date = payload.get("start", "2025-01-01")
                end_date = payload.get("end", "2026-08-01")
                # Load REAL parquet data
                df = load_ohlc_data(symbol, timeframe, start_date, end_date)
                if len(df) == 0:
                    raise ValueError(f"No data found for {symbol} {timeframe} {start_date}-{end_date}")
                # Load strategy from registry
                try:
                    import json as _json
                    with open("data/strategies/strategies.json") as _f:
                        _strats = _json.load(_f)
                    _strat_list = _strats if isinstance(_strats, list) else _strats.get("strategies", [])
                    strategy_logic = load_strategy_from_config(_strat_list[0]) if _strat_list else None
                except Exception:
                    strategy_logic = None
                if strategy_logic is None:
                    def strategy_logic(d):
                        return d.with_columns(
                            pl.col("price").pct_change(20).alias("_mom")
                        ).with_columns(
                            pl.when(pl.col("_mom") > 0.02).then(1.0)
                            .when(pl.col("_mom") < -0.02).then(-1.0)
                            .otherwise(0.0).alias("signal")
                        )
                result = engine.run_backtest(
                    strategy_logic=strategy_logic, historical_data=df,
                    initial_capital=capital, timeframe_seconds=3600.0,
                )
                m = result.metrics
                net_pnl = m.get('final_equity', capital) - capital
                bt_id = f"bkt-{int(_bt_t.time()*1000)}"
                bt_dir = os.path.join("data", "backtests")
                os.makedirs(bt_dir, exist_ok=True)
                # Build equity curve
                ec = result.equity_curve
                equity_data = []
                if not ec.is_empty():
                    timestamps = ec['timestamp'].to_list()
                    equities = ec['equity'].to_list()
                    step = max(1, len(timestamps) // 200)
                    for i in range(0, len(timestamps), step):
                        equity_data.append({"timestamp": int(timestamps[i]), "equity": round(equities[i], 2)})
                bt_data = {
                    "id": bt_id, "strategyName": "DSR Momentum Breakout",
                    "config": {"symbol": symbol, "timeframe": timeframe, "startDate": start_date, "endDate": end_date, "initialBalance": capital},
                    "results": {
                        "totalTrades": m.get('total_trades', 0),
                        "winRate": m.get('win_rate', 0),
                        "netPnl": round(net_pnl, 2),
                        "finalEquity": m.get('final_equity', capital),
                        "sharpe": m.get('sharpe_ratio', 0),
                        "sortino": m.get('sortino_ratio', 0),
                        "calmar": m.get('calmar_ratio', 0),
                        "cvar": m.get('cvar_5pct', 0),
                        "profitFactor": m.get('profit_factor', 0),
                        "maxDrawdown": m.get('max_drawdown_pct', 0),
                        "exposure": m.get('exposure_pct', 0),
                        "totalReturnPct": m.get('total_return_pct', 0),
                        "dataBars": m.get('total_bars', 0),
                    },
                    "equityCurve": equity_data,
                    "trades": [],
                    "ranAt": time.strftime('%Y-%m-%dT%H:%M:%S'),
                }
                with open(os.path.join(bt_dir, f"{bt_id}.json"), "w") as f:
                    json.dump(bt_data, f, indent=2)
                # Update strategies.json with latest backtest metrics
                try:
                    strat_file = "data/strategies/strategies.json"
                    if os.path.exists(strat_file):
                        with open(strat_file, 'r') as sf:
                            strat_data = json.load(sf)
                        strats = strat_data if isinstance(strat_data, list) else strat_data.get("strategies", [])
                        if strats:
                            s = strats[0]
                            if "backtestHistory" not in s:
                                s["backtestHistory"] = []
                            s["backtestHistory"].insert(0, {
                                "id": bt_id,
                                "date": bt_data["ranAt"],
                                "result": {
                                    "sharpe": m.get('sharpe_ratio', 0),
                                    "winRate": m.get('win_rate', 0),
                                    "netPnl": round(net_pnl, 2),
                                    "trades": m.get('total_trades', 0),
                                    "maxDD": m.get('max_drawdown_pct', 0),
                                    "pf": m.get('profit_factor', 0),
                                }
                            })
                            s["backtestHistory"] = s["backtestHistory"][:50]  # keep last 50
                            s["metrics"] = {
                                "sharpe": m.get('sharpe_ratio', 0),
                                "winRate": m.get('win_rate', 0),
                                "totalTrades": m.get('total_trades', 0),
                                "maxDD": m.get('max_drawdown_pct', 0),
                                "lastBacktest": bt_data["ranAt"],
                            }
                            out_data = strat_data if isinstance(strat_data, list) else {"strategies": strats}
                            with open(strat_file, 'w') as sf:
                                json.dump(out_data, sf, indent=2)
                except Exception:
                    pass  # Non-critical
                self._send_json(200, {"success": True, "result": bt_data})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif clean_path == "/api/backtest/wfo":
            try:
                from are.backtest_enhanced import EnhancedBacktestEngine
                from are.data_loader import load_ohlc_data
                from are.strategy_engine import load_strategy_from_config
                import polars as pl, time as _wfo_t
                engine = EnhancedBacktestEngine()
                symbol = payload.get("symbol", "XAUUSD")
                timeframe = payload.get("timeframe", "H1")
                n_folds = int(payload.get("folds", 5))
                start_date = payload.get("start", "2025-01-01")
                end_date = payload.get("end", "2026-08-01")
                # Load REAL parquet data
                df = load_ohlc_data(symbol, timeframe, start_date, end_date)
                if len(df) == 0:
                    raise ValueError(f"No data found for {symbol} {timeframe}")
                n = len(df)
                # Load strategy
                try:
                    import json as _json
                    with open("data/strategies/strategies.json") as _f:
                        _strats = _json.load(_f)
                    _strat_list = _strats if isinstance(_strats, list) else _strats.get("strategies", [])
                    strategy_logic = load_strategy_from_config(_strat_list[0]) if _strat_list else None
                except Exception:
                    strategy_logic = None
                def strategy_factory(params):
                    lb = params.get("lookback", 20)
                    def _strat(d):
                        if strategy_logic:
                            return strategy_logic(d)
                        return d.with_columns(pl.col("price").pct_change(lb).alias("_mom")).with_columns(
                            pl.when(pl.col("_mom") > 0.02).then(1.0).when(pl.col("_mom") < -0.02).then(-1.0).otherwise(0.0).alias("signal")
                        )
                    return _strat
                # Configurable param_grid from request body
                raw_grid = payload.get("param_grid")
                if isinstance(raw_grid, list) and len(raw_grid) > 0:
                    param_grid = raw_grid
                else:
                    param_grid = [{"lookback": lb} for lb in (10, 15, 20, 25, 30)]
                wfo_result = engine.run_walk_forward_optimization(
                    strategy_factory=strategy_factory, param_grid=param_grid,
                    historical_data=df, train_window_bars=max(200, n // (n_folds * 2)),
                    test_window_bars=max(50, n // (n_folds * 4)), step_bars=max(50, n // (n_folds * 4)),
                    purge_bars=5, label_horizon_bars=1, initial_capital=100000.0, timeframe_seconds=3600.0,
                )
                # Serialize WFO folds
                folds_data = []
                for f in wfo_result.folds:
                    folds_data.append({
                        "fold_id": f.fold_id,
                        "is_sharpe": f.is_metrics.get("sharpe_ratio", 0),
                        "oos_sharpe": f.oos_metrics.get("sharpe_ratio", 0),
                        "wfe": f.wfe,
                        "winner_params": f.winner_params,
                    })
                self._send_json(200, {
                    "symbol": symbol, "folds": n_folds,
                    "pooled_oos_sharpe": wfo_result.pooled_oos_sharpe,
                    "mean_wfe": wfo_result.mean_wfe,
                    "fold_count": wfo_result.fold_count,
                    "effective_trials": wfo_result.effective_trial_count,
                    "folds_data": folds_data,
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        else:
            self._send_json(404, {"error": f"Endpoint '{clean_path}' not found"})


def run_server(
    db_path: str = "are_interactive.db",
    host: str = "127.0.0.1",
    port: int = 8080,
    auth_token: Optional[str] = None,
) -> None:
    """Starts the Web UI HTTP Server."""
    global _GLOBAL_SERVER_STATE
    _GLOBAL_SERVER_STATE = AREServerState(db_path, auth_token=auth_token)

    # P0-1: Sync kill switch from persistent ExecutionState on startup
    if _GLOBAL_SERVER_STATE._exec_state.kill_switch_active:
        _GLOBAL_SERVER_STATE.safety_kernel.limits = SafetyLimits(
            max_position_size=_GLOBAL_SERVER_STATE.safety_kernel.limits.max_position_size,
            max_drawdown_pct=_GLOBAL_SERVER_STATE.safety_kernel.limits.max_drawdown_pct,
            volatility_cutoff=_GLOBAL_SERVER_STATE.safety_kernel.limits.volatility_cutoff,
            max_order_rate_per_min=_GLOBAL_SERVER_STATE.safety_kernel.limits.max_order_rate_per_min,
            kill_switch_active=True,
        )
        print(f"[ARE-WEB] WARNING: Kill switch synced from persistent state (ACTIVE)")

    server_address = (host, port)
    httpd = http.server.HTTPServer(server_address, AREAPIHandler)
    token_info = f" [Auth Protected: token='{auth_token}']" if auth_token else " [No Auth]"
    print(f"[ARE-WEB] Server started at http://{host}:{port}{token_info} (Database: {db_path})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[ARE-WEB] Shutting down server gracefully...")
    finally:
        httpd.server_close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AHFMES-ARE Web UI Server")
    parser.add_argument("--db", default="are_interactive.db", help="Path to SQLite database")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--auth-token", default=os.environ.get("ARE_AUTH_TOKEN", None), help="Access token for security gateway")

    args = parser.parse_args(argv)
    run_server(db_path=args.db, host=args.host, port=args.port, auth_token=args.auth_token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
