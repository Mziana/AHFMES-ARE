"""
Hypothesis Strategies for Property-Based Testing in AHFMES-ARE (ACC-801, DELEGASI_025)
"""

import math
from hypothesis import strategies as st


def corrupt_price_strategy():
    """
    Generates corrupt / pathological price values:
    - NaN, +Inf, -Inf
    - None
    - Negative floats
    - Extreme numbers (> 1e12)
    - Zero or non-numeric representations
    """
    return st.one_of(
        st.just(float("nan")),
        st.just(float("inf")),
        st.just(float("-inf")),
        st.none(),
        st.floats(max_value=-0.0001, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1e13, max_value=1e25, allow_nan=False, allow_infinity=False),
        st.just(0.0),
        st.text(min_size=1, max_size=10),
    )


def ambiguous_market_state_strategy():
    """
    Generates corrupt / ambiguous market state dictionaries:
    - Missing crucial keys ('price', 'symbol', 'size')
    - Flagged explicitly as ambiguous or corrupt
    - Injected with non-numeric or non-finite fields
    - Empty or non-dict payloads
    """
    base_dict = st.fixed_dictionaries(
        {},
        optional={
            "symbol": st.sampled_from(["BTCUSD", "XAUUSD", "EURUSD", "INVALID_PAIR"]),
            "price": st.one_of(st.floats(min_value=1.0, max_value=100000.0), corrupt_price_strategy()),
            "size": st.one_of(st.floats(min_value=-10.0, max_value=10.0), st.none()),
            "volatility": st.floats(min_value=-5.0, max_value=10.0),
            "is_ambiguous": st.booleans(),
            "is_corrupt": st.booleans(),
        },
    )
    return st.one_of(
        base_dict,
        st.dictionaries(st.text(min_size=1, max_size=5), st.text(min_size=1, max_size=5)),
        st.just({}),
    )


def extreme_slippage_latency_strategy():
    """
    Generates extreme execution conditions:
    - Slippage > 500 pips
    - Latency > 5000 ms
    """
    return st.fixed_dictionaries({
        "symbol": st.just("BTCUSD"),
        "price": st.floats(min_value=100.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
        "size": st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
        "slippage_pips": st.floats(min_value=500.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
        "latency_ms": st.floats(min_value=5000.1, max_value=500000.0, allow_nan=False, allow_infinity=False),
    })
