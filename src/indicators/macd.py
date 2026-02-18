"""MACD calculation and crossover detection."""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple


NumberList = List[Optional[float]]


def ema(values: Iterable[float], period: int) -> NumberList:
    """Return EMA series (SMA-seeded), with ``None`` until enough data."""
    if period <= 0:
        raise ValueError("period must be > 0")

    prices = list(values)
    out: NumberList = [None] * len(prices)
    if len(prices) < period:
        return out

    seed = sum(prices[:period]) / period
    out[period - 1] = seed

    alpha = 2 / (period + 1)
    prev = seed
    for i in range(period, len(prices)):
        prev = (prices[i] - prev) * alpha + prev
        out[i] = prev

    return out


def macd_series(
    closes: Iterable[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[NumberList, NumberList, NumberList]:
    """Return macd line, signal line, and histogram."""
    prices = list(closes)
    fast = ema(prices, fast_period)
    slow = ema(prices, slow_period)

    macd_line: NumberList = []
    for f, s in zip(fast, slow):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)

    valid_macd = [v for v in macd_line if v is not None]
    signal_valid = ema(valid_macd, signal_period)

    signal_line: NumberList = [None] * len(macd_line)
    start_index = next((i for i, v in enumerate(macd_line) if v is not None), len(macd_line))
    for offset, value in enumerate(signal_valid):
        idx = start_index + offset
        if idx < len(signal_line):
            signal_line[idx] = value

    histogram: NumberList = []
    for m, s in zip(macd_line, signal_line):
        if m is None or s is None:
            histogram.append(None)
        else:
            histogram.append(m - s)

    return macd_line, signal_line, histogram


def detect_macd_crossover_age(
    closes: Iterable[float],
    fast_period: int,
    slow_period: int,
    signal_period: int,
    within_bars: int,
    bullish: bool,
) -> Optional[int]:
    """
    Detect MACD crossover age in bars.

    Returns age where 0 means crossover happened on latest completed bar.
    """
    if within_bars <= 0:
        raise ValueError("within_bars must be > 0")

    macd_line, signal_line, _ = macd_series(closes, fast_period, slow_period, signal_period)
    diffs: NumberList = []
    for m, s in zip(macd_line, signal_line):
        if m is None or s is None:
            diffs.append(None)
        else:
            diffs.append(m - s)

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
