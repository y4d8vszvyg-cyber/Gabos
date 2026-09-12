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
from . import backtest as bt_mod
from . import portfolio as pf_mod
from . import watchlist as wl_mod
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


def _print_backtest(result: bt_mod.BacktestResult) -> None:
    print("\n  Backtest (Long/Flat-Trendfolge vs. Buy & Hold):")
    rows = [
        ["Strategie-Rendite", f"{result.total_return_pct:+.1f} %"],
        ["Buy & Hold", f"{result.buy_hold_return_pct:+.1f} %"],
        ["Rendite p.a.", f"{result.annual_return_pct:+.1f} %"],
        ["Volatilitaet p.a.", f"{result.annual_volatility_pct:.1f} %"],
        ["Sharpe-Ratio", f"{result.sharpe:.2f}"],
        ["Max Drawdown", f"{result.max_drawdown_pct:.1f} %"],
        ["Trefferquote (Tage)", f"{result.win_rate_pct:.1f} %"],
        ["Positionswechsel", f"{result.num_trades}"],
        ["Investiert (Zeit)", f"{result.exposure_pct:.1f} %"],
    ]
    print(tabulate(rows, tablefmt="simple", colalign=("left", "right")))
    print("    Hinweis: Historische Ergebnisse sind KEINE Garantie fuer die Zukunft.")


def _print_position(plan: pf_mod.PositionPlan, ticker: str, cur: str) -> None:
    print("\n  Positionsgroesse (risikobasiert):")
    rows = [
        ["Stueckzahl", f"{plan.shares}"],
        ["Kapitaleinsatz", f"{plan.position_value:.2f} {cur} ({plan.position_pct:.1f}% Depot)"],
        ["Stop-Loss", f"{plan.stop_price:.2f} {cur}"],
        ["Risiko je Aktie", f"{plan.risk_per_share:.2f} {cur}"],
        ["Max. Verlust bis Stop", f"{plan.risk_amount:.2f} {cur}"],
    ]
    if plan.reward_to_risk is not None:
        rows.append(["Chance/Risiko (CRV)", f"{plan.reward_to_risk:.2f} : 1"])
    print(tabulate(rows, tablefmt="simple", colalign=("left", "right")))
    print(f"    {plan.note}")


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
    p.add_argument("tickers", nargs="*", help="Ein oder mehrere Symbole, z.B. AAPL MSFT SAP.DE")
    p.add_argument("--watchlist", metavar="DATEI",
                   help="Ticker aus einer Textdatei laden (ein Symbol pro Zeile)")
    p.add_argument("--period", default="1y",
                   help="Zeitraum der Historie (6mo, 1y, 2y, 5y, max). Standard: 1y")
    p.add_argument("--rank", action="store_true",
                   help="Mehrere Ticker analysieren und als Ranking ausgeben")
    p.add_argument("--options", action="store_true",
                   help="Zusaetzlich Call/Put-Optionsideen berechnen")
    p.add_argument("--backtest", action="store_true",
                   help="Historischen Backtest der Trendfolge-Strategie ausgeben")
    p.add_argument("--fundamental-weight", type=float, default=0.4,
                   help="Gewicht der Fundamentaldaten (0..1). Standard: 0.4")
    p.add_argument("--risk-free-rate", type=float, default=0.03,
                   help="Risikofreier Zins p.a. fuer die Optionsbewertung. Standard: 0.03")
    # Positionsgroessen-Rechner
    p.add_argument("--capital", type=float,
                   help="Depotkapital -> berechnet eine risikobasierte Positionsgroesse")
    p.add_argument("--risk-per-trade", type=float, default=1.0,
                   help="Anteil des Depots, der je Trade riskiert wird (%%). Standard: 1.0")
    p.add_argument("--atr-multiple", type=float, default=2.0,
                   help="Stop-Abstand als Vielfaches der ATR. Standard: 2.0")
    p.add_argument("--max-position", type=float, default=20.0,
                   help="Obergrenze je Position (%% des Depots). Standard: 20")
    p.add_argument("--version", action="version", version=f"stockanalyzer {__version__}")
    return p


def _collect_tickers(args) -> list:
    """Fuehrt Ticker aus Argumenten und Watchlist-Datei zusammen."""
    tickers = list(args.tickers)
    if args.watchlist:
        tickers = wl_mod.load(args.watchlist) + tickers
    # Duplikate entfernen, Reihenfolge bewahren.
    seen, unique = set(), []
    for tk in tickers:
        up = tk.upper()
        if up not in seen:
            seen.add(up)
            unique.append(up)
    return unique


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    analyzer = Analyzer(
        period=args.period,
        risk_free_rate=args.risk_free_rate,
        fundamental_weight=args.fundamental_weight,
    )

    print(DISCLAIMER)

    try:
        tickers = _collect_tickers(args)
    except FileNotFoundError as exc:
        print(f"\n[Fehler] {exc}", file=sys.stderr)
        return 1

    if not tickers:
        print("\n[Fehler] Keine Ticker angegeben. Beispiel: 'AAPL' oder '--watchlist datei.txt'.",
              file=sys.stderr)
        return 1

    if args.rank and len(tickers) > 1:
        reports, errors = analyzer.rank(tickers, with_options=args.options)
        if reports:
            _print_ranking(reports)
        for tk, err in errors:
            print(f"  [Fehler] {tk}: {err}", file=sys.stderr)
        return 0 if reports else 1

    exit_code = 0
    for ticker in tickers:
        try:
            md = analyzer.fetch(ticker)
            report = analyzer.analyze_market_data(md, with_options=args.options)
            _print_report(report)

            if args.backtest:
                _print_backtest(bt_mod.run(md.history, risk_free_rate=args.risk_free_rate))

            if args.capital:
                from .indicators import atr as atr_fn
                atr_val = float(atr_fn(md.history, 14).dropna().iloc[-1])
                try:
                    plan = pf_mod.position_size(
                        capital=args.capital,
                        entry_price=report.last_price,
                        atr=atr_val,
                        risk_per_trade_pct=args.risk_per_trade,
                        atr_multiple=args.atr_multiple,
                        max_position_pct=args.max_position,
                    )
                    _print_position(plan, ticker, report.currency)
                except ValueError as exc:
                    print(f"\n  [Positionsgroesse uebersprungen] {exc}", file=sys.stderr)
        except DataError as exc:
            print(f"\n[Fehler] {ticker}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
