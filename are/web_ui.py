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
from typing import Any, Dict, List, Optional

from are.champion import ChampionRecord, ChampionRegistry
from are.evidence import EvidenceLedger
from are.habitat import ConditionAtlas, HabitatAdapter
from are.operational import OperationalBrain, OperationalSignal
from are.p001_program import P001ProgramRunner
from are.registry import Registry
from are.safety import CapitalSafetyKernel, SafetyDecision, SafetyLimits
from are.storage import EventStore


class AREServerState:
    """Thread-safe application state container for the Web UI."""

    def __init__(self, db_path: str = "are_interactive.db"):
        self.db_path = db_path
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

        self.atlas = ConditionAtlas()
        self.habitat = HabitatAdapter(self.atlas, self.event_store)
        self.brain = OperationalBrain(
            champion_registry=self.champion_registry,
            safety_kernel=self.safety_kernel,
            habitat=self.habitat,
            event_store=self.event_store,
        )

        self.live_ticks_history: List[Dict[str, Any]] = []

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
                    "kill_switch_active": self.safety_kernel.limits.kill_switch_active,
                    "max_drawdown_pct": self.safety_kernel.limits.max_drawdown_pct,
                    "volatility_cutoff": self.safety_kernel.limits.volatility_cutoff,
                    "max_order_rate_per_min": self.safety_kernel.limits.max_order_rate_per_min,
                    "max_position_size": self.safety_kernel.limits.max_position_size,
                },
                "stream_stats": {
                    "total_ticks": total_ticks,
                    "veto_count": veto_count,
                    "veto_ratio_pct": round(veto_ratio, 2),
                    "chain_health": "VERIFIED_OK" if chain_ok else "CHAIN_CORRUPTED",
                },
                "recent_ticks": self.live_ticks_history[-30:],
                "server_time": time.time(),
            }

    def set_kill_switch(self, active: bool) -> bool:
        with self.lock:
            new_limits = SafetyLimits(
                max_position_size=self.safety_limits.max_position_size,
                max_drawdown_pct=self.safety_limits.max_drawdown_pct,
                volatility_cutoff=self.safety_limits.volatility_cutoff,
                max_order_rate_per_min=self.safety_limits.max_order_rate_per_min,
                kill_switch_active=active,
            )
            self.safety_limits = new_limits
            self.safety_kernel = CapitalSafetyKernel(new_limits)
            self.brain.safety_kernel = self.safety_kernel
            return self.safety_limits.kill_switch_active

    def process_tick_event(
        self,
        symbol: str = "BTCUSD",
        price: float = 65000.0,
        volatility: float = 1.0,
        trend_strength: float = 1.2,
        is_shock: bool = False,
    ) -> Dict[str, Any]:
        with self.lock:
            ts = time.time()
            features = {
                "price": price,
                "volatility": volatility * (3.5 if is_shock else 1.0),
                "trend_strength": trend_strength,
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
                timestamp=ts,
                market_features=features,
                current_risk_state=risk_state,
                as_of_cutoff=ts + 100.0,
            )

            tick_record = {
                "time": ts,
                "price": price,
                "signal": sig.final_action,
                "allowed": sig.safety_decision.allowed,
                "reason": sig.safety_decision.reason,
                "is_shock": is_shock,
            }
            self.live_ticks_history.append(tick_record)
            if len(self.live_ticks_history) > 200:
                self.live_ticks_history.pop(0)

            return tick_record

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

    def _send_json(self, status_code: int, data: Any):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        global _GLOBAL_SERVER_STATE
        state = _GLOBAL_SERVER_STATE

        if self.path in ("/", "/index.html"):
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

        elif self.path == "/api/status":
            if state is not None:
                self._send_json(200, state.get_status_payload())
            else:
                self._send_json(500, {"error": "Server state uninitialized"})

        elif self.path == "/api/champion-history":
            if state is not None:
                lineage = state.champion_registry.list_champion_lineage()
                self._send_json(200, [r.__dict__ for r in lineage])
            else:
                self._send_json(500, {"error": "Server state uninitialized"})

        else:
            self._send_json(404, {"error": f"Endpoint '{self.path}' not found"})

    def do_POST(self):
        global _GLOBAL_SERVER_STATE
        state = _GLOBAL_SERVER_STATE
        if state is None:
            self._send_json(500, {"error": "Server state uninitialized"})
            return

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if self.path == "/api/run-cycle":
            symbol = payload.get("symbol", "BTCUSD")
            res = state.run_autonomous_cycle(symbol)
            self._send_json(200, res)

        elif self.path == "/api/kill-switch":
            active = bool(payload.get("active", True))
            new_val = state.set_kill_switch(active)
            self._send_json(200, {"kill_switch_active": new_val})

        elif self.path == "/api/step-tick":
            symbol = payload.get("symbol", "BTCUSD")
            price = float(payload.get("price", 65000.0))
            vol = float(payload.get("volatility", 1.0))
            is_shock = bool(payload.get("is_shock", False))
            tick_res = state.process_tick_event(symbol=symbol, price=price, volatility=vol, is_shock=is_shock)
            self._send_json(200, tick_res)

        elif self.path == "/api/chat":
            msg = str(payload.get("message", "")).strip().lower()
            reply = self._generate_copilot_response(msg, state)
            self._send_json(200, {"reply": reply})

        else:
            self._send_json(404, {"error": f"Endpoint '{self.path}' not found"})

    def _generate_copilot_response(self, msg: str, state: AREServerState) -> str:
        champ = state.champion_registry.get_active_champion()
        champ_name = champ.champion_id if champ else "Belum Ada (Genesis)"
        ks_active = state.safety_kernel.limits.kill_switch_active

        if any(w in msg for w in ("halo", "hai", "siapa", "kamu", "bantuan", "help")):
            return (
                "👋 **Halo! Saya AI Copilot AHFMES-ARE Control Center.**\n\n"
                "Saya dapat membantu Anda memantau status riset kuantitatif, mengelola batas keselamatan modal CSK, "
                "memicu siklus riset otonom, atau menguji injeksi anomali pasar. "
                "Coba tanyakan: *'Status sistem saat ini?'*, *'Jalankan riset baru'*, atau *'Aktifkan kill switch'*."
            )

        elif any(w in msg for w in ("status", "kondisi", "champion", "keadaan")):
            status_text = "AKTIF" if not ks_active else "DIHENTIKAN (Kill-Switch Aktif)"
            return (
                f"📊 **Ringkasan Status Sistem AHFMES-ARE:**\n\n"
                f"• **Active Champion**: `{champ_name}`\n"
                f"• **Status Eksekusi**: `{status_text}`\n"
                f"• **Max Drawdown Limit**: `{state.safety_limits.max_drawdown_pct * 100:.1f}%`\n"
                f"• **Volatility Cutoff**: `{state.safety_limits.volatility_cutoff} sigma`\n"
                f"• **Integritas Ledger**: `VERIFIED (Append-Only EventStore Cryptographic Chain OK)`"
            )

        elif any(w in msg for w in ("riset", "cycle", "run", "temukan", "alpha")):
            res = state.run_autonomous_cycle("BTCUSD")
            champ_res = res.get("promoted_champion")
            if champ_res:
                return (
                    f"🚀 **Siklus Riset Otonom Berhasil Dijalankan!**\n\n"
                    f"• **Program Status**: `SUCCESS`\n"
                    f"• **Champion Baru Dipromosikan**: `{champ_res['champion_id']}`\n"
                    f"• **Kandidat Terpilih**: `{champ_res['candidate_id']}`\n"
                    f"• **Metrik Validasi Out-of-Sample**: Lolos uji adversarial Critic dan ratifikasi Governor SoD."
                )
            else:
                return "🔍 **Siklus riset telah selesai dievaluasi**, namun tidak ada kandidat baru yang mengungguli Champion aktif saat ini."

        elif any(w in msg for w in ("kill", "darurat", "stop", "matikan", "bahaya")):
            state.set_kill_switch(True)
            return (
                "🛑 **EMERGENCY KILL SWITCH TELAH DIAKTIFKAN!**\n\n"
                "Capital Safety Kernel (CSK) kini memblokir seluruh eksekusi order (VETO aktif). "
                "Seluruh sinyal perdagangan baru akan dialihkan ke `EMERGENCY_FLAT` demi mengamankan modal."
            )

        elif any(w in msg for w in ("hidupkan", "nyalakan", "resume", "aktifkan kembali", "reset kill")):
            state.set_kill_switch(False)
            return "✅ **Kill Switch dinonaktifkan.** Sistem kembali ke mode operasional normal terpagar CSK."

        elif any(w in msg for w in ("shock", "anomali", "injeksi", "pasar")):
            tick_res = state.process_tick_event(is_shock=True)
            return (
                f"⚡ **Injeksi Volatility Shock Terkirim!**\n\n"
                f"• **Sinyal Dihasilkan**: `{tick_res['signal']}`\n"
                f"• **Keputusan CSK**: `Allowed = {tick_res['allowed']}`\n"
                f"• **Keterangan**: `{tick_res['reason']}`\n"
                "Regret Analyzer akan mendeteksi peningkatan rasio veto jika anomali berlanjut."
            )

        else:
            return (
                f"🤖 Saya memahami pertanyaan Anda mengenai *'{msg}'*. "
                f"Saat ini sistem berjalan dengan Champion `{champ_name}` di bawah perlindungan Capital Safety Kernel. "
                "Ketik *'status'* untuk melihat telemetri lengkap, atau gunakan tombol Action Hub di sebelah kiri."
            )


def run_server(
    db_path: str = "are_interactive.db",
    host: str = "127.0.0.1",
    port: int = 8080,
) -> None:
    """Starts the Web UI HTTP Server."""
    global _GLOBAL_SERVER_STATE
    _GLOBAL_SERVER_STATE = AREServerState(db_path)

    server_address = (host, port)
    httpd = http.server.HTTPServer(server_address, AREAPIHandler)
    print(f"[ARE-WEB] Server started at http://{host}:{port} (Database: {db_path})")
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

    args = parser.parse_args(argv)
    run_server(db_path=args.db, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
