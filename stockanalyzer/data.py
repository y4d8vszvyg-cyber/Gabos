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


def fetch(ticker: str, period: str = "1y", interval: str = "1d",
          source: str = "auto") -> MarketData:
    """Laedt Kurshistorie und Fundamentaldaten fuer einen Ticker.

    Parameters
    ----------
    ticker:   Symbol, z.B. "AAPL", "MSFT", "SAP.DE".
    period:   Zeitraum der Historie ("6mo", "1y", "2y", "5y", "max").
    interval: Kerzen-Intervall ("1d", "1wk", "1mo").
    source:   "auto" (Yahoo, bei Fehler Stooq), "yahoo" oder "stooq".
    """
    if source == "stooq":
        return _fetch_stooq(ticker, period)
    try:
        return _fetch_yahoo(ticker, period, interval)
    except DataError:
        if source == "yahoo":
            raise
        # Auto-Fallback auf Stooq (kein API-Key noetig).
        return _fetch_stooq(ticker, period)


def _fetch_yahoo(ticker: str, period: str, interval: str) -> MarketData:
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


_PERIOD_DAYS = {"6mo": 190, "1y": 370, "2y": 740, "5y": 1830, "max": 100000}


def _fetch_stooq(ticker: str, period: str) -> MarketData:
    """Laedt Tageskurse von Stooq (CSV, ohne API-Key).

    US-Symbole brauchen bei Stooq das Suffix ``.us`` (wird ergaenzt, falls
    kein Punkt im Symbol steht). Indizes wie ``^SPX`` funktionieren direkt.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise DataError("Leeres Ticker-Symbol.")

    symbol = ticker if ("." in ticker or ticker.startswith("^")) else f"{ticker}.US"
    url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&i=d"

    try:
        df = pd.read_csv(url)
    except Exception as exc:  # noqa: BLE001
        raise DataError(f"Stooq-Daten fuer '{ticker}' nicht ladbar: {exc}") from exc

    if df is None or df.empty or "Close" not in df.columns:
        raise DataError(
            f"Keine Stooq-Daten fuer '{ticker}'. Symbol korrekt? "
            f"(US-Aktien: reines Symbol, dt. Aktien: z.B. 'SAP.DE')."
        )

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    days = _PERIOD_DAYS.get(period, 370)
    df = df.tail(min(len(df), days)).dropna(subset=["Close"])

    if len(df) < 20:
        raise DataError(f"Zu wenige Stooq-Datenpunkte fuer '{ticker}' ({len(df)}).")

    # Stooq liefert keine Fundamentaldaten -> info bleibt leer.
    return MarketData(ticker=ticker, history=df, info={})


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
