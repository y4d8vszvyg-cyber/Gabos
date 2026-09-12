"""Fertiges Startskript fuer die iPad-App 'Pyto' (und aehnliche Python-Apps).

So benutzt du es:
  1. Lege den ganzen Projektordner 'Gabos' in Pyto ab (siehe ANLEITUNG.md).
  2. Oeffne diese Datei in Pyto und druecke oben rechts auf ▶ (Run).
  3. Aendere unten bei SYMBOL das Kuerzel, um eine andere Aktie zu pruefen.

WICHTIG: In Pyto laesst sich 'yfinance' (Yahoo) meist NICHT installieren, weil
es eine kompilierte Komponente braucht. Deshalb nutzt dieses Skript die
Datenquelle 'stooq' - die braucht nur 'pandas' (in Pyto vorhanden) und liefert
echte Boersen-Tageskurse (US, DE, Indizes, Forex, Krypto). Hinweis: ueber Stooq
gibt es keine Optionsketten und keine Fundamentaldaten - dafuer brauchst du
Yahoo (z. B. am PC oder in Google Colab).
"""

import os
import sys

# ---- Damit Pyto das Paket 'stockanalyzer' findet (liegt im Ordner darueber) ----
HIER = os.path.dirname(os.path.abspath(__file__))
PROJEKT = os.path.dirname(HIER)
if PROJEKT not in sys.path:
    sys.path.insert(0, PROJEKT)

from stockanalyzer.analyzer import Analyzer
from stockanalyzer import backtest, report
from stockanalyzer.data import DataError

# ============================================================
#   HIER anpassen: welches Symbol willst du analysieren?
#   US-Aktien: reines Kuerzel (AAPL, MSFT, NVDA)
#   Deutsche Aktien: mit Suffix .DE (SAP.DE, BMW.DE)
#   Indizes: ^SPX (S&P 500), ^DJI (Dow Jones)
# ============================================================
SYMBOL = "AAPL"
ZEITRAUM = "1y"            # "6mo", "1y", "2y", "5y", "max"
REPORT_SPEICHERN = True    # True = interaktive report.html erzeugen
# ============================================================


def main():
    print("=" * 52)
    print(f"  Analyse: {SYMBOL}  (Datenquelle: Stooq, Live-Daten)")
    print("=" * 52)

    analyzer = Analyzer(period=ZEITRAUM, source="stooq")
    try:
        md = analyzer.fetch(SYMBOL)
    except DataError as exc:
        print("\n[Fehler beim Laden]", exc)
        print("Tipp: Symbol pruefen. US = reines Kuerzel, dt. Aktie = '.DE'.")
        return

    rep = analyzer.analyze_market_data(md)

    print(f"\n  Name          : {rep.name}")
    print(f"  Letzter Kurs  : {rep.last_price:.2f} {rep.currency}")
    print(f"  Technik-Score : {rep.technical.score:.1f} / 100")
    print(f"  GESAMT-SCORE  : {rep.combined_score:.1f} / 100")
    print(f"  EMPFEHLUNG    : {rep.recommendation}")

    print("\n  Technische Signale:")
    for name, contrib, reason in rep.technical.signals:
        zeichen = "+" if contrib > 0 else "-" if contrib < 0 else " "
        print(f"    [{zeichen}] {name}: {reason}")

    # Kurzer Backtest (Trendfolge vs. Buy & Hold).
    res = backtest.run(md.history)
    print("\n  Backtest (Trendfolge vs. Buy & Hold):")
    print(f"    Strategie {res.total_return_pct:+.1f}%   "
          f"Buy&Hold {res.buy_hold_return_pct:+.1f}%   Sharpe {res.sharpe:.2f}")

    if REPORT_SPEICHERN:
        try:
            comp = None
            try:
                from stockanalyzer import multistrategy
                comp = multistrategy.compare(md.history)
            except Exception:  # noqa: BLE001 - Vergleich ist optional
                comp = None
            pfad = os.path.join(PROJEKT, "report.html")
            report.write_html(pfad, res, md.history["Close"], report=rep, comparison=comp,
                              title=f"{rep.name} - Report")
            print(f"\n  Interaktiver Report gespeichert: {pfad}")
            print("  -> In Pyto ueber die Datei-Ansicht teilen/oeffnen,")
            print("     oder in der Dateien-App im Browser oeffnen.")
        except Exception as exc:  # noqa: BLE001
            print(f"\n  (Report uebersprungen: {exc})")

    print("\n  Hinweis: Keine Anlageberatung. Keine Gewinngarantie.")


if __name__ == "__main__":
    main()
