"""Fundamentale Kennzahlen aus den yfinance-``info``-Daten bewerten.

Die Fundamentaldaten von Yahoo sind unvollstaendig/uneinheitlich. Fehlende
Werte werden neutral behandelt und nicht als Fehler gewertet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


def _num(info: dict, *keys) -> Optional[float]:
    """Ersten vorhandenen, numerischen Wert aus mehreren moeglichen Keys holen."""
    for key in keys:
        val = info.get(key)
        if isinstance(val, (int, float)) and val == val:  # nicht NaN
            return float(val)
    return None


@dataclass
class FundamentalScore:
    score: float                      # 0..100, hoeher = fundamental attraktiver
    points: list = field(default_factory=list)   # (Kennzahl, Wert, Beitrag, Kommentar)
    metrics: dict = field(default_factory=dict)   # Rohwerte fuer die Anzeige


def analyze(info: dict) -> FundamentalScore:
    """Bewertet Bewertung, Profitabilitaet, Verschuldung und Wachstum."""
    points: list = []
    metrics: dict = {}
    score = 50.0  # neutraler Startwert

    pe = _num(info, "trailingPE", "forwardPE")
    metrics["KGV (P/E)"] = pe
    if pe is not None:
        if pe <= 0:
            points.append(("KGV", pe, -10, "negativ (Verlust)"))
            score -= 10
        elif pe < 15:
            points.append(("KGV", pe, +12, "guenstig bewertet"))
            score += 12
        elif pe < 25:
            points.append(("KGV", pe, +4, "moderate Bewertung"))
            score += 4
        elif pe < 40:
            points.append(("KGV", pe, -4, "erhoehte Bewertung"))
            score -= 4
        else:
            points.append(("KGV", pe, -10, "sehr teuer"))
            score -= 10

    peg = _num(info, "trailingPegRatio", "pegRatio")
    metrics["PEG"] = peg
    if peg is not None and peg > 0:
        if peg < 1:
            points.append(("PEG", peg, +8, "Wachstum guenstig eingepreist"))
            score += 8
        elif peg > 2:
            points.append(("PEG", peg, -6, "Wachstum teuer eingepreist"))
            score -= 6

    margin = _num(info, "profitMargins")
    metrics["Nettomarge"] = margin
    if margin is not None:
        if margin > 0.20:
            points.append(("Nettomarge", margin, +10, "sehr profitabel"))
            score += 10
        elif margin > 0.08:
            points.append(("Nettomarge", margin, +5, "solide profitabel"))
            score += 5
        elif margin < 0:
            points.append(("Nettomarge", margin, -12, "unprofitabel"))
            score -= 12

    roe = _num(info, "returnOnEquity")
    metrics["Eigenkapitalrendite (ROE)"] = roe
    if roe is not None:
        if roe > 0.20:
            points.append(("ROE", roe, +8, "hohe Kapitalrendite"))
            score += 8
        elif roe < 0:
            points.append(("ROE", roe, -6, "negative Kapitalrendite"))
            score -= 6

    d2e = _num(info, "debtToEquity")
    metrics["Verschuldung (D/E)"] = d2e
    if d2e is not None:
        # yfinance liefert D/E teils in Prozent (z.B. 150 statt 1.5)
        ratio = d2e / 100.0 if d2e > 5 else d2e
        if ratio < 0.5:
            points.append(("D/E", d2e, +6, "niedrige Verschuldung"))
            score += 6
        elif ratio > 2.0:
            points.append(("D/E", d2e, -8, "hohe Verschuldung"))
            score -= 8

    rev_growth = _num(info, "revenueGrowth")
    metrics["Umsatzwachstum"] = rev_growth
    if rev_growth is not None:
        if rev_growth > 0.15:
            points.append(("Umsatzwachstum", rev_growth, +8, "starkes Wachstum"))
            score += 8
        elif rev_growth < 0:
            points.append(("Umsatzwachstum", rev_growth, -6, "schrumpfender Umsatz"))
            score -= 6

    div_yield = _num(info, "dividendYield")
    metrics["Dividendenrendite"] = div_yield
    if div_yield is not None and div_yield > 0:
        # Yahoo liefert teils 0.03, teils 3.0 - normalisieren auf Anteil
        y = div_yield / 100.0 if div_yield > 1 else div_yield
        if 0.02 <= y <= 0.08:
            points.append(("Dividende", div_yield, +4, "attraktive Ausschuettung"))
            score += 4

    score = max(0.0, min(100.0, score))
    return FundamentalScore(score=score, points=points, metrics=metrics)
