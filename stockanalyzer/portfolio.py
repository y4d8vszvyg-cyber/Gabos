"""Positionsgroessen und Risikomanagement.

Das mit Abstand Wichtigste beim Investieren ist nicht das "beste" Signal,
sondern **wie viel** man je Position riskiert. Dieses Modul rechnet aus, wie
gross eine Position sein darf, damit ein einzelner Fehlschlag das Depot nicht
ruiniert.

Kernidee (Risk-per-Trade / Fixed-Fractional):
    Riskiere pro Trade nur einen kleinen, festen Anteil des Depots
    (z.B. 1-2%). Der Stop-Loss (haeufig aus der Volatilitaet/ATR abgeleitet)
    bestimmt zusammen mit diesem Risikobetrag die Stueckzahl.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionPlan:
    shares: int                 # empfohlene Stueckzahl (ganzzahlig)
    position_value: float       # Kapitaleinsatz fuer die Position
    position_pct: float         # Anteil am Depot
    risk_amount: float          # maximaler Verlust bis zum Stop
    stop_price: float           # Stop-Loss-Kurs
    risk_per_share: float       # Verlust je Aktie bis zum Stop
    reward_to_risk: Optional[float]  # Chance/Risiko, falls Kursziel gesetzt
    note: str


def position_size(
    capital: float,
    entry_price: float,
    stop_price: Optional[float] = None,
    risk_per_trade_pct: float = 1.0,
    atr: Optional[float] = None,
    atr_multiple: float = 2.0,
    max_position_pct: float = 20.0,
    target_price: Optional[float] = None,
) -> PositionPlan:
    """Berechnet eine risikobasierte Positionsgroesse.

    Parameters
    ----------
    capital:            Gesamtes verfuegbares Depotkapital.
    entry_price:        Geplanter Einstiegskurs.
    stop_price:         Fester Stop-Loss. Wenn None, wird er aus ``atr``
                        abgeleitet: entry - atr_multiple * atr.
    risk_per_trade_pct: Anteil des Depots, den man je Trade riskiert (1-2% ueblich).
    atr:                Average True Range zur Ableitung des Stops.
    max_position_pct:   Deckelt den Kapitaleinsatz je Position (Diversifikation).
    target_price:       Optionales Kursziel fuer die Chance/Risiko-Kennzahl.
    """
    if capital <= 0 or entry_price <= 0:
        raise ValueError("capital und entry_price muessen > 0 sein.")

    if stop_price is None:
        if atr is None or atr <= 0:
            raise ValueError("Entweder stop_price oder ein positiver atr wird benoetigt.")
        stop_price = entry_price - atr_multiple * atr

    if stop_price >= entry_price:
        raise ValueError("stop_price muss unter dem entry_price liegen (Long-Position).")

    risk_per_share = entry_price - stop_price
    risk_amount = capital * (risk_per_trade_pct / 100.0)

    shares = int(risk_amount // risk_per_share)

    # Positionsobergrenze zur Diversifikation.
    max_value = capital * (max_position_pct / 100.0)
    if shares * entry_price > max_value:
        shares = int(max_value // entry_price)
        note = f"Durch Positionslimit ({max_position_pct:.0f}% des Depots) begrenzt."
    else:
        note = f"Groesse durch Risiko je Trade ({risk_per_trade_pct:.1f}%) bestimmt."

    shares = max(shares, 0)
    position_value = shares * entry_price
    actual_risk = shares * risk_per_share

    reward_to_risk = None
    if target_price is not None and target_price > entry_price:
        reward = target_price - entry_price
        reward_to_risk = round(reward / risk_per_share, 2)

    return PositionPlan(
        shares=shares,
        position_value=round(position_value, 2),
        position_pct=round(position_value / capital * 100, 1),
        risk_amount=round(actual_risk, 2),
        stop_price=round(stop_price, 2),
        risk_per_share=round(risk_per_share, 2),
        reward_to_risk=reward_to_risk,
        note=note,
    )
