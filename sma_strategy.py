"""Simple Moving Average (SMA) trading strategy using Alpaca's API."""

import os
import argparse
import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame

API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")


def get_api() -> REST:
    """Instantiate Alpaca REST API client."""
    return REST(API_KEY, API_SECRET, base_url=BASE_URL)


def fetch_bars(symbol: str, long_window: int) -> pd.DataFrame:
    """Fetch historical daily bars for a symbol."""
    api = get_api()
    end = pd.Timestamp.now(tz="America/New_York")
    start = end - pd.Timedelta(days=long_window * 3)
    bars = api.get_bars(
        symbol,
        TimeFrame.Day,
        start.isoformat(),
        end.isoformat(),
        adjustment="raw",
    ).df
    if symbol in bars.index.get_level_values("symbol"):
        bars = bars.xs(symbol)
    if bars.empty:
        raise ValueError(f"No data returned for {symbol}")
    return bars


def compute_sma(bars: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """Append short and long SMAs to the dataframe."""
    bars["sma_short"] = bars["close"].rolling(window=short_window).mean()
    bars["sma_long"] = bars["close"].rolling(window=long_window).mean()
    return bars


def generate_signal(bars: pd.DataFrame) -> str | None:
    """Generate trading signal based on SMA crossover."""
    if len(bars) < 2:
        return None
    latest = bars.iloc[-1]
    prev = bars.iloc[-2]
    if latest["sma_short"] > latest["sma_long"] and prev["sma_short"] <= prev["sma_long"]:
        return "buy"
    if latest["sma_short"] < latest["sma_long"] and prev["sma_short"] >= prev["sma_long"]:
        return "sell"
    return None


def submit_order(symbol: str, qty: int, side: str):
    """Submit market order to Alpaca."""
    api = get_api()
    return api.submit_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="market",
        time_in_force="day",
    )


def main():
    parser = argparse.ArgumentParser(description="SMA crossover strategy using Alpaca")
    parser.add_argument("symbol", help="Ticker symbol to trade")
    parser.add_argument("--short", type=int, default=20, help="Short SMA window")
    parser.add_argument("--long", type=int, default=50, help="Long SMA window")
    parser.add_argument("--qty", type=int, default=1, help="Order quantity")
    parser.add_argument("--dry-run", action="store_true", help="Only compute signal")
    args = parser.parse_args()

    bars = fetch_bars(args.symbol, args.long)
    bars = compute_sma(bars, args.short, args.long)
    signal = generate_signal(bars)

    print(bars[["close", "sma_short", "sma_long"]].tail())
    if signal:
        print(f"Signal generated: {signal}")
        if not args.dry_run:
            order = submit_order(args.symbol, args.qty, signal)
            print(f"Order submitted: {order}")
    else:
        print("No trade signal")


if __name__ == "__main__":
    main()
