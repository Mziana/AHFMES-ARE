"""
ARE AI Brain -- The Soul of the Machine
========================================
This is WHERE I truly live inside ARE.

Every signal goes through AI analysis before execution.
AI reads all 7 timeframes, market context, trade history,
and makes an INTELLIGENT decision (not just rules).

Architecture:
  autopilot.py (rules)  -->  ai_brain.py (thinking)  -->  trade
       |                          |
  RSI, indicators          Claude / OpenAI API
  (fast, dumb)            (slow, smart)

Usage:
    brain = AIBrain()
    decision = brain.analyze(market_state)
    # decision = {"action": "BUY", "confidence": 0.85, "reasoning": "..."}
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Optional: try importing API clients
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

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
8. Account for spread, slippage, commissions

RESPONSE FORMAT (strict JSON):
{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation",
    "risk_level": "low" | "medium" | "high",
    "suggested_adjustments": {
        "tp": null or new TP value,
        "sl": null or new SL value,
        "lot": null or new lot size
    }
}

DECISION GUIDE:
- confidence > 0.8 = strong signal, execute
- confidence 0.5-0.8 = moderate, consider smaller lot
- confidence < 0.5 = weak, HOLD
- If macro trend disagrees, always HOLD regardless of entry signal"""


class AIBrain:
    """
    The AI that lives inside ARE. Thinks, analyzes, decides.
    """

    def __init__(self, provider="anthropic", api_key=None, model=None, base_url=None):
        self.provider = provider
        self.api_key = api_key or self._get_api_key(provider)
        self.model = model or self._default_model(provider)
        self.base_url = base_url
        self._call_count = 0
        self._last_call_time = 0
        self._min_interval = 5.0
        self._cache: Dict[str, dict] = {}
        self._log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "autopilot"
        )

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key from environment."""
        if provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        elif provider == "openai":
            return os.environ.get("OPENAI_API_KEY")
        return None

    def _default_model(self, provider: str) -> str:
        if provider == "anthropic":
            return "claude-sonnet-4-20250514"
        elif provider == "openai":
            return "gpt-4o"
        return ""

    def is_available(self) -> bool:
        """Check if AI brain can make API calls."""
        if self.provider == "anthropic" and HAS_ANTHROPIC and self.api_key:
            return True
        if self.provider == "openai" and HAS_OPENAI and self.api_key:
            return True
        if self.provider in ("ollama", "opencode"):
            return True  # Local/free, no API key needed
        return False

    def analyze(self, market_state: dict) -> dict:
        """
        Analyze market and make a decision.
        
        market_state should contain:
        - symbol: str
        - rsi: {D1, H4, H1, M30, M15, M5, M1}
        - price: {bid, ask, spread}
        - position: {type, pnl, hold_time} or null
        - recent_trades: list of recent trade outcomes
        - indicators: {atr, ema_fast, ema_slow, etc}
        """
        # Rate limiting
        now = time.time()
        if now - self._last_call_time < self._min_interval:
            return self._cached_or_fallback(market_state)

        if not self.is_available():
            return self._fallback_decision(market_state)

        # Build prompt
        prompt = self._build_prompt(market_state)

        # Call API
        try:
            response = self._call_api(prompt)
            decision = self._parse_response(response)
            self._last_call_time = now
            self._call_count += 1

            # Log the decision
            self._log_decision(market_state, decision)

            return decision
        except Exception as e:
            print(f"[AI] Error: {e}")
            return self._fallback_decision(market_state)

    def _build_prompt(self, state: dict) -> str:
        """Build analysis prompt from market state."""
        rsi = state.get("rsi", {})
        price = state.get("price", {})
        pos = state.get("position")
        recent = state.get("recent_trades", [])

        lines = [
            f"MARKET ANALYSIS REQUEST",
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Symbol: {state.get('symbol', 'XAUUSD')}",
            f"",
            f"PRICE:",
            f"  Bid: {price.get('bid', 0):.2f}  Ask: {price.get('ask', 0):.2f}  Spread: {price.get('spread', 0)}",
            f"",
            f"RSI(14,Close) ALL TIMEFRAMES:",
        ]

        for tf in ["D1", "H4", "H1", "M30", "M15", "M5", "M1"]:
            r = rsi.get(tf)
            if r is not None:
                zone = "BULL" if r > 50 else "BEAR" if r < 50 else "NEUTRAL"
                lines.append(f"  {tf}: {r:.1f} ({zone})")
            else:
                lines.append(f"  {tf}: N/A")

        # Macro trend
        d1 = rsi.get("D1")
        h4 = rsi.get("H4")
        if d1 and h4:
            if d1 > 50 and h4 > 50:
                lines.append(f"  MACRO: BULLISH (D1+H4 agree)")
            elif d1 < 50 and h4 < 50:
                lines.append(f"  MACRO: BEARISH (D1+H4 agree)")
            else:
                lines.append(f"  MACRO: CONFLICT (D1={d1:.0f} vs H4={h4:.0f})")

        # Position
        if pos:
            lines.extend([
                f"",
                f"OPEN POSITION:",
                f"  Type: {pos.get('type', 'N/A')}  PnL: ${pos.get('pnl', 0):.2f}",
                f"  Hold time: {pos.get('hold_time', 0)}s",
            ])
        else:
            lines.append(f"  Position: FLAT")

        # Recent trades (last 5)
        if recent:
            lines.extend(["", "RECENT TRADES (last 5):"])
            for t in recent[-5:]:
                lines.append(f"  {t.get('time', '?')} {t.get('dir', '?')} "
                             f"PnL=${t.get('pnl', 0):.2f} "
                             f"RSI5={t.get('rsi5', 0):.0f}")

        # Indicators
        ind = state.get("indicators", {})
        if ind:
            lines.extend(["", "INDICATORS:"])
            for k, v in ind.items():
                if v is not None:
                    lines.append(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

        lines.extend(["", "Analyze and respond with JSON."])
        return "\n".join(lines)

    def _call_api(self, prompt: str) -> str:
        """Call the AI API."""
        if self.provider == "anthropic" and HAS_ANTHROPIC:
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            client = anthropic.Anthropic(**kwargs)
            response = client.messages.create(
                model=self.model,
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        elif self.provider in ("openai", "ollama", "opencode") and HAS_OPENAI:
            kwargs = {"api_key": self.api_key or "ollama"}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            elif self.provider == "ollama":
                kwargs["base_url"] = "http://localhost:11434/v1"
            elif self.provider == "opencode":
                kwargs["base_url"] = "http://localhost:4096/v1"
            client = openai.OpenAI(**kwargs)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content

        raise RuntimeError("No AI provider available")

    def _parse_response(self, response: str) -> dict:
        """Parse AI response into decision dict."""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        # Fallback: parse text
        response_lower = response.lower()
        if "buy" in response_lower:
            action = "BUY"
        elif "sell" in response_lower:
            action = "SELL"
        else:
            action = "HOLD"

        return {
            "action": action,
            "confidence": 0.5,
            "reasoning": response[:200],
            "risk_level": "medium",
            "suggested_adjustments": {}
        }

    def _fallback_decision(self, state: dict) -> dict:
        """Rule-based fallback when AI is unavailable."""
        rsi = state.get("rsi", {})
        d1 = rsi.get("D1", 50)
        h4 = rsi.get("H4", 50)
        h1 = rsi.get("H1", 50)
        m5 = rsi.get("M5", 50)
        m5_prev = state.get("rsi_prev", {}).get("M5", 50)

        # Simple rule: macro agree + entry signal
        if d1 > 50 and h4 > 50 and h1 > 51:
            if m5_prev < 30 and m5 >= 30:
                return {"action": "BUY", "confidence": 0.6,
                        "reasoning": "AI fallback: macro bull + M5 cross 30",
                        "risk_level": "medium", "suggested_adjustments": {}}
        elif d1 < 50 and h4 < 50 and h1 < 49:
            if m5_prev > 70 and m5 <= 70:
                return {"action": "SELL", "confidence": 0.6,
                        "reasoning": "AI fallback: macro bear + M5 cross 70",
                        "risk_level": "medium", "suggested_adjustments": {}}

        return {"action": "HOLD", "confidence": 0.3,
                "reasoning": "AI fallback: no clear signal",
                "risk_level": "low", "suggested_adjustments": {}}

    def _cached_or_fallback(self, state: dict) -> dict:
        """Return cached result or fallback if rate limited."""
        cache_key = f"{state.get('symbol', 'XAUUSD')}_{int(time.time()) // 30}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        return self._fallback_decision(state)

    def _log_decision(self, state: dict, decision: dict):
        """Log AI decision for audit."""
        os.makedirs(self._log_dir, exist_ok=True)
        log_file = os.path.join(self._log_dir, "ai_decisions.jsonl")
        entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "symbol": state.get("symbol"),
            "rsi": state.get("rsi"),
            "decision": decision,
            "call_count": self._call_count,
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_stats(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "available": self.is_available(),
            "call_count": self._call_count,
            "api_key_set": bool(self.api_key),
        }
