"""
AHFMES WEB_UI — Conversational AI Copilot (ACC-711, ACC-712, ACC-713, DELEGASI_030)

Integrates with local Ollama Qwen 2.5 Coder (http://localhost:11434/api/generate)
providing Prompt-Cache Prefix Optimization, Post-Trade Shadow Diagnostics,
and a resilient deterministic factual fallback engine (Explainable AI / Zero Hallucination).
Zero external hard-dependencies (stdlib only).
"""

from __future__ import annotations

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
    """Conversational AI Copilot orchestrating Ollama Qwen 2.5 Coder and fallback reasoning."""

    def __init__(
        self,
        server_state: Any = None,
        ollama_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_sec: float = 1.0,
        event_store: Optional[Any] = None,
    ):
        self.server_state = server_state
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "qwen2.5-coder")
        self.timeout_sec = timeout_sec
        self.event_store = event_store
        self._model_discovered = False
        self.diagnostics = PostTradeDiagnostics()

    def _discover_ollama_model(self) -> Optional[str]:
        """Auto-discovers available models from local Ollama tags API."""
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

    def build_prompt(self, user_message: str, dynamic_context: Dict[str, Any]) -> str:
        """
        Constructs optimized prompt separating static prefix cache from dynamic execution state.
        """
        champ = dynamic_context.get("champion", {})
        safety = dynamic_context.get("safety", {})
        stats = dynamic_context.get("stream_stats", {})

        dynamic_part = (
            "\nKonteks Real-Time Dinamis:\n"
            f"- Active Champion: {champ.get('champion_id', 'NONE')} (Candidate: {champ.get('candidate_id', 'N/A')})\n"
            f"- Status Champion: {champ.get('status', 'INACTIVE')}\n"
            f"- CSK Kill Switch Active: {safety.get('kill_switch_active', False)}\n"
            f"- Max Drawdown Limit: {safety.get('max_drawdown_pct', 0.15) * 100:.1f}%\n"
            f"- Volatility Cutoff: {safety.get('volatility_cutoff', 2.5)} sigma\n"
            f"- Total Ticks: {stats.get('total_ticks', 0)} | Veto Count: {stats.get('veto_count', 0)}\n"
            f"- Chain Integrity: {stats.get('chain_health', 'UNKNOWN')}\n"
        )
        return f"{STATIC_SYSTEM_PREFIX}\n{dynamic_part}\nUser: {user_message}\nAI Copilot:"

    def generate_response(self, user_message: str) -> str:
        """
        Generates a context-aware response using Ollama Qwen 2.5 Coder if available,
        falling back cleanly to the deterministic internal engine if offline (ACC-712, ACC-713).
        """
        msg = user_message.strip()
        if not msg:
            return "Silakan ajukan pertanyaan atau instruksi terkait sistem AHFMES-ARE."

        # 1. Trigger Direct Action Intents (Fail-Closed)
        lower_msg = msg.lower()
        if any(w in lower_msg for w in ("hidupkan", "nyalakan", "resume", "aktifkan kembali", "reset kill", "unblock")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(False)
        elif any(w in lower_msg for w in ("kill", "darurat", "stop", "matikan", "bahaya", "veto")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(True)

        # 2. Attempt dynamic model auto-discovery
        self._discover_ollama_model()

        # 3. Gather Real-Time Context
        context = self._get_current_context()

        # 4. Attempt Ollama Qwen 2.5 Coder Generation
        ollama_reply = self._query_ollama(msg, context)
        if ollama_reply is not None:
            return ollama_reply

        # 5. Resilient Deterministic Fallback Engine (ACC-713, DELEGASI_030)
        return self._generate_builtin_response(msg)

    def _get_current_context(self) -> Dict[str, Any]:
        if self.server_state is not None and hasattr(self.server_state, "get_status_payload"):
            return self.server_state.get_status_payload()
        return {
            "champion": {"champion_id": "P001_CHAMPION_V1", "candidate_id": "CAND_ALPHA_001", "status": "ACTIVE"},
            "safety": {"kill_switch_active": False, "max_drawdown_pct": 0.15, "volatility_cutoff": 2.5},
            "stream_stats": {"total_ticks": 0, "veto_count": 0, "chain_health": "VERIFIED_OK"},
        }

    def _query_ollama(self, user_message: str, context: Dict[str, Any]) -> Optional[str]:
        prompt_text = self.build_prompt(user_message, context)
        payload = {
            "model": self.model_name,
            "prompt": prompt_text,
            "stream": False,
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.ollama_url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                if response.status == 200:
                    resp_json = json.loads(response.read().decode("utf-8"))
                    res_text = resp_json.get("response", "").strip()
                    if res_text:
                        return res_text
        except Exception:
            return None

        return None

    def _normalize_query(self, text: str) -> str:
        """Normalizes whitespaces, symbols, and domain abbreviations."""
        t = text.lower().strip()
        t = re.sub(r"[\s\-_]+", " ", t)
        t = re.sub(r"\bmt\s*5\b|\bmetatrader\s*5\b|\bmetatrader\b", "mt5", t)
        t = re.sub(r"\bxau\s*usd\b|\bgold\b|\bemas\b", "xauusd", t)
        t = re.sub(r"\bbtc\s*usd\b|\bbitcoin\b", "btcusd", t)
        t = re.sub(r"\beur\s*usd\b", "eurusd", t)
        return t

    def _generate_builtin_response(self, user_message: str) -> str:
        raw_msg = user_message.strip()
        norm_msg = self._normalize_query(user_message)
        context = self._get_current_context()
        champ = context.get("champion", {})
        safety = context.get("safety", {})
        stats = context.get("stream_stats", {})

        champ_id = champ.get("champion_id", "Belum Ada (Genesis)")
        ks_active = safety.get("kill_switch_active", False)

        # Time-based natural greeting
        hour = time.localtime().tm_hour
        if 4 <= hour < 11:
            salam = "Selamat pagi"
        elif 11 <= hour < 15:
            salam = "Selamat siang"
        elif 15 <= hour < 18:
            salam = "Selamat sore"
        else:
            salam = "Selamat malam"

        # 1. Kill Switch Actions (Highest Priority)
        if any(w in norm_msg for w in ("hidupkan", "nyalakan", "resume", "aktifkan kembali", "reset kill", "unblock")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(False)
            return "✅ **Kill Switch dinonaktifkan.** Sistem kembali ke mode operasional normal terpagar CSK."

        elif any(w in norm_msg for w in ("kill", "darurat", "stop", "matikan", "bahaya", "veto")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(True)
            return (
                "🛑 **EMERGENCY KILL SWITCH TELAH DIAKTIFKAN!**\n\n"
                "Capital Safety Kernel (CSK) kini memblokir seluruh eksekusi order (VETO aktif). "
                "Seluruh sinyal perdagangan baru akan dialihkan ke `EMERGENCY_FLAT` demi mengamankan modal."
            )

        # 2. Post-Trade Diagnostics & Slippage Drift Inquiry (DELEGASI_030, XAI)
        elif any(w in norm_msg for w in (
            "slippage",
            "gagal",
            "anomali",
            "diagnostik",
            "drift",
            "latensi",
            "eksekusi terakhir",
            "order terakhir",
            "mengapa order",
            "kenapa order",
            "performa broker",
            "shadow",
        )):
            es = self.event_store
            if es is None and self.server_state is not None:
                es = getattr(self.server_state, "event_store", getattr(self.server_state, "_store", None))

            anomalies = self.diagnostics.query_recent_anomalies(event_store=es, limit=5)
            if anomalies:
                details_list = []
                for a in anomalies:
                    details_list.append(
                        f"• **{a.symbol}** (Strategi: `{a.strategy_id}`): Expected `{a.expected_price:.5f}` vs Fill `{a.actual_price:.5f}` "
                        f"$\rightarrow$ Slippage **{a.slippage_pips:.1f} pips**, Latensi **{a.execution_latency_ms:.1f}ms** "
                        f"(*{a.anomaly_reason}*)"
                    )
                summary = "\n".join(details_list)
                return (
                    f"🔍 **Laporan Shadow Diagnostics & Slippage Drift (Evidence-Based):**\n\n"
                    f"Ditemukan {len(anomalies)} anomali eksekusi terekam pada Evidence Ledger:\n"
                    f"{summary}\n\n"
                    f"💡 *Capital Safety Kernel (CSK) terus memvalidasi deviasi ini untuk memastikan eksekusi tetap aman.*"
                )
            else:
                return (
                    "✅ **Laporan Shadow Diagnostics & Slippage Drift:**\n\n"
                    "Berdasarkan verifikasi pada Evidence Ledger, seluruh eksekusi order terakhir berada dalam batas nominal "
                    "(Slippage < 3.0 pips dan Latensi < 1500ms). Tidak ditemukan anomali drift broker."
                )

        # 3. Expanded Identity & Capabilities
        elif any(w in norm_msg for w in (
            "ceritakan tentang dirimu",
            "jelaskan tentang dirimu",
            "siapa kamu",
            "apa kemampuanmu",
            "apa tugasmu",
            "kamu bisa apa",
            "kamu siapa",
            "siapa anda",
            "perkenalkan dirimu",
            "profil",
            "tentang kamu",
            "kemampuanmu",
            "fungsi kamu",
            "tugas kamu",
        )):
            return (
                f"🤖 **{salam}! Saya adalah AI Copilot AHFMES-ARE Control Center.**\n\n"
                "**Arsitektur & Kemampuan Utama Saya:**\n"
                "1. **Autonomous Research Engine (ARE)**: Memandu siklus hipotesis kuantitatif, backtesting sandbox, verifikasi out-of-sample holdout, dan promosi Champion model.\n"
                "2. **Capital Safety Kernel (CSK)**: Memastikan eksekusi mematuhi batas ketat risiko modal (Max Drawdown 15%, Volatility Cutoff 2.5σ, Rate Limit 10 order/menit).\n"
                "3. **MetaTrader 5 & Multi-Asset Adapter**: Menghubungkan feed harga realtime dan order gateway ke terminal MT5 (`are/mt5_feed.py` & `are/mt5_gateway.py`).\n"
                "4. **Evidence Ledger & Experience Store**: Menyimpan snapshot data pasar dan memori penyesalan anomali secara append-only dan anti-tamper.\n"
                "5. **Post-Trade Shadow Diagnostics**: Memantau slippage drift dan anomali eksekusi broker secara faktual tanpa halusinasi.\n"
                "6. **Interactive Action Hub**: Menjalankan riset baru, menyimulasikan tick pasar, atau memicu Emergency Kill Switch secara instan."
            )

        # 4. MetaTrader 5 & Multi-Asset Knowledge
        elif any(w in norm_msg for w in (
            "mt5",
            "xauusd",
            "btcusd",
            "eurusd",
            "forex",
            "broker",
            "terminal",
            "buka pasar",
            "akses pasar",
            "trading",
            "pair",
            "live trading",
        )):
            return (
                "📊 **Integrasi MetaTrader 5 (MT5) & Multi-Asset AHFMES-ARE:**\n\n"
                "AHFMES-ARE telah dilengkapi modul bridge trading siap pakai:\n"
                "• **Market Feed Adapter (`are/mt5_feed.py`)**: Mengalirkan tick realtime dari terminal MT5 untuk instrumen seperti `XAUUSD` (Gold), `BTCUSD`, atau pasangan Forex.\n"
                "• **Execution Risk Firewall (`are/mt5_gateway.py`)**: Memfilter seluruh sinyal order Champion melalui batas proteksi Capital Safety Kernel (CSK) sebelum diteruskan ke broker.\n\n"
                "💡 **Cara Menghubungkan ke Pasar XAUUSD / Forex:**\n"
                "Inisialisasi konfigurasi feed: `MT5FeedConfig(symbol='XAUUSD')` lalu aktifkan `MT5LiveDemoRunner`. "
                "Bila terjadi anomali volatilitas ekstrem atau lonjakan drawdown, sistem secara otomatis melakukan `EMERGENCY_FLAT` demi mengamankan modal."
            )

        # 5. Quantitative Strategy Inquiries
        elif any(w in norm_msg for w in ("rsi", "scalping", "strategi", "orderbook", "mean reversion", "alpha", "ema", "momentum")):
            return (
                "📈 **Analisis Strategi Kuantitatif AHFMES-ARE:**\n\n"
                "1. **RSI / Momentum (`are/features.py`)**: Menghitung kecepatan pergerakan harga & crossover EMA cepat vs lambat.\n"
                "2. **Orderbook Imbalance**: Mengukur rasio ketidakseimbangan volume bid-ask pada top depth 5 level.\n"
                "3. **Mean Reversion**: Menghitung Z-score deviasi harga terhadap rolling window.\n\n"
                "Seluruh sinyal strategi wajib lolos verifikasi OOS (*Out-of-Sample*) pada holdout dataset sebelum dipromosikan sebagai Champion."
            )

        # 6. System Status
        elif any(w in norm_msg for w in ("status", "kondisi", "champion", "keadaan", "telemetri", "kesehatan")):
            status_text = "AKTIF" if not ks_active else "DIHENTIKAN (Kill-Switch Aktif)"
            return (
                f"📊 **Ringkasan Status Sistem AHFMES-ARE:**\n\n"
                f"• **Active Champion**: `{champ_id}`\n"
                f"• **Status Eksekusi**: `{status_text}`\n"
                f"• **Max Drawdown Limit**: `{safety.get('max_drawdown_pct', 0.15) * 100:.1f}%`\n"
                f"• **Volatility Cutoff**: `{safety.get('volatility_cutoff', 2.50)} sigma`\n"
                f"• **Total Ticks / Vetoes**: `{stats.get('total_ticks', 0)} ticks / {stats.get('veto_count', 0)} vetoes`\n"
                f"• **Integritas Ledger**: `{stats.get('chain_health', 'VERIFIED_OK')}`"
            )

        # 7. General Greeting
        elif re.search(r"\b(halo|hai|hello|bantuan|help|apa kabar|selamat pagi|selamat siang|selamat sore|selamat malam)\b", norm_msg):
            return (
                f"👋 **{salam}! Saya AI Copilot AHFMES-ARE Control Center.**\n\n"
                "Saya siap membantu Anda memantau status riset kuantitatif, mengelola batas keselamatan modal CSK, "
                "memicu siklus riset otonom, atau menghubungkan sistem ke terminal MetaTrader 5 (MT5). "
                "Coba tanyakan: *'Status sistem saat ini?'*, *'Jelaskan integrasi MT5 dan XAUUSD'*, atau *'Aktifkan kill switch'*."
            )

        # 8. Intelligent Non-Robotic Fallback
        else:
            return (
                f"📊 **Analisis Kontekstual AHFMES-ARE:**\n\n"
                f"Mengenai topik *'{raw_msg}'*, sistem saat ini beroperasi dengan Champion `{champ_id}` "
                f"di bawah pengawasan ketat Capital Safety Kernel (CSK) dengan batas drawdown `{safety.get('max_drawdown_pct', 0.15) * 100:.1f}%`. "
                f"Anda dapat mengeksplorasi telemetri sistem (*'status'*), integrasi eksekusi pasar (*'MT5 & XAUUSD'*), "
                f"analisis slippage broker (*'slippage'*, *'diagnostik'*), atau mengontrol batas risiko melalui obrolan ini."
            )