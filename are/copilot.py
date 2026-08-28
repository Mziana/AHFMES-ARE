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
        timeout_sec: float = 10.0,
    ):
        self.server_state = server_state
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "qwen2.5-coder")
        self.timeout_sec = timeout_sec

    def generate_response(self, user_message: str) -> str:
        """
        Generates a context-aware response using Ollama Qwen 2.5 Coder if available,
        falling back cleanly to the deterministic internal engine if offline (ACC-712, ACC-713).
        """
        msg = user_message.strip()
        if not msg:
            return "Silakan ajukan pertanyaan atau instruksi terkait sistem AHFMES-ARE."

        # 1. Gather Real-Time Context
        context = self._get_current_context()

        # 2. Attempt Ollama Qwen 2.5 Coder Generation
        ollama_reply = self._query_ollama(msg, context)
        if ollama_reply is not None:
            return ollama_reply

        # 3. Resilient Deterministic Fallback Engine (ACC-713)
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

        if any(w in lower_msg for w in ("halo", "hai", "siapa", "kamu", "bantuan", "help")):
            return (
                "👋 **Halo! Saya AI Copilot AHFMES-ARE Control Center.**\n\n"
                "Saya dapat membantu Anda memantau status riset kuantitatif, mengelola batas keselamatan modal CSK, "
                "memicu siklus riset otonom, atau menguji injeksi anomali pasar. "
                "Coba tanyakan: *'Status sistem saat ini?'*, *'Jalankan riset baru'*, atau *'Aktifkan kill switch'*."
            )

        elif any(w in lower_msg for w in ("rsi", "scalping", "strategi", "orderbook", "mean reversion")):
            return (
                "📈 **Analisis Strategi Kuantitatif AHFMES-ARE:**\n\n"
                "1. **RSI / Momentum**: Menghitung kecepatan harga & crossover EMA cepat vs lambat.\n"
                "2. **Orderbook Imbalance**: Mengukur ketidakseimbangan volume bid-ask pada top depth.\n"
                "3. **Mean Reversion**: Menghitung Z-score deviasi harga terhadap rolling mean window.\n\n"
                "Seluruh sinyal wajib lolos uji firewall Capital Safety Kernel (CSK) sebelum dieksekusi."
            )

        elif any(w in lower_msg for w in ("status", "kondisi", "champion", "keadaan")):
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

        elif any(w in lower_msg for w in ("kill", "darurat", "stop", "matikan", "bahaya")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(True)
            return (
                "🛑 **EMERGENCY KILL SWITCH TELAH DIAKTIFKAN!**\n\n"
                "Capital Safety Kernel (CSK) kini memblokir seluruh eksekusi order (VETO aktif). "
                "Seluruh sinyal perdagangan baru akan dialihkan ke `EMERGENCY_FLAT` demi mengamankan modal."
            )

        elif any(w in lower_msg for w in ("hidupkan", "nyalakan", "resume", "aktifkan kembali", "reset kill")):
            if self.server_state is not None and hasattr(self.server_state, "set_kill_switch"):
                self.server_state.set_kill_switch(False)
            return "✅ **Kill Switch dinonaktifkan.** Sistem kembali ke mode operasional normal terpagar CSK."

        else:
            return (
                f"🤖 Saya memahami pertanyaan Anda mengenai *'{user_message}'*. "
                f"Saat ini sistem berjalan dengan Champion `{champ_id}` di bawah perlindungan Capital Safety Kernel. "
                "Ketik *'status'* untuk melihat telemetri lengkap, atau gunakan tombol Action Hub di sebelah kiri."
            )

