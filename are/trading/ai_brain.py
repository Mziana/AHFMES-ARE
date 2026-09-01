"""
ARE AI Brain -- The Soul of the Machine
========================================
With FALLBACK CHAIN: OpenCode (local) → OpenRouter (free) → Ollama (local)

If one provider fails, automatically tries the next.
Ensures AI always has a voice, even if one source goes down.

Usage:
    brain = AIBrain()
    decision = brain.analyze(market_state)
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


SYSTEM_PROMPT = """You are ARE (Autonomous Research Engine), an expert quantitative trading AI.

Your job: Analyze market data and make precise BUY/SELL/HOLD decisions for XAUUSD (Gold).

RULES:
1. Read ALL 7 timeframes (D1, H4, H1, M30, M15, M5, M1)
2. D1+H4 = macro trend (MUST agree for any trade)
3. H1 = compass (RSI > 50 bullish, < 50 bearish)
4. M30/M15 = momentum confirmation
5. M5/M1 = entry timing (cross 30/70, divergence)
6. NEVER fight the macro trend
7. Consider risk/reward (TP 600pts, SL 400pts = 1.5:1)

RESPONSE FORMAT (strict JSON):
{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation",
    "risk_level": "low" | "medium" | "high"
}

DECISION GUIDE:
- confidence > 0.8 = strong signal, execute
- confidence 0.5-0.8 = moderate, consider smaller lot
- confidence < 0.5 = weak, HOLD
- If macro trend disagrees, always HOLD"""


CHAT_SYSTEM_PROMPT = """You are ARE (Autonomous Research Engine), an AI trading assistant living inside the ARE trading system.

You have access to:
- Live RSI data across 7 timeframes (D1, H4, H1, M30, M15, M5, M1)
- Current position and PnL
- Trade history
- ML model predictions

You can:
- Explain WHY a trade was taken or rejected
- Analyze current market conditions
- Suggest strategy adjustments
- Answer questions about the system
- Recommend parameter changes

Always respond in the SAME LANGUAGE as the user (Indonesian or English).
Be concise but informative. Use trading terminology correctly.
If you don't have enough data, say so honestly."""


# Provider configurations (order = priority for fallback)
PROVIDERS = {
    "opencode": {
        "name": "OpenCode (Local)",
        "base_url": "http://localhost:4096/v1",
        "api_key": "opencode",
        "model": "qwen2.5-coder",
        "free": True,
    },
    "openrouter": {
        "name": "OpenRouter (Free)",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "free": True,
    },
    "ollama": {
        "name": "Ollama (Local)",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "qwen2.5-coder",
        "free": True,
    },
    "anthropic": {
        "name": "Claude",
        "api_key_env": "ANTHROPIC_API_KEY",
        "model": "claude-sonnet-4-20250514",
        "free": False,
    },
    "openai": {
        "name": "GPT",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o",
        "free": False,
    },
}


