"""Mehrere Strategie-Varianten auf derselben Historie vergleichen.

Statt einer einzigen Trendfolge werden verschiedene Parametersaetze getestet
(unterschiedliche Trend-Fenster, RSI-Grenzen, mit/ohne MACD-Bestaetigung).
So sieht man, wie robust eine Idee gegenueber ihren Einstellungen ist -
ein wichtiger Schutz gegen "Overfitting" (das Verbiegen auf die Vergangenheit).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import backtest as bt


@dataclass
class Strategy:
    name: str
    sma_window: int = 50
    rsi_max: float = 70
    use_macd: bool = True


# Sinnvolle Standard-Varianten fuer den Vergleich.
DEFAULT_STRATEGIES = [
    Strategy("Trend schnell (SMA20)", sma_window=20, rsi_max=75, use_macd=True),
    Strategy("Trend Standard (SMA50)", sma_window=50, rsi_max=70, use_macd=True),
    Strategy("Trend langsam (SMA100)", sma_window=100, rsi_max=70, use_macd=True),
    Strategy("Ohne MACD-Filter", sma_window=50, rsi_max=70, use_macd=False),
]


def compare(df: pd.DataFrame, strategies=None, fee_pct: float = 0.001,
            risk_free_rate: float = 0.03) -> list:
    """Backtestet mehrere Strategien und gibt die Ergebnisse (mit Namen) zurueck.

    Sortiert nach Sharpe-Ratio absteigend (risikoadjustierte Rendite).
    """
    if strategies is None:
        strategies = DEFAULT_STRATEGIES

    results = []
    for strat in strategies:
        res = bt.run(
            df, fee_pct=fee_pct, risk_free_rate=risk_free_rate,
            sma_window=strat.sma_window, rsi_max=strat.rsi_max, use_macd=strat.use_macd,
        )
        res.name = strat.name
        results.append(res)

    results.sort(key=lambda r: r.sharpe, reverse=True)
    return results
