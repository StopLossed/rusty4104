"""Screener engine orchestration for fetching and indicator filtering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from threading import Event
from typing import Callable, Iterable, List, Optional

from data.alpaca_client import AlpacaDataProvider, build_date_range
from indicators.macd import detect_macd_crossover_age, macd_series
from indicators.moving_averages import detect_ma_crossover_age, sma


SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


@dataclass
class ScanConfig:
    symbols_text: str
    timeframe: str = "Day"
    lookback_days: int = 180
    end_date: Optional[date] = None
    within_bars: int = 1

    use_macd: bool = True
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    use_ma: bool = False
    ma_fast: int = 20
    ma_slow: int = 200


@dataclass
class ScanResult:
    symbol: str
    last_close: float
    signal_type: str
    signal_age: int
    macd: Optional[float]
    signal_line: Optional[float]
    histogram: Optional[float]
    fast_ma: Optional[float]
    slow_ma: Optional[float]
    last_bar_time: str
    close_series: List[float]


def parse_symbols(raw_text: str) -> tuple[list[str], list[str]]:
    tokens = re.split(r"[\s,;]+", raw_text.upper().strip())
    valid: list[str] = []
    invalid: list[str] = []
    for token in tokens:
        if not token:
            continue
        if SYMBOL_RE.match(token):
            valid.append(token)
        else:
            invalid.append(token)

    deduped = list(dict.fromkeys(valid))
    return deduped, invalid


class ScreenerEngine:
    """Handles scan lifecycle and signal matching."""

    def __init__(self, provider: AlpacaDataProvider):
        self.provider = provider

    def run_scan(
        self,
        config: ScanConfig,
        cancel_event: Event,
        progress_cb: Callable[[int, int, int], None],
    ) -> tuple[list[ScanResult], list[str], list[str]]:
        symbols, invalid = parse_symbols(config.symbols_text)
        if not symbols:
            return [], invalid, []

        timeframe = self.provider.timeframe_from_string(config.timeframe)
        start, end = build_date_range(config.lookback_days, config.end_date)

        results: list[ScanResult] = []
        warnings: list[str] = []
        chunk_size = 25

        for start_idx in range(0, len(symbols), chunk_size):
            if cancel_event.is_set():
                break

            chunk = symbols[start_idx : start_idx + chunk_size]
            bars_by_symbol = self.provider.get_bars(chunk, timeframe, start, end)

            for symbol in chunk:
                if cancel_event.is_set():
                    break

                bars = bars_by_symbol.get(symbol, [])
                closes = [b.close for b in bars]
                if len(closes) < max(config.ma_slow, config.macd_slow + config.macd_signal + 3):
                    warnings.append(f"{symbol}: not enough bars for selected indicators")
                    progress_cb(min(start_idx + chunk.index(symbol) + 1, len(symbols)), len(symbols), len(results))
                    continue

                last = bars[-1]
                macd_line, signal_line, histogram = macd_series(
                    closes,
                    config.macd_fast,
                    config.macd_slow,
                    config.macd_signal,
                )
                fast_sma = sma(closes, config.ma_fast)
                slow_sma = sma(closes, config.ma_slow)

                symbol_matches = self._evaluate_symbol(
                    symbol=symbol,
                    closes=closes,
                    last_close=last.close,
                    last_bar_time=last.timestamp.isoformat(),
                    config=config,
                    macd_line=macd_line,
                    signal_line=signal_line,
                    histogram=histogram,
                    fast_sma=fast_sma,
                    slow_sma=slow_sma,
                )
                results.extend(symbol_matches)
                progress_cb(min(start_idx + chunk.index(symbol) + 1, len(symbols)), len(symbols), len(results))

        return results, invalid, warnings

    def _evaluate_symbol(
        self,
        *,
        symbol: str,
        closes: list[float],
        last_close: float,
        last_bar_time: str,
        config: ScanConfig,
        macd_line: list[Optional[float]],
        signal_line: list[Optional[float]],
        histogram: list[Optional[float]],
        fast_sma: list[Optional[float]],
        slow_sma: list[Optional[float]],
    ) -> list[ScanResult]:
        matches: list[ScanResult] = []

        if config.use_macd:
            for bullish, label in ((True, "MACD Bull"), (False, "MACD Bear")):
                age = detect_macd_crossover_age(
                    closes,
                    config.macd_fast,
                    config.macd_slow,
                    config.macd_signal,
                    config.within_bars,
                    bullish,
                )
                if age is not None:
                    matches.append(
                        ScanResult(
                            symbol=symbol,
                            last_close=last_close,
                            signal_type=label,
                            signal_age=age,
                            macd=macd_line[-1],
                            signal_line=signal_line[-1],
                            histogram=histogram[-1],
                            fast_ma=fast_sma[-1],
                            slow_ma=slow_sma[-1],
                            last_bar_time=last_bar_time,
                            close_series=closes,
                        )
                    )

        if config.use_ma:
            for bullish, label in ((True, "MA Bull"), (False, "MA Bear")):
                age = detect_ma_crossover_age(
                    closes,
                    config.ma_fast,
                    config.ma_slow,
                    config.within_bars,
                    bullish,
                )
                if age is not None:
                    matches.append(
                        ScanResult(
                            symbol=symbol,
                            last_close=last_close,
                            signal_type=label,
                            signal_age=age,
                            macd=macd_line[-1],
                            signal_line=signal_line[-1],
                            histogram=histogram[-1],
                            fast_ma=fast_sma[-1],
                            slow_ma=slow_sma[-1],
                            last_bar_time=last_bar_time,
                            close_series=closes,
                        )
                    )

        return matches
