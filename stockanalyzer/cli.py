"""Kommandozeilen-Oberflaeche fuer den Aktien-Analyzer.

Beispiele
---------
    python -m stockanalyzer AAPL
    python -m stockanalyzer AAPL MSFT NVDA --rank
    python -m stockanalyzer TSLA --options
    python -m stockanalyzer SAP.DE --period 2y
"""

from __future__ import annotations

import argparse
import sys

from tabulate import tabulate

from . import __version__
from .analyzer import Analyzer, StockReport
from .data import DataError

DISCLAIMER = (
    "HINWEIS: Keine Anlageberatung. Analysewerkzeug zu Bildungszwecken. "
    "Kursprognosen sind unmoeglich, Verluste (inkl. Totalverlust bei Optionen) "
    "sind moeglich. Entscheide nie allein auf Basis dieser Ausgabe."
)


def _fmt(val, digits=2, suffix=""):
    if val is None:
        return "-"
    if isinstance(val, float) and val != val:  # NaN
        return "-"
    if isinstance(val, (int, float)):
        return f"{val:.{digits}f}{suffix}"
    return str(val)


def _print_report(report: StockReport) -> None:
    cur = report.currency
    print("\n" + "=" * 68)
    print(f"  {report.name}  ({report.ticker})")
    print("=" * 68)
    print(f"  Aktueller Kurs : {report.last_price:.2f} {cur}")
    print(f"  Technik-Score  : {report.technical.score:.1f} / 100")
    print(f"  Fundamental    : {report.fundamental.score:.1f} / 100")
    print(f"  GESAMT-SCORE   : {report.combined_score:.1f} / 100")
    print(f"  EMPFEHLUNG     : {report.recommendation}")

    print("\n  Technische Signale:")
    for name, contrib, reason in report.technical.signals:
        arrow = "+" if contrib > 0 else "-" if contrib < 0 else " "
        print(f"    [{arrow}] {name:<20} {reason}")

    if report.fundamental.points:
        print("\n  Fundamentale Punkte:")
        for name, value, contrib, reason in report.fundamental.points:
            arrow = "+" if contrib > 0 else "-"
            print(f"    [{arrow}] {name:<20} {reason}")

    # Kennzahlen-Tabelle
    metrics = dict(report.technical.metrics)
    rows = []
    for key in ["RSI(14)", "SMA50", "SMA200", "MACD", "Bollinger %B",
                "Perf. 1M %", "Perf. 3M %", "Volatilitaet p.a. %",
                "Max Drawdown %", "ATR(14)"]:
        if key in metrics:
            rows.append([key, _fmt(metrics[key])])
    if rows:
        print("\n  Kennzahlen:")
        print(tabulate(rows, tablefmt="simple", colalign=("left", "right")))

    if report.option_ideas:
        print("\n  Options-Ideen (aus Marktrichtung abgeleitet):")
        opt_rows = []
        for idea in report.option_ideas:
            opt_rows.append([
                idea.option_type.upper(),
                f"{idea.strike:.2f}",
                idea.expiry,
                f"{idea.dte}d",
                f"{idea.fair_price:.2f}",
                f"{idea.implied_vol:.0f}%",
                f"{idea.delta:.2f}",
                f"{idea.theta:.3f}",
            ])
        print(tabulate(
            opt_rows,
            headers=["Typ", "Strike", "Verfall", "DTE", "Fair", "IV", "Delta", "Theta/Tag"],
            tablefmt="simple",
        ))
        print(f"\n    Strategie: {report.option_ideas[0].rationale}")
        print(f"    Risiko   : {report.option_ideas[0].risk_note}")

    if report.warnings:
        print("\n  Warnungen:")
        for w in report.warnings:
            print(f"    ! {w}")


def _print_ranking(reports) -> None:
    print("\n" + "=" * 68)
    print("  RANKING (nach Gesamt-Score)")
    print("=" * 68)
    rows = []
    for i, r in enumerate(reports, 1):
        rows.append([
            i,
            r.ticker,
            f"{r.last_price:.2f} {r.currency}",
            f"{r.technical.score:.0f}",
            f"{r.fundamental.score:.0f}",
            f"{r.combined_score:.1f}",
            r.recommendation,
        ])
    print(tabulate(
        rows,
        headers=["#", "Ticker", "Kurs", "Tech", "Fund", "Gesamt", "Empfehlung"],
        tablefmt="simple",
    ))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stockanalyzer",
        description="Analysiert Aktien und Optionen und leitet datenbasierte Signale ab.",
        epilog=DISCLAIMER,
    )
    p.add_argument("tickers", nargs="+", help="Ein oder mehrere Symbole, z.B. AAPL MSFT SAP.DE")
    p.add_argument("--period", default="1y",
                   help="Zeitraum der Historie (6mo, 1y, 2y, 5y, max). Standard: 1y")
    p.add_argument("--rank", action="store_true",
                   help="Mehrere Ticker analysieren und als Ranking ausgeben")
    p.add_argument("--options", action="store_true",
                   help="Zusaetzlich Call/Put-Optionsideen berechnen")
    p.add_argument("--fundamental-weight", type=float, default=0.4,
                   help="Gewicht der Fundamentaldaten (0..1). Standard: 0.4")
    p.add_argument("--risk-free-rate", type=float, default=0.03,
                   help="Risikofreier Zins p.a. fuer die Optionsbewertung. Standard: 0.03")
    p.add_argument("--version", action="version", version=f"stockanalyzer {__version__}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    analyzer = Analyzer(
        period=args.period,
        risk_free_rate=args.risk_free_rate,
        fundamental_weight=args.fundamental_weight,
    )

    print(DISCLAIMER)

    if args.rank and len(args.tickers) > 1:
        reports, errors = analyzer.rank(args.tickers, with_options=args.options)
        if reports:
            _print_ranking(reports)
        for tk, err in errors:
            print(f"  [Fehler] {tk}: {err}", file=sys.stderr)
        return 0 if reports else 1

    exit_code = 0
    for ticker in args.tickers:
        try:
            report = analyzer.analyze(ticker, with_options=args.options)
            _print_report(report)
        except DataError as exc:
            print(f"\n[Fehler] {ticker}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
