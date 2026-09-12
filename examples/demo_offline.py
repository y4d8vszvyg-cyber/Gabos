"""Offline-Demo: zeigt die komplette Analyse mit synthetischen Kursdaten.

Nuetzlich, wenn kein Internet/Yahoo-Zugriff verfuegbar ist. Erzeugt einen
kuenstlichen Aufwaertstrend, laesst die technische + fundamentale Analyse
darueber laufen und gibt einen vollstaendigen Report inklusive einer
Options-Idee aus (mit fair per Black-Scholes bewerteten Optionen).

Ausfuehren:
    python examples/demo_offline.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

# Projekt-Wurzel in den Pfad legen, damit das Skript auch direkt (ohne
# gesetztes PYTHONPATH) laufbar ist.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stockanalyzer import backtest, fundamentals, indicators, options, portfolio, signals  # noqa: E402
from stockanalyzer.signals import recommendation_label


def make_history(seed: int = 7, days: int = 300, trend: float = 0.0007) -> pd.DataFrame:
    """Erzeugt eine realistische OHLCV-Historie mit leichtem Aufwaertstrend."""
    rng = np.random.default_rng(seed)
    log_ret = rng.normal(trend, 0.015, days)
    close = 100 * np.exp(np.cumsum(log_ret))
    idx = pd.date_range("2024-01-01", periods=days, freq="B")
    high = close * (1 + np.abs(rng.normal(0, 0.008, days)))
    low = close * (1 - np.abs(rng.normal(0, 0.008, days)))
    open_ = close * (1 + rng.normal(0, 0.005, days))
    vol = rng.integers(800_000, 3_000_000, days)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol},
        index=idx,
    )


def main() -> None:
    df = make_history()
    S = float(df["Close"].iloc[-1])

    tech = signals.analyze(df)
    fund = fundamentals.analyze({
        "trailingPE": 18, "profitMargins": 0.22, "returnOnEquity": 0.24,
        "debtToEquity": 45, "revenueGrowth": 0.17, "dividendYield": 0.015,
    })
    combined = 0.6 * tech.score + 0.4 * fund.score

    print("=" * 68)
    print("  DEMO (synthetische Daten - keine echten Kurse!)")
    print("=" * 68)
    print(f"  Letzter Kurs   : {S:.2f}")
    print(f"  Technik-Score  : {tech.score:.1f} / 100")
    print(f"  Fundamental    : {fund.score:.1f} / 100")
    print(f"  GESAMT         : {combined:.1f} / 100  ->  {recommendation_label(combined)}")

    print("\n  Technische Signale:")
    for name, contrib, reason in tech.signals:
        sign = "+" if contrib > 0 else "-"
        print(f"    [{sign}] {name:<20} {reason}")

    # Beispielhafte Optionsbewertung: 30 Tage, 5% OTM Call.
    T, r, sigma = 30 / 365, 0.03, 0.30
    K = round(S * 1.05, 2)
    call = options.black_scholes(S, K, T, r, sigma, "call")
    put = options.black_scholes(S, K, T, r, sigma, "put")
    gc = options.greeks(S, K, T, r, sigma, "call")

    print("\n  Beispiel-Optionen (30 Tage, Strike 5% OTM, IV 30%):")
    print(f"    CALL @ {K:.2f}: fairer Preis {call:.2f} | Delta {gc.delta:.2f} "
          f"| Theta {gc.theta:.3f}/Tag | Vega {gc.vega:.3f}")
    print(f"    PUT  @ {K:.2f}: fairer Preis {put:.2f}")
    print("\n  Interpretation: bullisches Bild -> Long Call setzt auf steigende")
    print("  Kurse. Max. Verlust = Praemie. Theta frisst taeglich Zeitwert.")

    # --- Backtest der Trendfolge-Strategie ---
    result = backtest.run(df)
    print("\n  Backtest (Long/Flat-Trendfolge vs. Buy & Hold):")
    print(f"    Strategie : {result.total_return_pct:+.1f} %   "
          f"Buy&Hold: {result.buy_hold_return_pct:+.1f} %")
    print(f"    Sharpe    : {result.sharpe:.2f}   Max Drawdown: {result.max_drawdown_pct:.1f} %   "
          f"investiert: {result.exposure_pct:.0f}% der Zeit")
    print("    (Historische Ergebnisse sind KEINE Garantie fuer die Zukunft.)")

    # --- Positionsgroesse (risikobasiert) ---
    atr_val = float(indicators.atr(df, 14).dropna().iloc[-1])
    plan = portfolio.position_size(
        capital=10_000, entry_price=S, atr=atr_val, risk_per_trade_pct=1.0, atr_multiple=2.0,
    )
    print("\n  Positionsgroesse bei 10.000 Kapital, 1% Risiko/Trade:")
    print(f"    {plan.shares} Stueck fuer {plan.position_value:.2f} ({plan.position_pct:.1f}% Depot), "
          f"Stop {plan.stop_price:.2f}, max. Verlust {plan.risk_amount:.2f}")

    # --- Equity-Kurve als Chart speichern (falls matplotlib installiert) ---
    try:
        from stockanalyzer import plot
        path = plot.equity_curve(
            result, df["Close"],
            title="Demo - Equity-Kurve (synthetische Daten)", outfile="equity.png",
        )
        print(f"\n  Equity-Kurve gespeichert: {path}")
    except Exception as exc:  # noqa: BLE001 - Chart ist optional
        print(f"\n  (Chart uebersprungen: {exc})")


if __name__ == "__main__":
    main()
