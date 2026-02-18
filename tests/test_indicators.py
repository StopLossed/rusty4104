from indicators.macd import detect_macd_crossover_age, macd_series
from indicators.moving_averages import detect_ma_crossover_age, sma


def test_sma_series():
    vals = [1, 2, 3, 4, 5]
    result = sma(vals, 3)
    assert result[:2] == [None, None]
    assert result[2:] == [2.0, 3.0, 4.0]


def test_ma_bullish_crossover_within_window():
    closes = [10, 9, 8, 7, 6, 7, 9, 12]
    age = detect_ma_crossover_age(closes, fast_period=2, slow_period=4, within_bars=3, bullish=True)
    assert age is not None
    assert age <= 2


def test_ma_bearish_crossover_within_window():
    closes = [12, 13, 14, 15, 16, 15, 13, 10]
    age = detect_ma_crossover_age(closes, fast_period=2, slow_period=4, within_bars=3, bullish=False)
    assert age is not None
    assert age <= 2


def test_macd_series_has_histogram_alignment():
    closes = [100 + i for i in range(60)]
    macd_line, signal_line, histogram = macd_series(closes)
    assert len(macd_line) == len(closes)
    assert len(signal_line) == len(closes)
    assert len(histogram) == len(closes)

    idx = len(closes) - 1
    assert macd_line[idx] is not None
    assert signal_line[idx] is not None
    assert histogram[idx] == macd_line[idx] - signal_line[idx]


def test_macd_bullish_crossover_age():
    closes = [30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 21, 22, 23, 24, 25]
    age = detect_macd_crossover_age(closes, fast_period=4, slow_period=8, signal_period=3, within_bars=5, bullish=True)
    assert age is not None
    assert age <= 4


def test_macd_bearish_crossover_absent_returns_none():
    closes = [i for i in range(1, 80)]
    age = detect_macd_crossover_age(closes, fast_period=12, slow_period=26, signal_period=9, within_bars=5, bullish=False)
    assert age is None
