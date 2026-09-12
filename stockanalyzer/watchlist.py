"""Watchlist aus einer Textdatei einlesen.

Format: ein Ticker pro Zeile. Leerzeilen und Kommentare (# ...) werden
ignoriert. Ein optionaler Kommentar hinter dem Symbol ist erlaubt:

    # Meine Watchlist
    AAPL      # Apple
    MSFT
    SAP.DE    # SAP (Xetra)
"""

from __future__ import annotations

import os


def load(path: str) -> list:
    """Liest Ticker-Symbole aus einer Datei und gibt sie als Liste zurueck."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Watchlist-Datei nicht gefunden: {path}")

    tickers: list = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # Inline-Kommentar abschneiden.
            symbol = line.split("#", 1)[0].strip()
            if symbol:
                tickers.append(symbol.upper())

    # Duplikate entfernen, Reihenfolge bewahren.
    seen: set = set()
    unique = []
    for tk in tickers:
        if tk not in seen:
            seen.add(tk)
            unique.append(tk)
    return unique
