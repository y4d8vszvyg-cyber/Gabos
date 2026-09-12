"""Test fuer das Plot-Modul (erzeugt eine PNG-Datei, netzunabhaengig)."""

import numpy as np
import pandas as pd

from stockanalyzer import backtest, plot


def _ohlcv(close_values):
    close = pd.Series(close_values,
                      index=pd.date_range("2023-01-01", periods=len(close_values), freq="B"))
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": np.full(len(close), 1_000_000),
    })


def test_equity_curve_writes_png(tmp_path):
    rng = np.random.default_rng(5)
    df = _ohlcv(100 + np.cumsum(rng.normal(0.1, 1.2, 260)))
    result = backtest.run(df)
    out = tmp_path / "equity.png"
    path = plot.equity_curve(result, df["Close"], outfile=str(out))
    assert out.exists()
    assert out.stat().st_size > 1000       # nicht leer
    assert path == str(out)


def test_equity_curve_dark_mode(tmp_path):
    df = _ohlcv(np.linspace(80, 120, 260) + np.random.default_rng(2).normal(0, 1, 260))
    result = backtest.run(df)
    out = tmp_path / "equity_dark.png"
    plot.equity_curve(result, df["Close"], outfile=str(out), dark=True)
    assert out.exists() and out.stat().st_size > 1000
