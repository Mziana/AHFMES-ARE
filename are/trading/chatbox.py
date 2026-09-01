"""
ARE Chatbox -- Talk to ARE's Brain
====================================
Interactive chat that works as a floating window.
Can be opened from any menu in ARELauncher.bat.

Usage:
    python -m are.trading.chatbox              # Interactive chat
    python -m are.trading.chatbox --check      # Check provider status
"""
import sys
import os
import json
import time
from datetime import datetime, timezone

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False


def get_market_context():
    """Get current market state for chat context."""
    if not HAS_MT5 or not mt5.initialize():
        return {}

    context = {"rsi": {}, "position": None, "stats": {}}

    # Get RSI for all timeframes
    symbol = "XAUUSD"
    for tf_name, tf_const in [("D1", 16385), ("H4", 16388), ("H1", 16384),
                               ("M30", 32769), ("M15", 32768), ("M5", 16387), ("M1", 16386)]:
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, 50)
            if rates is not None and len(rates) > 15:
                closes = [float(r["close"]) for r in rates]
                # Quick RSI
                period = 14
                deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                gains = [max(d, 0) for d in deltas]
                losses = [max(-d, 0) for d in deltas]
                ag = sum(gains[:period]) / period
                al = sum(losses[:period]) / period
                for i in range(period, len(deltas)):
                    ag = (ag * (period - 1) + gains[i]) / period
                    al = (al * (period - 1) + losses[i]) / period
                rsi = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
                context["rsi"][tf_name] = round(rsi, 1)
        except Exception:
            pass

    # Position
    pos = mt5.positions_get(symbol=symbol)
    if pos:
        p = pos[0]
        context["position"] = {
            "type": "BUY" if p.type == 0 else "SELL",
            "pnl": p.profit, "volume": p.volume,
        }

    # Account
    acct = mt5.account_info()
    if acct:
        context["stats"]["balance"] = acct.balance
        context["stats"]["equity"] = acct.equity

    mt5.shutdown()
    return context


def print_header():
    print()
    print("=" * 62)
    print("  ARE CHATBOX -- Talk to ARE's Brain")
    print("  Type your message and press Enter")
    print("  Commands: /status, /rsi, /check, /clear, /quit")
    print("=" * 62)
    print()


def print_rsi_table(context):
    """Print RSI table."""
    rsi = context.get("rsi", {})
    if not rsi:
        print("  No RSI data available (MT5 not connected?)")
        return
    print(f"  {'TF':>4s}  {'RSI':>6s}  {'Zone':>8s}  {'Bar'}")
    print(f"  {'-'*40}")
    for tf in ["D1", "H4", "H1", "M30", "M15", "M5", "M1"]:
        r = rsi.get(tf)
        if r is not None:
            bar_len = int(r / 2)
            bar = "=" * bar_len + ">" * 1
            zone = "BULL" if r > 50 else "BEAR" if r < 50 else "NEUTRAL"
            print(f"  {tf:>4s}  {r:>6.1f}  {zone:>8s}  {bar}")
    print()


def main():
    from are.trading.ai_brain import AIBrain, PROVIDERS

    args = sys.argv[1:]

    # Load config
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f).get("ai", {})
    except Exception:
        config = {}

    # Hardcode OpenRouter key
    config.setdefault("provider", "openrouter")
    config["api_key"] = os.environ.get("OPENROUTER_API_KEY", "")

    brain = AIBrain(config)

    # Check providers mode
    if "--check" in args:
        print("Checking providers...")
        results = brain.check_providers()
        for name, info in results.items():
            status = info.get("status", "?")
            icon = "[OK]" if status == "OK" else "[!!]"
            extra = info.get("model", info.get("error", ""))
            print(f"  {icon} {name:>12s}: {status} {extra}")
        return

    # Get initial context
    context = get_market_context()

    print_header()
    if context.get("rsi"):
        print_rsi_table(context)

    # Chat loop
    while True:
        try:
            user_input = input("YOU> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Commands
        if user_input.lower() in ("/quit", "/exit", "/q"):
            print("Goodbye!")
            break
        elif user_input.lower() == "/clear":
            brain._chat_history.clear()
            print("  [Chat history cleared]")
            continue
        elif user_input.lower() == "/rsi":
            context = get_market_context()
            print_rsi_table(context)
            continue
        elif user_input.lower() == "/status":
            stats = brain.get_stats()
            print(f"  Active provider: {stats['active_provider']}")
            print(f"  API calls: {stats['call_count']}")
            print(f"  Chat history: {stats['chat_history_len']} messages")
            print(f"  Fallback chain: {' -> '.join(stats['fallback_chain'])}")
            continue
        elif user_input.lower() == "/check":
            results = brain.check_providers()
            for name, info in results.items():
                status = info.get("status", "?")
                icon = "[OK]" if status == "OK" else "[!!]"
                print(f"  {icon} {name}: {status}")
            continue
        elif user_input.lower().startswith("/"):
            print("  Unknown command. Try: /status, /rsi, /check, /clear, /quit")
            continue

        # Refresh context periodically
        if HAS_MT5:
            context = get_market_context()

        # Get AI response
        print("  [Thinking...]", end="", flush=True)
        response = brain.chat(user_input, context)
        print(f"\rARE> {response}\n")


if __name__ == "__main__":
    main()
