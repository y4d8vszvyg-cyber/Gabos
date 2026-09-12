"""Technische Indikatoren - reine pandas/numpy-Implementierungen.

Alle Funktionen erwarten eine ``pd.Series`` (meist Schlusskurse) bzw. den
OHLCV-DataFrame und geben pandas-Objekte zurueck, damit sie sich verketten
lassen.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average (gleitender Durchschnitt)."""
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder-Glaettung), Skala 0-100.

    <30 gilt klassisch als ueberverkauft, >70 als ueberkauft.
    """
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder-Glaettung entspricht EMA mit alpha = 1/window
    avg_gain = gain.ewm(alpha=1.0 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    # Wenn avg_loss==0 (nur Gewinne) -> RSI 100
    out = out.fillna(100.0)
    return out


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD-Linie, Signallinie und Histogramm.

    Returns
    -------
    (macd_line, signal_line, histogram) als ``pd.Series``.
    """
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """Bollinger-Baender: (mittleres Band, oberes Band, unteres Band, %B)."""
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = (upper - lower)
    percent_b = (series - lower) / width.replace(0.0, np.nan)
    return mid, upper, lower, percent_b


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range - Mass fuer Volatilitaet in Kurseinheiten."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1.0 / window, adjust=False).mean()


def annualized_volatility(series: pd.Series, window: int = 30, periods_per_year: int = 252) -> float:
    """Annualisierte historische Volatilitaet aus taeglichen Log-Renditen."""
    log_ret = np.log(series / series.shift(1)).dropna()
    if len(log_ret) < 2:
        return float("nan")
    recent = log_ret.tail(window)
    return float(recent.std(ddof=1) * np.sqrt(periods_per_year))


def performance(series: pd.Series, days: int) -> float:
    """Prozentuale Kursveraenderung ueber die letzten ``days`` Handelstage."""
    if len(series) <= days:
        return float("nan")
    old = series.iloc[-days - 1]
    new = series.iloc[-1]
    if old == 0:
        return float("nan")
    return float((new / old - 1.0) * 100.0)


def max_drawdown(series: pd.Series) -> float:
    """Maximaler Drawdown (groesster prozentualer Verlust vom Hoch) im Fenster."""
    running_max = series.cummax()
    drawdown = series / running_max - 1.0
    return float(drawdown.min() * 100.0)
