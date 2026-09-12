"""Tests fuer Backtest, Positionsgroessen und Watchlist (netzunabhaengig)."""

import numpy as np
import pandas as pd
import pytest

from stockanalyzer import backtest, portfolio, watchlist


def _ohlcv(close_values):
    close = pd.Series(close_values, index=pd.date_range("2023-01-01", periods=len(close_values), freq="B"))
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": np.full(len(close), 1_000_000),
    })


# --- Backtest ---

def test_backtest_uptrend_makes_money():
    # Verrauschter Aufwaertstrend (eine perfekt gerade Linie haette RSI=100
    # und die Strategie bliebe korrekterweise komplett draussen).
    rng = np.random.default_rng(11)
    trend = np.linspace(50, 150, 260)
    noise = np.cumsum(rng.normal(0, 1.2, 260))
    df = _ohlcv(trend + noise)
    result = backtest.run(df)
    assert result.total_return_pct > 0
    assert 0 <= result.exposure_pct <= 100
    assert result.equity_curve.iloc[-1] > 0


def test_backtest_positions_are_binary():
    df = _ohlcv(100 + np.cumsum(np.random.default_rng(3).normal(0, 1, 200)))
    pos = backtest.generate_positions(df)
    assert set(pos.unique()).issubset({0, 1})


def test_backtest_no_lookahead_flat_start():
    # Am ersten Tag kann noch keine Position bestehen (Signal von "gestern").
    df = _ohlcv(np.linspace(50, 150, 260))
    result = backtest.run(df)
    assert result.signal.iloc[0] == 0


def test_backtest_metrics_finite():
    df = _ohlcv(100 + np.cumsum(np.random.default_rng(9).normal(0, 1.5, 300)))
    r = backtest.run(df)
    for value in [r.sharpe, r.max_drawdown_pct, r.annual_return_pct, r.annual_volatility_pct]:
        assert np.isfinite(value)


# --- Positionsgroesse ---

def test_position_size_respects_risk():
    plan = portfolio.position_size(
        capital=10_000, entry_price=100, stop_price=90, risk_per_trade_pct=2.0,
    )
    # Risiko je Aktie = 10, erlaubtes Risiko = 200 -> 20 Stueck
    assert plan.shares == 20
    assert plan.risk_amount == pytest.approx(200.0)
    assert plan.stop_price == 90


def test_position_size_capped_by_max_position():
    # Enger Stop wuerde riesige Position erlauben -> Positionslimit greift.
    plan = portfolio.position_size(
        capital=10_000, entry_price=100, stop_price=99.9,
        risk_per_trade_pct=5.0, max_position_pct=20.0,
    )
    assert plan.position_value <= 2_000 + 1e-6
    assert "Positionslimit" in plan.note


def test_position_size_from_atr():
    plan = portfolio.position_size(
        capital=50_000, entry_price=200, atr=5, atr_multiple=2.0, risk_per_trade_pct=1.0,
    )
    assert plan.stop_price == pytest.approx(190.0)
    assert plan.shares == int((50_000 * 0.01) // 10)


def test_position_size_reward_to_risk():
    plan = portfolio.position_size(
        capital=10_000, entry_price=100, stop_price=90, target_price=130,
    )
    assert plan.reward_to_risk == pytest.approx(3.0)


def test_position_size_invalid_stop_raises():
    with pytest.raises(ValueError):
        portfolio.position_size(capital=10_000, entry_price=100, stop_price=110)


# --- Watchlist ---

def test_watchlist_parsing(tmp_path):
    f = tmp_path / "wl.txt"
    f.write_text(
        "# Kommentar\n\nAAPL   # Apple\nmsft\nAAPL\n  SAP.DE  \n", encoding="utf-8"
    )
    result = watchlist.load(str(f))
    assert result == ["AAPL", "MSFT", "SAP.DE"]   # dedupliziert, gross, Kommentare weg


def test_watchlist_missing_file():
    with pytest.raises(FileNotFoundError):
        watchlist.load("/nicht/vorhanden/xyz.txt")
