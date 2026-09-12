"""Tests fuer die netzunabhaengigen Kernfunktionen (Mathematik/Logik).

Bewusst ohne yfinance/Netzwerk - hier wird die Korrektheit der Modelle geprueft.
"""

import math

import numpy as np
import pandas as pd
import pytest

from stockanalyzer import indicators as ind
from stockanalyzer import options as opt
from stockanalyzer import signals, fundamentals


def _series(values):
    idx = pd.date_range("2023-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=idx)


# --- Indikatoren ---

def test_sma_basic():
    s = _series([1, 2, 3, 4, 5])
    result = ind.sma(s, 3).dropna().tolist()
    assert result == pytest.approx([2.0, 3.0, 4.0])


def test_rsi_all_gains_is_100():
    s = _series(list(range(1, 40)))  # nur steigend
    assert ind.rsi(s, 14).iloc[-1] == pytest.approx(100.0, abs=1e-6)


def test_rsi_bounds():
    rng = np.random.default_rng(42)
    s = _series(100 + np.cumsum(rng.normal(0, 1, 200)))
    r = ind.rsi(s, 14).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_macd_shapes():
    s = _series(100 + np.cumsum(np.random.default_rng(1).normal(0, 1, 100)))
    macd_line, signal_line, hist = ind.macd(s)
    assert len(macd_line) == len(signal_line) == len(hist) == len(s)


# --- Black-Scholes / Optionen ---

def test_put_call_parity():
    # C - P = S*e^{-qT} - K*e^{-rT}
    S, K, T, r, sigma, q = 100, 100, 0.5, 0.03, 0.2, 0.0
    c = opt.black_scholes(S, K, T, r, sigma, "call", q)
    p = opt.black_scholes(S, K, T, r, sigma, "put", q)
    lhs = c - p
    rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    assert lhs == pytest.approx(rhs, abs=1e-6)


def test_call_price_known_value():
    # Standard-Lehrbuchbeispiel: S=K=100, T=1, r=5%, sigma=20% -> ~10.4506
    price = opt.black_scholes(100, 100, 1.0, 0.05, 0.20, "call")
    assert price == pytest.approx(10.4506, abs=1e-3)


def test_implied_vol_roundtrip():
    S, K, T, r, sigma = 120, 100, 0.75, 0.02, 0.35
    price = opt.black_scholes(S, K, T, r, sigma, "call")
    iv = opt.implied_volatility(price, S, K, T, r, "call")
    assert iv == pytest.approx(sigma, abs=1e-3)


def test_call_delta_between_0_and_1():
    g = opt.greeks(100, 100, 0.5, 0.03, 0.2, "call")
    assert 0.0 <= g.delta <= 1.0
    assert g.gamma > 0
    assert g.vega > 0


def test_put_delta_negative():
    g = opt.greeks(100, 100, 0.5, 0.03, 0.2, "put")
    assert -1.0 <= g.delta <= 0.0


def test_expired_option_intrinsic_value():
    assert opt.black_scholes(110, 100, 0.0, 0.03, 0.2, "call") == pytest.approx(10.0)
    assert opt.black_scholes(90, 100, 0.0, 0.03, 0.2, "put") == pytest.approx(10.0)


# --- Signale ---

def test_uptrend_scores_bullish():
    # Klar steigender Kurs -> Score sollte > 50 sein
    s = _series(np.linspace(50, 150, 250))
    df = pd.DataFrame({
        "Open": s, "High": s * 1.01, "Low": s * 0.99, "Close": s,
        "Volume": np.full(len(s), 1_000_000),
    })
    result = signals.analyze(df)
    assert result.score > 50
    assert 0 <= result.score <= 100


def test_downtrend_scores_bearish():
    s = _series(np.linspace(150, 50, 250))
    df = pd.DataFrame({
        "Open": s, "High": s * 1.01, "Low": s * 0.99, "Close": s,
        "Volume": np.full(len(s), 1_000_000),
    })
    result = signals.analyze(df)
    assert result.score < 50


def test_recommendation_labels():
    assert "KAUFEN" in signals.recommendation_label(75)
    assert "HALTEN" in signals.recommendation_label(50)
    assert "VERKAUFEN" in signals.recommendation_label(20)


# --- Fundamentaldaten ---

def test_fundamentals_cheap_profitable_scores_high():
    info = {
        "trailingPE": 12, "profitMargins": 0.25, "returnOnEquity": 0.25,
        "debtToEquity": 30, "revenueGrowth": 0.20,
    }
    result = fundamentals.analyze(info)
    assert result.score > 60


def test_fundamentals_empty_is_neutral():
    result = fundamentals.analyze({})
    assert result.score == 50.0
    assert result.points == []
