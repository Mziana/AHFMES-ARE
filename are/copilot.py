"""
AHFMES WEB_UI — Conversational AI Copilot (ACC-711, ACC-712, ACC-713, DELEGASI_030)

Integrates with AI Brain fallback chain:
1. Ollama (local, free) — PRIMARY
2. OpenRouter (free models) — BACKUP
3. Built-in deterministic fallback — ALWAYS AVAILABLE

Zero external hard-dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from are.diagnostics import PostTradeDiagnostics, SlippageReport

STATIC_SYSTEM_PREFIX = (
    "Anda adalah AI Copilot Resmi untuk AHFMES-ARE Control Center (Autonomous Research Engine).\n"
    "Arsitektur & Konstitusi Sistem:\n"
    "1. Autonomous Research Engine (World 2: PROVE): Vectorized backtesting, OOS verification, Champion promotion.\n"
    "2. Capital Safety Kernel (CSK): Absolute risk limits (Max DD 15%, Volatility Cutoff 2.5 sigma, Rate Limits).\n"
    "3. Windows Vault Protocol: Immutable dual-layer JSONL witness and self-healing SQLite primary cache.\n"
    "4. Post-Trade Shadow Diagnostics: Factual slippage drift and latency anomaly analysis.\n"
    "Aturan Komunikasi: Jawab dalam Bahasa Indonesia kuantitatif, ramah, profesional, dan berbasis bukti faktual tanpa halusinasi."
)


class ConversationalCopilot:
    """Conversational AI Copilot with fallback chain: Ollama → OpenRouter → Rules."""

    def __init__(
        self,
        server_state: Any = None,
        ollama_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_sec: float = 30.0,
        event_store: Optional[Any] = None,
    ):
        self.server_state = server_state
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
        self.timeout_sec = timeout_sec
        self.event_store = event_store
        self._model_discovered = False
        self.diagnostics = PostTradeDiagnostics()
        self._openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

    def _discover_ollama_model(self) -> Optional[str]:
        if self._model_discovered:
            return self.model_name
        self._model_discovered = True
        tags_url = re.sub(r"/api/generate/?$", "/api/tags", self.ollama_url)
        try:
            req = urllib.request.Request(tags_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=0.3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)]
                    for candidate in ("qwen", "coder", "deepseek", "llama"):
                        for m in models:
                            if candidate in m.lower():
                                self.model_name = m
                                return self.model_name
                    if models:
                        self.model_name = models[0]
                        return self.model_name
        except Exception:
            pass
        return self.model_name

    def _build_evidence_context(self, event_store: Optional[Any] = None) -> str:
        store = event_store or self.event_store
        anomalies = self.diagnostics.query_recent_anomalies(event_store=store, limit=3)
        if anomalies:
            anomaly_lines = [
                f"{a.strategy_id} {a.symbol} slippage: {a.slippage_pips:.2f} pips, latency: {a.execution_latency_ms:.1f}ms ({a.anomaly_reason})"
                for a in anomalies
            ]
            anomaly_str = "; ".join(anomaly_lines)
        else:
            anomaly_str = "None (No anomalies recorded)"
        reports = self.diagnostics.fetch_all(event_store=store, limit=3)
        if reports:
            report_lines = [
                f"{r.strategy_id} {r.symbol} slippage: {r.slippage_pips:.2f} pips, latency: {r.execution_latency_ms:.1f}ms"
                for r in reports
            ]
            report_str = "; ".join(report_lines)
        else:
            report_str = "None (No executions recorded)"
        context = self._get_current_context()
        champ = context.get("champion", {})
        champ_id = champ.get("champion_id", "NONE")
        champ_status = champ.get("status", "INACTIVE")
        vault_status = "UNKNOWN"
        if store is not None and hasattr(store, "verify_full_chain_integrity"):
            try:
                ok, status_str = store.verify_full_chain_integrity()
                vault_status = f"VERIFIED_{status_str}" if ok else f"FAILED_{status_str}"
            except Exception:
                vault_status = "INTEGRITY_CHECK_ERROR"
        else:
            stats = context.get("stream_stats", {})
            vault_status = stats.get("chain_health", "VERIFIED_OK")
        evidence_text = (
            "[EVIDENCE CONTEXT]\n"
            f"- Recent Anomalies: {anomaly_str}\n"
            f"- Recent Slippage: {report_str}\n"
            f"- Active Champion: {champ_id} | Status: {champ_status}\n"
            f"- Vault Integrity: {vault_status}\n"
            "[END]\n\n"
            "[INSTRUCTION]\n"
            "You are an evidence-bound trading assistant. Use ONLY data from EVIDENCE CONTEXT above.\n"
            'If data not available, say: "Data tidak tersedia di EvidenceLedger."\n'
            "[END]"
        )
        if len(evidence_text) > 2000:
            evidence_text = evidence_text[:2000]
        return evidence_text

    def build_prompt(self, user_message: str, dynamic_context: Optional[Dict[str, Any]] = None, event_store: Optional[Any] = None) -> str:
        ctx = dynamic_context if dynamic_context is not None else self._get_current_context()
        champ = ctx.get("champion", {})
        safety = ctx.get("safety", {})
        stats = ctx.get("stream_stats", {})
        store = event_store or self.event_store
        evidence_context = self._build_evidence_context(store)
        evidence_hash = hashlib.sha256(evidence_context.encode("utf-8")).hexdigest()
        dynamic_part = (
            "\nKonteks Real-Time:\n"
            f"- Active Champion: {champ.get('champion_id', 'NONE')}\n"
            f"- Status: {champ.get('status', 'INACTIVE')}\n"
            f"- Kill Switch: {safety.get('kill_switch_active', False)}\n"
            f"- Max DD: {safety.get('max_drawdown_pct', 0.15) * 100:.1f}%\n"
            f"- Ticks: {stats.get('total_ticks', 0)} | Vetoes: {stats.get('veto_count', 0)}\n"
        )
        return f"{STATIC_SYSTEM_PREFIX}\n\n{evidence_context}\n{dynamic_part}\nUser: {user_message}\nAI:"

    def generate_response(self, user_message: str) -> str:
        msg = user_message.strip()
        if not msg:
            return "Silakan ajukan pertanyaan atau instruksi terkait sistem AHFMES-ARE."
        lower_msg = msg.lower()
        if any(w in lower_msg for w in ("hidupkan", "nyalakan", "resume", "aktifkan kembali", "reset kill", "unblock")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(False)
        elif any(w in lower_msg for w in ("kill", "darurat", "stop", "matikan", "bahaya", "veto")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(True)
        self._discover_ollama_model()
        context = self._get_current_context()
        # 1. Try Ollama (local, free)
        ollama_reply = self._query_ollama(msg, context)
        if ollama_reply is not None:
            return f"[ollama] {ollama_reply}"
        # 2. Try OpenRouter (free models)
        openrouter_reply = self._query_openrouter(msg, context)
        if openrouter_reply is not None:
            return f"[openrouter] {openrouter_reply}"
        # 3. Fallback to deterministic rules
        return self._generate_builtin_response(msg)

    def _query_openrouter(self, user_message: str, context: Dict[str, Any]) -> Optional[str]:
        if not self._openrouter_key:
            return None
        prompt_text = self.build_prompt(user_message, context)
        free_models = [
            "google/gemini-2.0-flash-exp:free",
            "deepseek/deepseek-r1:free",
            "deepseek/deepseek-chat:free",
            "qwen/qwen-2.5-coder-32b-instruct:free",
        ]
        for model in free_models:
            try:
                payload = json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.3,
                    "max_tokens": 1024,
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._openrouter_key}",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if content:
                            return content.strip()
            except Exception:
                continue
        return None

    def _query_ollama(self, user_message: str, context: Dict[str, Any]) -> Optional[str]:
        prompt_text = self.build_prompt(user_message, context)
        payload = {"model": self.model_name, "prompt": prompt_text, "stream": False}
        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.ollama_url, data=req_data,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                if response.status == 200:
                    resp_json = json.loads(response.read().decode("utf-8"))
                    res_text = resp_json.get("response", "").strip()
                    if res_text:
                        ev_ctx = self._build_evidence_context(self.event_store)
                        ok, final_text = self._verify_factual_consistency(res_text, ev_ctx)
                        return final_text
        except Exception:
            return None
        return None

    def _verify_factual_consistency(self, ollama_response: str, evidence_context: str) -> tuple[bool, str]:
        metric_pattern = re.compile(
            r'\b(slippage|latency|latensi|drawdown|sharpe|spread|profit|pnl|veto|ticks)\b[^\d]*?([\d.]+)',
            re.IGNORECASE,
        )

        def _norm_kw(k: str) -> str:
            return "latency" if k.lower() == "latensi" else k.lower()

        ev_metrics: Dict[str, List[float]] = {}
        for m in metric_pattern.finditer(evidence_context):
            kw = _norm_kw(m.group(1))
            try:
                val = float(m.group(2))
                ev_metrics.setdefault(kw, []).append(val)
            except ValueError:
                continue
        for m in metric_pattern.finditer(ollama_response):
            kw = _norm_kw(m.group(1))
            try:
                resp_val = float(m.group(2))
            except ValueError:
                continue
            if kw in ev_metrics:
                allowed_vals = ev_metrics[kw]
                matched = any(abs(resp_val - ev_v) <= max(0.001 * abs(ev_v), 1e-4) for ev_v in allowed_vals)
                if not matched:
                    return False, "[DATA TIDAK TERSEDIA]"
        return True, ollama_response

    def _normalize_query(self, text: str) -> str:
        t = text.lower().strip()
        t = re.sub(r"[\s\-_]+", " ", t)
        t = re.sub(r"\bmt\s*5\b|\bmetatrader\s*5\b|\bmetatrader\b", "mt5", t)
        t = re.sub(r"\bxau\s*usd\b|\bgold\b|\bemas\b", "xauusd", t)
        t = re.sub(r"\bbtc\s*usd\b|\bbitcoin\b", "btcusd", t)
        t = re.sub(r"\beur\s*usd\b", "eurusd", t)
        return t

    def _get_current_context(self) -> Dict[str, Any]:
        if self.server_state is not None and hasattr(self.server_state, "get_status_payload"):
            return self.server_state.get_status_payload()
        return {
            "champion": {"champion_id": "P001_CHAMPION_V1", "candidate_id": "CAND_ALPHA_001", "status": "ACTIVE"},
            "safety": {"kill_switch_active": False, "max_drawdown_pct": 0.15, "volatility_cutoff": 2.5},
            "stream_stats": {"total_ticks": 0, "veto_count": 0, "chain_health": "VERIFIED_OK"},
        }

    def _generate_builtin_response(self, user_message: str) -> str:
        raw_msg = user_message.strip()
        norm_msg = self._normalize_query(user_message)
        context = self._get_current_context()
        champ = context.get("champion", {})
        safety = context.get("safety", {})
        stats = context.get("stream_stats", {})
        champ_id = champ.get("champion_id", "Belum Ada (Genesis)")
        ks_active = safety.get("kill_switch_active", False)
        hour = time.localtime().tm_hour
        if 4 <= hour < 11:
            salam = "Selamat pagi"
        elif 11 <= hour < 15:
            salam = "Selamat siang"
        elif 15 <= hour < 18:
            salam = "Selamat sore"
        else:
            salam = "Selamat malam"
        if any(w in norm_msg for w in ("hidupkan", "nyalakan", "resume", "aktifkan kembali", "reset kill", "unblock")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(False)
            return "Kill Switch dinonaktifkan. Sistem kembali ke mode normal."
        elif any(w in norm_msg for w in ("kill", "darurat", "stop", "matikan", "bahaya", "veto")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(True)
            return "EMERGENCY KILL SWITCH DIAKTIFKAN! Semua order diblokir."
        elif any(w in norm_msg for w in ("slippage", "gagal", "anomali", "diagnostik", "drift")):
            anomalies = self.diagnostics.query_recent_anomalies(event_store=self.event_store, limit=5)
            if anomalies:
                details = []
                for a in anomalies:
                    details.append(f"{a.symbol} ({a.strategy_id}): slippage {a.slippage_pips:.1f} pips, latensi {a.execution_latency_ms:.1f}ms")
                return f"Laporan Shadow Diagnostics:\n" + "\n".join(details)
            return "Tidak ditemukan anomali eksekusi."
        elif any(w in norm_msg for w in ("siapa kamu", "kamu siapa", "kemampuanmu", "apa tugasmu")):
            return (
                f"{salam}! Saya AI Copilot AHFMES-ARE.\n"
                "Kemampuan saya:\n"
                "1. Monitoring status ARE (champion, safety, ticks)\n"
                "2. Analisis slippage & anomali broker\n"
                "3. Kill switch control\n"
                "4. Integrasi MT5 & multi-asset\n"
                "5. Backtest & strategi kuantitatif\n\n"
                "Tanya: 'status', 'slippage', 'MT5 XAUUSD', atau 'kill switch'."
            )
        elif any(w in norm_msg for w in ("status", "kondisi", "champion", "keadaan", "telemetri")):
            status_text = "AKTIF" if not ks_active else "DIHENTIKAN (Kill-Switch)"
            return (
                f"Status AHFMES-ARE:\n"
                f"Champion: {champ_id}\n"
                f"Status: {status_text}\n"
                f"Max DD: {safety.get('max_drawdown_pct', 0.15) * 100:.1f}%\n"
                f"Ticks: {stats.get('total_ticks', 0)} | Vetoes: {stats.get('veto_count', 0)}\n"
                f"Ledger: {stats.get('chain_health', 'VERIFIED_OK')}"
            )
        elif re.search(r"\b(halo|hai|hello|bantuan|help|apa kabar|selamat)\b", norm_msg):
            return (
                f"{salam}! Saya AI Copilot AHFMES-ARE.\n"
                "Coba tanya: 'status', 'slippage', 'MT5 XAUUSD', atau 'kill switch'."
            )
        else:
            return (
                f"Mengenai '{raw_msg}':\n"
                f"Champion: {champ_id} | Status: {'AKTIF' if not ks_active else 'STOP'}\n"
                "Gunakan /status, /slippage, atau /kill untuk info lebih lanjut."
            )
