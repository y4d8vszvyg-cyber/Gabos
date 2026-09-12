"""Equity-Kurve eines Backtests als Chart zeichnen (matplotlib -> PNG).

Zwei Serien im Vergleich, beide auf Startwert 100 normiert:
    * Strategie  (Long/Flat-Trendfolge)
    * Buy & Hold (einfach halten)

Design nach den Datenvisualisierungs-Regeln: duenne Linien, dezentes Grid,
direkte End-Labels (Identitaet nicht nur ueber Farbe), validierte
farbenblind-sichere Palette, heller und dunkler Modus.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .backtest import BacktestResult

# Validierte, farbenblind-sichere Kategorienpalette (Slot 1 + 2).
_LIGHT = {
    "surface": "#fcfcfb", "text": "#0b0b0b", "muted": "#52514e",
    "grid": "#e6e6e3", "strat": "#2a78d6", "hold": "#eb6834",
}
_DARK = {
    "surface": "#1a1a19", "text": "#ffffff", "muted": "#c3c2b7",
    "grid": "#33332f", "strat": "#3987e5", "hold": "#d95926",
}


def equity_curve(result: BacktestResult, close: pd.Series,
                 title: str = "Backtest: Equity-Kurve",
                 outfile: str = "equity.png", dark: bool = False,
                 dpi: int = 130) -> str:
    """Zeichnet Strategie- vs. Buy-&-Hold-Kapitalkurve und speichert ein PNG.

    Parameters
    ----------
    result:  Ergebnis aus ``backtest.run``.
    close:   Schlusskurs-Serie (fuer die Buy-&-Hold-Kurve, gleicher Index).
    outfile: Zielpfad der PNG-Datei.
    dark:    Dunkles Farbschema verwenden.

    Returns den geschriebenen Dateipfad.
    """
    import matplotlib
    matplotlib.use("Agg")  # kein Display noetig (Server/CLI)
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    c = _DARK if dark else _LIGHT

    # Beide Kurven auf Start = 100 normieren -> direkt vergleichbar.
    strat = result.equity_curve / result.equity_curve.iloc[0] * 100.0
    hold = close / close.iloc[0] * 100.0
    idx = strat.index

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=dpi)
    fig.patch.set_facecolor(c["surface"])
    ax.set_facecolor(c["surface"])

    ax.plot(idx, hold.values, color=c["hold"], linewidth=2.0, label="Buy & Hold")
    ax.plot(idx, strat.values, color=c["strat"], linewidth=2.0, label="Strategie")

    # Startlinie bei 100 als dezente Referenz.
    ax.axhline(100, color=c["muted"], linewidth=0.8, linestyle=(0, (4, 4)), alpha=0.5)

    # Direkte End-Labels (Identitaet nicht nur ueber Farbe).
    for series, color, name in [(strat, c["strat"], "Strategie"),
                                (hold, c["hold"], "Buy & Hold")]:
        ax.annotate(
            f"{name}  {series.iloc[-1]:.0f}",
            xy=(idx[-1], series.iloc[-1]),
            xytext=(6, 0), textcoords="offset points",
            va="center", ha="left", fontsize=9, color=color, fontweight="bold",
        )

    # Achsen / Grid dezent.
    ax.set_title(title, color=c["text"], fontsize=13, fontweight="bold", loc="left", pad=12)
    ax.set_ylabel("Kapital (Start = 100)", color=c["muted"], fontsize=10)
    ax.grid(True, axis="y", color=c["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(c["grid"])
    ax.tick_params(colors=c["muted"], labelsize=9)

    # X-Achse als Datum formatieren, wenn moeglich.
    if hasattr(idx, "to_pydatetime"):
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

    # Kennzahlen-Box unten links.
    stats = (
        f"Strategie {result.total_return_pct:+.1f}%   "
        f"Buy&Hold {result.buy_hold_return_pct:+.1f}%\n"
        f"Sharpe {result.sharpe:.2f}   Max DD {result.max_drawdown_pct:.1f}%   "
        f"investiert {result.exposure_pct:.0f}%"
    )
    ax.text(0.012, 0.03, stats, transform=ax.transAxes, fontsize=8.5,
            color=c["muted"], va="bottom", ha="left")

    # Rechten Rand fuer die End-Labels freihalten.
    ax.margins(x=0.02)
    fig.subplots_adjust(left=0.08, right=0.86, top=0.90, bottom=0.10)

    fig.savefig(outfile, facecolor=c["surface"])
    plt.close(fig)
    return outfile
