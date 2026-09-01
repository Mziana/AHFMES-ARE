"""Live trading modules for AHFMES-ARE."""
try:
    from .mt5_live import MT5LiveFeed, Tick, Bar
    from .autopilot import AutopilotBrain, compute_rsi, detect_divergence
except ImportError:
    # MetaTrader5 not available (e.g., Linux CI, non-Windows)
    pass

__all__ = ["MT5LiveFeed", "Tick", "Bar", "AutopilotBrain"]
