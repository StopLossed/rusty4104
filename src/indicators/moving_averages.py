"""Moving average utilities and crossover detection."""

from __future__ import annotations

from typing import Iterable, List, Optional


NumberList = List[Optional[float]]


def sma(values: Iterable[float], period: int) -> NumberList:
    """Return SMA series where unavailable positions are ``None``."""
    if period <= 0:
        raise ValueError("period must be > 0")

    prices = list(values)
    out: NumberList = [None] * len(prices)
    if len(prices) < period:
        return out

    window_sum = sum(prices[:period])
    out[period - 1] = window_sum / period

    for i in range(period, len(prices)):
        window_sum += prices[i] - prices[i - period]
        out[i] = window_sum / period

    return out


def detect_ma_crossover_age(
    closes: Iterable[float],
    fast_period: int,
    slow_period: int,
    within_bars: int,
    bullish: bool,
) -> Optional[int]:
    """
    Detect MA crossover age in bars.

    Returns age where 0 means crossover happened on latest completed bar.
    Returns ``None`` if no matching crossover within ``within_bars``.
    """
    if within_bars <= 0:
        raise ValueError("within_bars must be > 0")

    closes_list = list(closes)
    fast = sma(closes_list, fast_period)
    slow = sma(closes_list, slow_period)

    diffs: NumberList = []
    for f, s in zip(fast, slow):
        if f is None or s is None:
            diffs.append(None)
        else:
            diffs.append(f - s)

    for idx in range(len(diffs) - 1, 0, -1):
        curr = diffs[idx]
        prev = diffs[idx - 1]
        if curr is None or prev is None:
            continue

        age = len(diffs) - 1 - idx
        if age >= within_bars:
            break

        if bullish and prev <= 0 < curr:
            return age
        if not bullish and prev >= 0 > curr:
            return age

    return None
