"""
AHFMES MT5_BRIDGE — MetaTrader 5 Market Feed Adapter (ACC-601, ACC-602)

Provides unified tick and bar ingestion with dynamic MetaTrader 5 binding
and a realistic deterministic standalone mock fallback.
Zero external hard-dependencies (stdlib only: json, time, math, typing, dataclasses).
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MT5FeedConfig:
    login: Optional[int] = None
    server: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None
    symbol: str = "BTCUSD"
    timeframe: str = "M1"
    use_mock: bool = True


class MT5MockFeed:
    """Realistic deterministic standalone market feed generator."""

    def __init__(self, base_price: float = 65000.0):
        self.base_price = base_price
        self._tick_seq = 0
        self._connected = False

    def initialize(self) -> bool:
        self._connected = True
        return True

    def get_latest_ticks(self, symbol: str = "BTCUSD", count: int = 10) -> List[Dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("MT5 Mock Feed not initialized")

        now = time.time()
        ticks: List[Dict[str, Any]] = []

        for i in range(count):
            self._tick_seq += 1
            # Deterministic wave oscillation
            delta = math.sin(self._tick_seq * 0.2) * 50.0 + (self._tick_seq * 0.5)
            price = self.base_price + delta
            spread = 1.0 + (abs(math.sin(self._tick_seq * 0.1)) * 1.5)
            bid = price - (spread / 2.0)
            ask = price + (spread / 2.0)
            vol = 1.0 + abs(math.cos(self._tick_seq * 0.3) * 2.0)

            ticks.append({
                "time": now - ((count - i) * 0.5),
                "bid": round(bid, 2),
                "ask": round(ask, 2),
                "last": round(price, 2),
                "volume": round(vol, 4),
                "bids": [(round(bid, 2), round(vol, 2)), (round(bid - 0.5, 2), 5.0)],
                "asks": [(round(ask, 2), round(vol, 2)), (round(ask + 0.5, 2), 5.0)],
            })

        return ticks

    def get_latest_bars(self, symbol: str = "BTCUSD", count: int = 20) -> List[Dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("MT5 Mock Feed not initialized")

        now = time.time()
        bars: List[Dict[str, Any]] = []

        for i in range(count):
            idx = self._tick_seq + i
            open_p = self.base_price + (math.sin(idx * 0.1) * 60.0)
            high_p = open_p + 15.0 + abs(math.sin(idx * 0.2) * 10.0)
            low_p = open_p - 15.0 - abs(math.cos(idx * 0.2) * 10.0)
            close_p = open_p + (math.cos(idx * 0.1) * 20.0)
            vol = 50.0 + abs(math.sin(idx) * 100.0)

            bars.append({
                "time": now - ((count - i) * 60.0),
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": round(vol, 2),
            })

        return bars

    def shutdown(self) -> None:
        self._connected = False


class MT5MarketFeed:
    """Unified Market Feed with graceful dynamic MT5 import or Mock fallback."""

    def __init__(self, config: Optional[MT5FeedConfig] = None):
        self.config = config or MT5FeedConfig()
        self._mt5_lib: Optional[Any] = None
        self._mock_feed: Optional[MT5MockFeed] = None
        self._is_live = False

        if not self.config.use_mock:
            try:
                import MetaTrader5 as mt5  # dynamic runtime check
                self._mt5_lib = mt5
            except ImportError:
                self._mt5_lib = None

        if self._mt5_lib is None:
            self._mock_feed = MT5MockFeed()

    def initialize(self) -> bool:
        if self._mock_feed is not None:
            return self._mock_feed.initialize()

        if self._mt5_lib is not None:
            init_kwargs: Dict[str, Any] = {}
            if self.config.path:
                init_kwargs["path"] = self.config.path
            if self.config.login:
                init_kwargs["login"] = self.config.login
            if self.config.password:
                init_kwargs["password"] = self.config.password
            if self.config.server:
                init_kwargs["server"] = self.config.server

            ok = self._mt5_lib.initialize(**init_kwargs)
            if not ok:
                # Fallback to mock on connection fail
                self._mock_feed = MT5MockFeed()
                return self._mock_feed.initialize()
            self._is_live = True
            return True

        return False

    def get_latest_ticks(self, symbol: Optional[str] = None, count: int = 10) -> List[Dict[str, Any]]:
        sym = symbol or self.config.symbol
        if self._mock_feed is not None:
            return self._mock_feed.get_latest_ticks(sym, count)

        if self._mt5_lib is not None and self._is_live:
            raw_ticks = self._mt5_lib.copy_ticks_from(sym, self._mt5_lib.COPY_TICKS_ALL, int(time.time()), count)
            if raw_ticks is None or len(raw_ticks) == 0:
                return []
            ticks = []
            for t in raw_ticks:
                ticks.append({
                    "time": float(t["time"]),
                    "bid": float(t["bid"]),
                    "ask": float(t["ask"]),
                    "last": float(t.get("last", (t["bid"] + t["ask"]) / 2.0)),
                    "volume": float(t.get("volume", 1.0)),
                    "bids": [(float(t["bid"]), float(t.get("volume", 1.0)))],
                    "asks": [(float(t["ask"]), float(t.get("volume", 1.0)))],
                })
            return ticks

        return []

    def get_latest_bars(self, symbol: Optional[str] = None, count: int = 20) -> List[Dict[str, Any]]:
        sym = symbol or self.config.symbol
        if self._mock_feed is not None:
            return self._mock_feed.get_latest_bars(sym, count)

        if self._mt5_lib is not None and self._is_live:
            tf = getattr(self._mt5_lib, f"TIMEFRAME_{self.config.timeframe}", self._mt5_lib.TIMEFRAME_M1)
            raw_rates = self._mt5_lib.copy_rates_from_pos(sym, tf, 0, count)
            if raw_rates is None or len(raw_rates) == 0:
                return []
            bars = []
            for r in raw_rates:
                bars.append({
                    "time": float(r["time"]),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "volume": float(r.get("tick_volume", 1.0)),
                })
            return bars

        return []

    def shutdown(self) -> None:
        if self._mock_feed is not None:
            self._mock_feed.shutdown()
        if self._mt5_lib is not None and self._is_live:
            self._mt5_lib.shutdown()
            self._is_live = False
