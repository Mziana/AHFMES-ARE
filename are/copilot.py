"""
AHFMES WEB_UI — Conversational AI Copilot (ACC-711, ACC-712, ACC-713)

Integrates with local Ollama Qwen 2.5 Coder (http://localhost:11434/api/generate)
providing real-time quantitative context injection and a resilient deterministic fallback.
Zero external hard-dependencies (stdlib only: json, os, re, time, urllib.request, typing).
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class ConversationalCopilot:
    """Conversational AI Copilot orchestrating Ollama Qwen 2.5 Coder and fallback reasoning."""

    def __init__(
        self,
        server_state: Any = None,
        ollama_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_sec: float = 1.0,
    ):
        self.server_state = server_state
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "qwen2.5-coder")
        self.timeout_sec = timeout_sec
        self._model_discovered = False

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
                    # Prioritize qwen, coder, deepseek, or llama
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

        # 5. Resilient Deterministic Fallback Engine (ACC-713)
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
        champ = context.get("champion", {})
        safety = context.get("safety", {})
        stats = context.get("stream_stats", {})

        system_prompt = (
            "Anda adalah AI Copilot Resmi untuk AHFMES-ARE Control Center (Autonomous Research Engine).\n"
            "Konteks Sistem Real-Time:\n"
            f"- Active Champion: {champ.get('champion_id', 'NONE')} (Candidate: {champ.get('candidate_id', 'N/A')})\n"
            f"- Status Champion: {champ.get('status', 'INACTIVE')}\n"
            f"- CSK Kill Switch Active: {safety.get('kill_switch_active', False)}\n"
            f"- Max Drawdown Limit: {safety.get('max_drawdown_pct', 0.15) * 100:.1f}%\n"
            f"- Volatility Cutoff: {safety.get('volatility_cutoff', 2.5)} sigma\n"
            f"- Total Ticks: {stats.get('total_ticks', 0)} | Veto Count: {stats.get('veto_count', 0)}\n"
            f"- Chain Integrity: {stats.get('chain_health', 'UNKNOWN')}\n\n"
            "Jawab pertanyaan user dalam Bahasa Indonesia yang ringkas, ramah, dan bernuansa kuantitatif profesional."
        )

        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\nUser: {user_message}\nAI Copilot:",
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

    def _generate_builtin_response(self, user_message: str) -> str:
        lower_msg = user_message.lower()
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
        if any(w in lower_msg for w in ("hidupkan", "nyalakan", "resume", "aktifkan kembali", "reset kill", "unblock")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(False)
            return "✅ **Kill Switch dinonaktifkan.** Sistem kembali ke mode operasional normal terpagar CSK."

        elif any(w in lower_msg for w in ("kill", "darurat", "stop", "matikan", "bahaya", "veto")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(True)
            return (
                "🛑 **EMERGENCY KILL SWITCH TELAH DIAKTIFKAN!**\n\n"
                "Capital Safety Kernel (CSK) kini memblokir seluruh eksekusi order (VETO aktif). "
                "Seluruh sinyal perdagangan baru akan dialihkan ke `EMERGENCY_FLAT` demi mengamankan modal."
            )

        # 2. Expanded Identity & Capabilities
        elif any(w in lower_msg for w in (
            "jelaskan tentang dirimu",
            "siapa kamu",
            "apa kemampuanmu",
            "kamu siapa",
            "siapa anda",
            "perkenalkan dirimu",
            "profil",
            "tentang kamu",
        )):
            return (
                f"🤖 **{salam}! Saya adalah AI Copilot AHFMES-ARE Control Center.**\n\n"
                "**Peran & Kemampuan Utama Saya:**\n"
                "1. **Autonomous Research Engine (ARE)**: Memantau siklus hipotesis kuantitatif, backtesting sandbox, verifikasi walk-forward, dan promosi Champion model.\n"
                "2. **Capital Safety Kernel (CSK)**: Memastikan eksekusi mematuhi batas ketat risiko modal (Max Drawdown 15%, Volatility Cutoff 2.5σ, Rate Limit 10 order/menit).\n"
                "3. **MetaTrader 5 & Multi-Asset Adapter**: Menghubungkan feed harga realtime dan order gateway ke terminal MT5 (`are/mt5_feed.py` & `are/mt5_gateway.py`).\n"
                "4. **Interactive Action Hub**: Menjalankan riset baru, menyimulasikan tick pasar, atau memicu Emergency Kill Switch secara instan."
            )

        # 3. MetaTrader 5 & Multi-Asset Knowledge
        elif any(w in lower_msg for w in (
            "mt5",
            "metatrader",
            "xauusd",
            "gold",
            "emas",
            "forex",
            "eurusd",
            "broker",
            "terminal",
            "pair",
            "live trading",
        )):
            return (
                "📊 **Integrasi MetaTrader 5 (MT5) & Multi-Asset AHFMES-ARE:**\n\n"
                "AHFMES-ARE telah dilengkapi modul bridge siap pakai:\n"
                "• **Market Feed Adapter (`are/mt5_feed.py`)**: Mengalirkan tick realtime dari terminal MT5 untuk instrumen seperti `XAUUSD`, `BTCUSD`, atau pasangan Forex.\n"
                "• **Execution Risk Firewall (`are/mt5_gateway.py`)**: Memfilter seluruh sinyal order Champion melalui batas proteksi Capital Safety Kernel (CSK) sebelum dikirim ke broker.\n\n"
                "💡 **Cara Menghubungkan ke XAUUSD / Forex:**\n"
                "Inisialisasi config feed: `MT5FeedConfig(symbol='XAUUSD')` lalu jalankan runner `MT5LiveDemoRunner`. "
                "Bila terjadi anomali volatilitas ekstrem, sistem akan otomatis melakukan `EMERGENCY_FLAT` demi mengamankan modal."
            )

        # 4. Quantitative Strategy Inquiries
        elif any(w in lower_msg for w in ("rsi", "scalping", "strategi", "orderbook", "mean reversion", "alpha")):
            return (
                "📈 **Analisis Strategi Kuantitatif AHFMES-ARE:**\n\n"
                "1. **RSI / Momentum (`are/features.py`)**: Menghitung kecepatan pergerakan harga & crossover EMA cepat vs lambat.\n"
                "2. **Orderbook Imbalance**: Mengukur rasio ketidakseimbangan volume bid-ask pada top depth 5 level.\n"
                "3. **Mean Reversion**: Menghitung Z-score deviasi harga terhadap rolling window.\n\n"
                "Seluruh sinyal strategi wajib lolos verifikasi OOS (*Out-of-Sample*) pada holdout dataset sebelum dipromosikan sebagai Champion."
            )

        # 5. System Status
        elif any(w in lower_msg for w in ("status", "kondisi", "champion", "keadaan", "telemetri")):
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

        # 6. General Greeting
        elif re.search(r"\b(halo|hai|hello|bantuan|help)\b", lower_msg):
            return (
                f"👋 **{salam}! Saya AI Copilot AHFMES-ARE Control Center.**\n\n"
                "Saya dapat membantu Anda memantau status riset kuantitatif, mengelola batas keselamatan modal CSK, "
                "memicu siklus riset otonom, atau menghubungkan sistem ke terminal MetaTrader 5 (MT5). "
                "Coba tanyakan: *'Status sistem saat ini?'*, *'Jelaskan integrasi MT5 dan XAUUSD'*, atau *'Aktifkan kill switch'*."
            )

        # 7. Fallback Contextual Response
        else:
            return (
                f"🤖 Saya memahami pertanyaan Anda mengenai *'{user_message}'*. "
                f"Saat ini sistem berjalan dengan Champion `{champ_id}` di bawah perlindungan Capital Safety Kernel. "
                "Ketik *'status'* untuk melihat telemetri lengkap, tanyakan tentang *'MT5 dan XAUUSD'*, atau gunakan tombol Action Hub."
            )

