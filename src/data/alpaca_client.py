"""Alpaca market data wrapper with in-memory caching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple

from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


@dataclass
class OHLCVBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class AlpacaDataProvider:
    """Fetches and caches stock bars from Alpaca data API."""

    def __init__(self, api_key: str, secret_key: str):
        self.client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
        self._cache: Dict[Tuple[str, str, datetime, datetime], List[OHLCVBar]] = {}

    @staticmethod
    def timeframe_from_string(value: str) -> TimeFrame:
        value = value.lower().strip()
        if value == "day":
            return TimeFrame.Day
        if value == "hour":
            return TimeFrame(1, TimeFrameUnit.Hour)
        if value == "minute":
            return TimeFrame(1, TimeFrameUnit.Minute)
        raise ValueError(f"Unsupported timeframe: {value}")

    @staticmethod
    def _estimated_delta(timeframe: TimeFrame) -> timedelta:
        if timeframe == TimeFrame.Day:
            return timedelta(days=1)
        if timeframe.unit_value == TimeFrameUnit.Hour:
            return timedelta(hours=timeframe.amount_value)
        if timeframe.unit_value == TimeFrameUnit.Minute:
            return timedelta(minutes=timeframe.amount_value)
        return timedelta(minutes=1)

    def get_bars(
        self,
        symbols: Iterable[str],
        timeframe: TimeFrame,
        start: datetime,
        end: datetime,
    ) -> Dict[str, List[OHLCVBar]]:
        """Fetch bar data for symbols, with cache and latest-forming-bar pruning."""
        symbols = [s.upper() for s in symbols]
        missing = [s for s in symbols if (s, str(timeframe), start, end) not in self._cache]

        if missing:
            request = StockBarsRequest(
                symbol_or_symbols=missing,
                timeframe=timeframe,
                start=start,
                end=end,
            )
            bars_response = self.client.get_stock_bars(request)

            for symbol in missing:
                symbol_bars = bars_response.data.get(symbol, [])
                converted = [
                    OHLCVBar(
                        timestamp=bar.timestamp,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=bar.volume,
                    )
                    for bar in symbol_bars
                ]
                self._cache[(symbol, str(timeframe), start, end)] = self._prune_incomplete_bar(converted, timeframe)

        return {s: self._cache.get((s, str(timeframe), start, end), []) for s in symbols}

    def _prune_incomplete_bar(self, bars: List[OHLCVBar], timeframe: TimeFrame) -> List[OHLCVBar]:
        if not bars:
            return bars

        delta = self._estimated_delta(timeframe)
        now_utc = datetime.now(timezone.utc)
        if bars[-1].timestamp + delta > now_utc:
            return bars[:-1]

        return bars


def build_date_range(lookback_days: int, end_date: date | None = None) -> Tuple[datetime, datetime]:
    """Build UTC datetime range used for historical requests."""
    if lookback_days <= 0:
        raise ValueError("lookback_days must be > 0")

    end = datetime.now(timezone.utc) if end_date is None else datetime.combine(end_date, datetime.max.time(), timezone.utc)
    start = end - timedelta(days=lookback_days * 2)
    return start, end
