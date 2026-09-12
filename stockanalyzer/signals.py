"""Technische Signale bilden und zu einem Gesamt-Score verdichten.

Der Ansatz ist bewusst transparent: jede Regel liefert einen Beitrag zwischen
etwa -1 und +1, versehen mit einer Begruendung. Die Summe wird auf 0..100
skaliert. So ist jederzeit nachvollziehbar, *warum* ein Signal entsteht -
im Gegensatz zu einer Black-Box.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import indicators as ind


@dataclass
class TechnicalScore:
    score: float                      # 0..100, hoeher = bullischer
    signals: list = field(default_factory=list)   # (Name, Beitrag, Begruendung)
    metrics: dict = field(default_factory=dict)


def _last(series: pd.Series) -> float:
    val = series.dropna()
    return float(val.iloc[-1]) if len(val) else float("nan")


def analyze(df: pd.DataFrame) -> TechnicalScore:
    close = df["Close"]
    signals: list = []
    metrics: dict = {}
    contrib = 0.0

    # --- Trend: Preis vs. gleitende Durchschnitte ---
    sma50 = ind.sma(close, 50)
    sma200 = ind.sma(close, 200)
    price = _last(close)
    s50, s200 = _last(sma50), _last(sma200)
    metrics["SMA50"] = s50
    metrics["SMA200"] = s200

    if not np.isnan(s50):
        if price > s50:
            contrib += 0.6
            signals.append(("Trend kurz/mittel", +0.6, "Kurs ueber SMA50 (Aufwaertstrend)"))
        else:
            contrib -= 0.6
            signals.append(("Trend kurz/mittel", -0.6, "Kurs unter SMA50 (Abwaertsdruck)"))

    if not np.isnan(s200):
        if price > s200:
            contrib += 0.6
            signals.append(("Trend langfristig", +0.6, "Kurs ueber SMA200 (Bullenmarkt)"))
        else:
            contrib -= 0.6
            signals.append(("Trend langfristig", -0.6, "Kurs unter SMA200 (Baerenmarkt)"))

    # Golden / Death Cross
    if not np.isnan(s50) and not np.isnan(s200):
        if s50 > s200:
            contrib += 0.4
            signals.append(("Golden Cross", +0.4, "SMA50 ueber SMA200"))
        else:
            contrib -= 0.4
            signals.append(("Death Cross", -0.4, "SMA50 unter SMA200"))

    # --- Momentum: RSI ---
    rsi_series = ind.rsi(close, 14)
    rsi_val = _last(rsi_series)
    metrics["RSI(14)"] = rsi_val
    if not np.isnan(rsi_val):
        if rsi_val < 30:
            contrib += 0.5
            signals.append(("RSI", +0.5, f"ueberverkauft ({rsi_val:.0f}) - moegliche Erholung"))
        elif rsi_val > 70:
            contrib -= 0.5
            signals.append(("RSI", -0.5, f"ueberkauft ({rsi_val:.0f}) - Rueckschlagrisiko"))
        elif rsi_val > 50:
            contrib += 0.2
            signals.append(("RSI", +0.2, f"positives Momentum ({rsi_val:.0f})"))
        else:
            contrib -= 0.2
            signals.append(("RSI", -0.2, f"schwaches Momentum ({rsi_val:.0f})"))

    # --- MACD ---
    macd_line, signal_line, hist = ind.macd(close)
    macd_val, sig_val, hist_val = _last(macd_line), _last(signal_line), _last(hist)
    metrics["MACD"] = macd_val
    metrics["MACD-Signal"] = sig_val
    if not np.isnan(hist_val):
        if macd_val > sig_val:
            contrib += 0.4
            signals.append(("MACD", +0.4, "MACD ueber Signallinie (bullisch)"))
        else:
            contrib -= 0.4
            signals.append(("MACD", -0.4, "MACD unter Signallinie (baerisch)"))

    # --- Bollinger %B ---
    _, _, _, pct_b = ind.bollinger_bands(close, 20, 2.0)
    pb = _last(pct_b)
    metrics["Bollinger %B"] = pb
    if not np.isnan(pb):
        if pb < 0.0:
            contrib += 0.3
            signals.append(("Bollinger", +0.3, "Kurs unter unterem Band (ueberverkauft)"))
        elif pb > 1.0:
            contrib -= 0.3
            signals.append(("Bollinger", -0.3, "Kurs ueber oberem Band (ueberkauft)"))

    # --- Momentum ueber Zeitfenster ---
    perf_1m = ind.performance(close, 21)
    perf_3m = ind.performance(close, 63)
    metrics["Perf. 1M %"] = perf_1m
    metrics["Perf. 3M %"] = perf_3m
    if not np.isnan(perf_3m):
        if perf_3m > 10:
            contrib += 0.3
            signals.append(("Momentum 3M", +0.3, f"+{perf_3m:.1f}% in 3 Monaten"))
        elif perf_3m < -10:
            contrib -= 0.3
            signals.append(("Momentum 3M", -0.3, f"{perf_3m:.1f}% in 3 Monaten"))

    # --- Volatilitaet / Risiko (nur Kennzahlen) ---
    metrics["Volatilitaet p.a. %"] = ind.annualized_volatility(close, 30) * 100
    metrics["Max Drawdown %"] = ind.max_drawdown(close)
    metrics["ATR(14)"] = _last(ind.atr(df, 14))

    # Beitraege liegen grob in [-3.3, +3.3]. Auf 0..100 skalieren.
    max_abs = 3.3
    normalized = max(-1.0, min(1.0, contrib / max_abs))
    score = 50.0 + normalized * 50.0
    return TechnicalScore(score=round(score, 1), signals=signals, metrics=metrics)


def recommendation_label(combined_score: float) -> str:
    """Uebersetzt den kombinierten Score in ein Label."""
    if combined_score >= 70:
        return "STARK KAUFEN (Buy)"
    if combined_score >= 58:
        return "KAUFEN (Accumulate)"
    if combined_score >= 42:
        return "HALTEN (Hold)"
    if combined_score >= 30:
        return "REDUZIEREN (Reduce)"
    return "VERKAUFEN (Sell)"