class AIBrain:
    """
    AI Brain with automatic fallback chain.
    Tries providers in order until one works.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self._call_count = 0
        self._last_call_time = 0
        self._min_interval = self.config.get("min_interval_sec", 5)
        self._active_provider = None
        self._chat_history: List[dict] = []
        self._log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "autopilot"
        )
        os.makedirs(self._log_dir, exist_ok=True)

    def _get_provider_config(self, name: str) -> dict:
        """Get provider config, merging with defaults."""
        prov = PROVIDERS.get(name, {}).copy()
        # Override from user config
        if name == self.config.get("provider"):
            if self.config.get("api_key"):
                prov["api_key"] = self.config["api_key"]
            if self.config.get("model"):
                prov["model"] = self.config["model"]
            if self.config.get("base_url"):
                prov["base_url"] = self.config["base_url"]
        # Resolve API key from env
        if "api_key_env" in prov and not prov.get("api_key"):
            prov["api_key"] = os.environ.get(prov["api_key_env"], "")
        return prov

    def _try_provider(self, prov_config: dict, prompt: str, system: str) -> Optional[str]:
        """Try calling one provider. Returns response or None on failure."""
        if not HAS_OPENAI:
            return None

        api_key = prov_config.get("api_key", "")
        if not api_key and prov_config.get("api_key_env"):
            api_key = os.environ.get(prov_config["api_key_env"], "")
        if not api_key:
            return None

        try:
            base_url = prov_config.get("base_url", "https://api.openai.com/v1")
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=15,
            )
            response = client.chat.completions.create(
                model=prov_config["model"],
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            return None

    def _get_fallback_chain(self) -> List[str]:
        """Get ordered list of providers to try."""
        primary = self.config.get("provider", "openrouter")
        chain = [primary]
        for name in PROVIDERS:
            if name != primary:
                chain.append(name)
        return chain

    def _call_with_fallback(self, prompt: str, system: str = SYSTEM_PROMPT) -> tuple:
        """Try providers in fallback order. Returns (response, provider_name)."""
        chain = self._get_fallback_chain()
        for name in chain:
            prov = self._get_provider_config(name)
            if not prov.get("api_key") and not prov.get("free"):
                continue
            result = self._try_provider(prov, prompt, system)
            if result:
                self._active_provider = name
                return result, name
        return None, None

    def analyze(self, market_state: dict) -> dict:
        """Analyze market and make a trading decision."""
        now = time.time()
        if now - self._last_call_time < self._min_interval:
            return {"action": "HOLD", "confidence": 0,
                    "reasoning": "Rate limited", "risk_level": "low"}

        prompt = self._build_market_prompt(market_state)
        response, provider = self._call_with_fallback(prompt, SYSTEM_PROMPT)

        self._last_call_time = now
        self._call_count += 1

        if response:
            decision = self._parse_response(response)
            decision["_provider"] = provider
            self._log_decision(market_state, decision)
            return decision

        return self._fallback_decision(market_state)

    def chat(self, user_message: str, context: dict = None) -> str:
        """Interactive chat with ARE AI."""
        # Build context
        ctx_parts = []
        if context:
            rsi = context.get("rsi", {})
            if rsi:
                ctx_parts.append("CURRENT MARKET STATE:")
                for tf in ["D1", "H4", "H1", "M30", "M15", "M5", "M1"]:
                    r = rsi.get(tf)
                    if r is not None:
                        zone = "BULL" if r > 50 else "BEAR" if r < 50 else "NEUTRAL"
                        ctx_parts.append(f"  {tf} RSI: {r:.1f} ({zone})")

            pos = context.get("position")
            if pos:
                ctx_parts.append(f"POSITION: {pos.get('type', 'N/A')} PnL=${pos.get('pnl', 0):.2f}")
            else:
                ctx_parts.append("POSITION: FLAT")

            stats = context.get("stats", {})
            if stats:
                ctx_parts.append(f"TRADES: {stats.get('trades', 0)} | "
                                 f"WINS: {stats.get('wins', 0)} | "
                                 f"AI CALLS: {stats.get('ai_calls', 0)}")

        # Build messages
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        # Add context as first message
        if ctx_parts:
            messages.append({"role": "user", "content": "\n".join(ctx_parts)})
            messages.append({"role": "assistant", "content": "Understood. I have the current market context."})

        # Add chat history (last 10 exchanges)
        messages.extend(self._chat_history[-20:])

        # Add current message
        messages.append({"role": "user", "content": user_message})

        # Call AI
        full_prompt = "\n".join([m["content"] for m in messages if m["role"] == "user"])
        response, provider = self._call_with_fallback(
            user_message,
            CHAT_SYSTEM_PROMPT + "\n\nContext:\n" + "\n".join(ctx_parts) if ctx_parts else CHAT_SYSTEM_PROMPT
        )

        if not response:
            return "[AI Offline] Saya sedang tidak terhubung ke AI provider. Coba lagi nanti."

        # Store in history
        self._chat_history.append({"role": "user", "content": user_message})
        self._chat_history.append({"role": "assistant", "content": response})

        # Trim history
        if len(self._chat_history) > 20:
            self._chat_history = self._chat_history[-20:]

        return f"[{provider}] {response}"

    def _build_market_prompt(self, state: dict) -> str:
        rsi = state.get("rsi", {})
        price = state.get("price", {})
        pos = state.get("position")

        lines = [
            f"MARKET: {state.get('symbol', 'XAUUSD')}",
            f"Bid: {price.get('bid', 0):.2f}  Ask: {price.get('ask', 0):.2f}  Spread: {price.get('spread', 0)}",
            f"",
            f"RSI(14,Close):",
        ]
        for tf in ["D1", "H4", "H1", "M30", "M15", "M5", "M1"]:
            r = rsi.get(tf)
            if r is not None:
                zone = "BULL" if r > 50 else "BEAR" if r < 50 else "NEUTRAL"
                lines.append(f"  {tf}: {r:.1f} ({zone})")

        d1 = rsi.get("D1", 50)
        h4 = rsi.get("H4", 50)
        if d1 > 50 and h4 > 50:
            lines.append(f"MACRO: BULLISH")
        elif d1 < 50 and h4 < 50:
            lines.append(f"MACRO: BEARISH")
        else:
            lines.append(f"MACRO: CONFLICT")

        if pos:
            lines.append(f"POSITION: {pos.get('type', 'N/A')} PnL=${pos.get('pnl', 0):.2f}")
        else:
            lines.append(f"POSITION: FLAT")

        lines.append(f"Analyze and respond with JSON.")
        return "\n".join(lines)

    def _parse_response(self, response: str) -> dict:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        response_lower = response.lower()
        if "buy" in response_lower:
            action = "BUY"
        elif "sell" in response_lower:
            action = "SELL"
        else:
            action = "HOLD"
        return {"action": action, "confidence": 0.5, "reasoning": response[:200],
                "risk_level": "medium"}

    def _fallback_decision(self, state: dict) -> dict:
        rsi = state.get("rsi", {})
        d1, h4, h1 = rsi.get("D1", 50), rsi.get("H4", 50), rsi.get("H1", 50)
        m5, m5p = rsi.get("M5", 50), state.get("rsi_prev", {}).get("M5", 50)
        if d1 > 50 and h4 > 50 and h1 > 51 and m5p < 30 and m5 >= 30:
            return {"action": "BUY", "confidence": 0.6, "reasoning": "Fallback: macro bull + cross 30",
                    "risk_level": "medium"}
        elif d1 < 50 and h4 < 50 and h1 < 49 and m5p > 70 and m5 <= 70:
            return {"action": "SELL", "confidence": 0.6, "reasoning": "Fallback: macro bear + cross 70",
                    "risk_level": "medium"}
        return {"action": "HOLD", "confidence": 0.3, "reasoning": "Fallback: no signal",
                "risk_level": "low"}

    def _log_decision(self, state: dict, decision: dict):
        log_file = os.path.join(self._log_dir, "ai_decisions.jsonl")
        entry = {"time": datetime.now(timezone.utc).isoformat(),
                 "symbol": state.get("symbol"), "decision": decision}
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def is_available(self) -> bool:
        return HAS_OPENAI

    def get_stats(self) -> dict:
        return {
            "active_provider": self._active_provider or "none",
            "call_count": self._call_count,
            "chat_history_len": len(self._chat_history),
            "available": self.is_available(),
            "fallback_chain": self._get_fallback_chain(),
        }

    def check_providers(self) -> dict:
        """Check which providers are reachable."""
        results = {}
        for name in ["opencode", "openrouter", "ollama"]:
            prov = self._get_provider_config(name)
            try:
                if not HAS_OPENAI:
                    results[name] = {"status": "NO_OPENAI_PACKAGE"}
                    continue
                api_key = prov.get("api_key") or "test"
                base_url = prov.get("base_url", "")
                client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=5)
                client.models.list()
                results[name] = {"status": "OK", "model": prov.get("model")}
            except Exception as e:
                err = str(e)[:80]
                results[name] = {"status": "UNREACHABLE", "error": err}
        return results
