- 👋 Hi, I’m Russ
- 👀 I’m interested in python data science and android development.
- 🌱 I’m currently learning python and data science
- 💞️ I’m looking to collaborate on interesting python projects.
- 📫 How to reach me @rusty4104 on twitter.

<!---
rusty4104/rusty4104 is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
--->

## SMA Trading Strategy

The `sma_strategy.py` script demonstrates a simple moving average (SMA) crossover strategy using [Alpaca](https://alpaca.markets/) for both market data and order execution.

```bash
python sma_strategy.py AAPL --short 20 --long 50 --qty 10 --dry-run
```

By removing `--dry-run`, the script will submit market orders to your Alpaca account when a crossover signal is detected.

Set the environment variables `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, and optionally `APCA_API_BASE_URL` (defaults to Alpaca's paper trading API) before running the script.
