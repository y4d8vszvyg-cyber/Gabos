"""Kursdaten und Fundamentaldaten beschaffen.

Die Datenquelle ist yfinance (Yahoo Finance). Netzwerkzugriff kann fehlschlagen
(kein Internet, Rate-Limits). Alle Funktionen werfen in dem Fall eine
aussagekraeftige ``DataError`` statt einer kryptischen Exception.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


class DataError(RuntimeError):
    """Wird geworfen, wenn Kurs- oder Fundamentaldaten nicht geladen werden koennen."""


@dataclass
class MarketData:
    """Container fuer die geladenen Daten eines Tickers."""

    ticker: str
    history: pd.DataFrame          # OHLCV, Index = Datum
    info: dict = field(default_factory=dict)   # Fundamentaldaten / Metadaten

    @property
    def last_price(self) -> float:
        return float(self.history["Close"].iloc[-1])

    @property
    def currency(self) -> str:
        return str(self.info.get("currency", "") or "")

    @property
    def name(self) -> str:
        return str(self.info.get("shortName") or self.info.get("longName") or self.ticker)


def _import_yfinance():
    try:
        import yfinance as yf  # noqa: WPS433 (lazy import ist gewollt)
    except ImportError as exc:  # pragma: no cover - abhaengig von Umgebung
        raise DataError(
            "yfinance ist nicht installiert. Bitte 'pip install -r requirements.txt' ausfuehren."
        ) from exc
    return yf


def fetch(ticker: str, period: str = "1y", interval: str = "1d") -> MarketData:
    """Laedt Kurshistorie und Fundamentaldaten fuer einen Ticker.

    Parameters
    ----------
    ticker:   Symbol, z.B. "AAPL", "MSFT", "SAP.DE".
    period:   Zeitraum der Historie ("6mo", "1y", "2y", "5y", "max").
    interval: Kerzen-Intervall ("1d", "1wk", "1mo").
    """
    yf = _import_yfinance()
    ticker = ticker.strip().upper()
    if not ticker:
        raise DataError("Leeres Ticker-Symbol.")

    try:
        t = yf.Ticker(ticker)
        history = t.history(period=period, interval=interval, auto_adjust=False)
    except Exception as exc:  # noqa: BLE001 - yfinance wirft diverse Fehler
        raise DataError(f"Kursdaten fuer '{ticker}' konnten nicht geladen werden: {exc}") from exc

    if history is None or history.empty:
        raise DataError(
            f"Keine Kursdaten fuer '{ticker}' gefunden. Symbol korrekt? "
            f"(Deutsche Aktien brauchen ein Suffix, z.B. 'SAP.DE')."
        )

    history = history.dropna(subset=["Close"])
    if len(history) < 20:
        raise DataError(
            f"Zu wenige Datenpunkte fuer '{ticker}' ({len(history)}). "
            f"Waehle einen laengeren Zeitraum."
        )

    info: dict = {}
    try:
        info = dict(t.info or {})
    except Exception:  # noqa: BLE001 - .info ist oft instabil, darf aber nicht blockieren
        info = {}

    return MarketData(ticker=ticker, history=history, info=info)


def fetch_option_chain(ticker: str, expiry: Optional[str] = None):
    """Laedt die Optionskette (Calls/Puts) fuer ein Verfallsdatum.

    Gibt ``(expiry, calls_df, puts_df)`` zurueck. Ohne ``expiry`` wird das
    naechste verfuegbare Datum genommen.
    """
    yf = _import_yfinance()
    t = yf.Ticker(ticker.strip().upper())

    try:
        expiries = list(t.options or [])
    except Exception as exc:  # noqa: BLE001
        raise DataError(f"Optionsdaten fuer '{ticker}' nicht verfuegbar: {exc}") from exc

    if not expiries:
        raise DataError(f"Fuer '{ticker}' sind keine Optionen verfuegbar.")

    if expiry is None:
        expiry = expiries[0]
    elif expiry not in expiries:
        raise DataError(
            f"Verfallsdatum '{expiry}' nicht verfuegbar. Verfuegbar: {', '.join(expiries[:8])}..."
        )

    chain = t.option_chain(expiry)
    return expiry, chain.calls, chain.puts, expiries
