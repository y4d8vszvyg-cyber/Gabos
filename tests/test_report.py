"""Tests fuer Multistrategy-Vergleich und HTML-Report (netzunabhaengig)."""

import numpy as np
import pandas as pd

from stockanalyzer import backtest, multistrategy, report


def _ohlcv(close_values):
    close = pd.Series(close_values,
                      index=pd.date_range("2022-01-03", periods=len(close_values), freq="B"))
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": np.full(len(close), 1_000_000),
    })


def _history():
    rng = np.random.default_rng(21)
    return _ohlcv(100 + np.cumsum(rng.normal(0.05, 1.3, 300)))


# --- Backtest: neue Felder ---

def test_backtest_has_drawdown_and_name():
    r = backtest.run(_history())
    assert isinstance(r.drawdown, pd.Series)
    assert (r.drawdown <= 0.0001).all()          # Drawdown ist nie positiv
    assert r.name == "Strategie"


def test_backtest_parameters_change_result():
    df = _history()
    fast = backtest.run(df, sma_window=20, rsi_max=75)
    slow = backtest.run(df, sma_window=100)
    # Unterschiedliche Parameter -> i.d.R. unterschiedliche Exposure.
    assert fast.exposure_pct != slow.exposure_pct


# --- Multistrategy ---

def test_compare_returns_all_and_sorted():
    results = multistrategy.compare(_history())
    assert len(results) == len(multistrategy.DEFAULT_STRATEGIES)
    sharpes = [r.sharpe for r in results]
    assert sharpes == sorted(sharpes, reverse=True)   # nach Sharpe absteigend
    assert all(r.name for r in results)


# --- HTML-Report ---

def test_build_html_is_standalone():
    df = _history()
    r = backtest.run(df)
    html = report.build_html(r, df["Close"])
    assert html.startswith("<!doctype html>")
    assert "<title>" in html
    assert "REPORT" in html                 # eingebettete Daten
    assert "getScreenCTM" in html           # Hover-Interaktion vorhanden
    # Keine externen Ressourcen (CSP-sicher, offline nutzbar).
    assert "http://" not in html.replace("http://www.w3.org/2000/svg", "")
    assert "https://" not in html


def test_report_with_comparison_and_meta(tmp_path):
    from stockanalyzer.analyzer import Analyzer
    from stockanalyzer import signals, fundamentals
    from stockanalyzer.analyzer import StockReport

    df = _history()
    r = backtest.run(df)
    comp = multistrategy.compare(df)
    # Minimaler StockReport zum Testen der Meta-Sektion.
    tech = signals.analyze(df)
    fund = fundamentals.analyze({"trailingPE": 15, "profitMargins": 0.2})
    sr = StockReport(
        ticker="TEST", name="Test AG", currency="EUR", last_price=123.45,
        technical=tech, fundamental=fund, combined_score=64.0,
        recommendation="KAUFEN (Accumulate)",
    )
    out = tmp_path / "report.html"
    report.write_html(str(out), r, df["Close"], report=sr, comparison=comp)
    text = out.read_text(encoding="utf-8")
    assert out.exists() and len(text) > 5000
    assert "Test AG" in text
    assert "comparison" in text
