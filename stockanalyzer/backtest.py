"""Backtesting: Wie haetten die Signale historisch abgeschnitten?

Der Ansatz ist bewusst einfach und transparent (kein Overfitting):
Es wird eine **Long/Flat-Trendfolge-Strategie** getestet, die genau die
Bausteine nutzt, die auch im Live-Scoring stecken:

    Long (investiert),  wenn Kurs > SMA50  UND  MACD > Signallinie  UND  RSI < 70
    Flat (Cash),        sonst

Verglichen wird gegen "Buy & Hold". Zusaetzlich werden Kennzahlen berechnet,
mit denen man Strategien serioes beurteilt: Gesamtrendite, annualisierte
Rendite, Volatilitaet, Sharpe-Ratio, maximaler Drawdown, Trefferquote.

WICHTIG: Ein guter Backtest ist KEINE Garantie fuer die Zukunft. Vergangene
Signale koennen sich jederzeit anders verhalten. Transaktionskosten/Spreads
sind vereinfacht als fixe Gebuehr je Positionswechsel modelliert.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import indicators as ind


@dataclass
class BacktestResult:
    total_return_pct: float          # Gesamtrendite der Strategie
    buy_hold_return_pct: float       # Vergleich: einfach halten
    annual_return_pct: float
    annual_volatility_pct: float
    sharpe: float
    max_drawdown_pct: float
    win_rate_pct: float              # Anteil profitabler Handelstage (investiert)
    num_trades: int                  # Anzahl Positionswechsel
    exposure_pct: float              # Anteil der Zeit investiert
    equity_curve: pd.Series          # Kapitalkurve (Start = 1.0)
    signal: pd.Series                # 1 = investiert, 0 = Cash
    drawdown: pd.Series              # laufender Drawdown in % (<= 0)
    name: str = "Strategie"          # Bezeichnung der Strategie-Variante


def generate_positions(df: pd.DataFrame, sma_window: int = 50,
                       rsi_max: float = 70, use_macd: bool = True) -> pd.Series:
    """Erzeugt das taegliche Long/Flat-Signal (1/0) aus den Indikatoren.

    Parameters
    ----------
    sma_window: Fenster des Trendfilters (Kurs muss darueber liegen).
    rsi_max:    RSI-Obergrenze - oberhalb gilt der Markt als ueberkauft (kein Neueinstieg).
    use_macd:   Zusaetzliche MACD-Bestaetigung verlangen.
    """
    close = df["Close"]
    sma = ind.sma(close, sma_window)
    rsi = ind.rsi(close, 14)

    long_cond = (close > sma) & (rsi < rsi_max)
    if use_macd:
        macd_line, signal_line, _ = ind.macd(close)
        long_cond = long_cond & (macd_line > signal_line)
    return long_cond.fillna(False).astype(int)


def run(df: pd.DataFrame, fee_pct: float = 0.001, risk_free_rate: float = 0.03,
        periods_per_year: int = 252, sma_window: int = 50,
        rsi_max: float = 70, use_macd: bool = True) -> BacktestResult:
    """Fuehrt den Backtest auf einer OHLCV-Historie aus.

    Die Strategieparameter (``sma_window``, ``rsi_max``, ``use_macd``) erlauben
    den Vergleich mehrerer Varianten.

    Parameters
    ----------
    fee_pct: Gebuehr je Positionswechsel (0.001 = 0,1%).
    """
    close = df["Close"]
    daily_ret = close.pct_change().fillna(0.0)

    # Signal von *gestern* bestimmt die heutige Position (kein Look-ahead-Bias).
    position = generate_positions(
        df, sma_window=sma_window, rsi_max=rsi_max, use_macd=use_macd
    ).shift(1).fillna(0)

    # Gebuehren bei jedem Wechsel der Position.
    switches = position.diff().abs().fillna(0)
    fees = switches * fee_pct

    strat_ret = position * daily_ret - fees
    equity = (1.0 + strat_ret).cumprod()

    total_return = float(equity.iloc[-1] - 1.0) * 100
    buy_hold = float(close.iloc[-1] / close.iloc[0] - 1.0) * 100

    n = len(daily_ret)
    years = max(n / periods_per_year, 1e-9)
    ann_return = float((equity.iloc[-1]) ** (1 / years) - 1.0) * 100 if equity.iloc[-1] > 0 else -100.0
    ann_vol = float(strat_ret.std(ddof=1) * np.sqrt(periods_per_year)) * 100

    excess = strat_ret - risk_free_rate / periods_per_year
    sharpe = float(excess.mean() / strat_ret.std(ddof=1) * np.sqrt(periods_per_year)) \
        if strat_ret.std(ddof=1) > 0 else 0.0

    running_max = equity.cummax()
    drawdown = (equity / running_max - 1.0) * 100
    max_dd = float(drawdown.min())

    invested = strat_ret[position > 0]
    win_rate = float((invested > 0).mean()) * 100 if len(invested) else 0.0
    num_trades = int(switches.sum())
    exposure = float((position > 0).mean()) * 100

    return BacktestResult(
        total_return_pct=round(total_return, 2),
        buy_hold_return_pct=round(buy_hold, 2),
        annual_return_pct=round(ann_return, 2),
        annual_volatility_pct=round(ann_vol, 2),
        sharpe=round(sharpe, 2),
        max_drawdown_pct=round(max_dd, 2),
        win_rate_pct=round(win_rate, 1),
        num_trades=num_trades,
        exposure_pct=round(exposure, 1),
        equity_curve=equity,
        signal=position,
        drawdown=drawdown.round(3),
    )
