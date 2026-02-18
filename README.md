# GTK4 Alpaca Stock Screener

Linux desktop stock screener built with **Python 3 + GTK4 (PyGObject)**.

It fetches historical bars from **Alpaca Market Data (alpaca-py)** and filters symbols by:

- MACD bullish/bearish signal-line crossovers.
- Optional moving-average bullish/bearish crossovers.
- Configurable crossover detection window: within last `N` bars.

## Features

- GTK4 desktop app (`Gtk.Application` + `Gtk.ApplicationWindow`) with:
  - Header bar
  - Filter panel
  - Sortable results table
  - Detail pane with sparkline chart
  - Status bar/progress text
- Alpaca market data via `StockHistoricalDataClient`
- Background scan thread to avoid UI freezing
- In-memory OHLCV cache per symbol/timeframe/date-range
- Symbol input via paste textarea or file load
- Settings dialog for API keys (no disk persistence)
- API keys also read from environment:
  - `ALPACA_API_KEY`
  - `ALPACA_SECRET_KEY`
- Unit tests for indicator math and crossover detection (pytest)

## Project Structure

```text
src/
  app.py
  ui/
    main_window.py
  data/
    alpaca_client.py
  indicators/
    macd.py
    moving_averages.py
  screener/
    engine.py
  utils/
    logging.py
tests/
  test_indicators.py
requirements.txt
README.md
```

## Ubuntu Setup

### 1) Install system dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
  libgirepository1.0-dev libcairo2-dev pkg-config \
  gir1.2-gtk-4.0 python3-gi python3-gi-cairo
```

### 2) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> Note: PyGObject may use system GTK bindings already provided by apt packages.

### 4) Configure Alpaca credentials

```bash
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
```

(You can also set/edit keys in the app **Settings** dialog at runtime.)

### 5) Run the application

```bash
PYTHONPATH=src python3 src/app.py
```

### 6) Run tests

```bash
PYTHONPATH=src pytest -q
```

## Usage

1. Paste symbols in the symbols box (one ticker per line or comma-separated).
2. Select timeframe, lookback, and optional end date.
3. Enable MACD and/or MA filters.
4. Adjust MACD (`fast`, `slow`, `signal`) and MA (`fast`, `slow`) parameters.
5. Set “within last N bars”.
6. Click **Run Scan**.
7. Click any result row to view a detail summary and sparkline chart.

## How it works

1. **UI (`src/ui/main_window.py`)** collects scan settings and symbols.
2. UI starts a **background thread** and calls the screener engine.
3. **Engine (`src/screener/engine.py`)** validates symbols, chunks requests, and reports progress.
4. Engine calls **Alpaca provider (`src/data/alpaca_client.py`)** to fetch and cache OHLCV bars.
5. Engine computes indicators via:
   - **MACD (`src/indicators/macd.py`)**
   - **Moving averages (`src/indicators/moving_averages.py`)**
6. Crossover matches are returned to UI and rendered in the sortable table.
7. Selecting a row updates the detail pane and sparkline.

## Notes

- For intraday timeframes, currently forming bar is pruned to avoid false crossover on incomplete data.
- Invalid symbols are skipped and shown as warnings in status text.
- Credentials are held in memory only unless you choose to export env vars in your shell profile.
