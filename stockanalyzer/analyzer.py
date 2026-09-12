"""Orchestrierung: Daten holen, Signale + Fundamentaldaten kombinieren, Report bauen."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from . import data as data_mod
from . import fundamentals as fund_mod
from . import indicators as ind
from . import options as opt_mod
from . import signals as sig_mod


@dataclass
class OptionIdea:
    """Ein konkreter Options-Vorschlag mit Kennzahlen und Begruendung."""

    option_type: str          # "call" oder "put"
    strike: float
    expiry: str
    dte: int                  # Tage bis Verfall
    fair_price: float
    implied_vol: float
    delta: float
    theta: float
    vega: float
    rationale: str
    risk_note: str


@dataclass
class StockReport:
    ticker: str
    name: str
    currency: str
    last_price: float
    technical: sig_mod.TechnicalScore
    fundamental: fund_mod.FundamentalScore
    combined_score: float
    recommendation: str
    option_ideas: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class Analyzer:
    """Fuehrt die komplette Analyse fuer einen Ticker aus."""

    def __init__(self, period: str = "1y", risk_free_rate: float = 0.03,
                 fundamental_weight: float = 0.4):
        self.period = period
        self.risk_free_rate = risk_free_rate
        # Gewichtung Technik vs. Fundamental beim Gesamt-Score.
        self.fundamental_weight = max(0.0, min(1.0, fundamental_weight))

    def analyze(self, ticker: str, with_options: bool = False) -> StockReport:
        md = data_mod.fetch(ticker, period=self.period)

        technical = sig_mod.analyze(md.history)
        fundamental = fund_mod.analyze(md.info)

        # Wenn kaum Fundamentaldaten vorhanden sind, Technik staerker gewichten.
        fw = self.fundamental_weight
        if not fundamental.points:
            fw = 0.0
        combined = (1 - fw) * technical.score + fw * fundamental.score

        warnings: list = []
        vol = technical.metrics.get("Volatilitaet p.a. %")
        if isinstance(vol, float) and vol == vol and vol > 60:
            warnings.append(f"Sehr hohe Volatilitaet ({vol:.0f}% p.a.) - erhoehtes Risiko.")
        if not fundamental.points:
            warnings.append("Keine Fundamentaldaten verfuegbar - Bewertung rein technisch.")

        report = StockReport(
            ticker=md.ticker,
            name=md.name,
            currency=md.currency,
            last_price=md.last_price,
            technical=technical,
            fundamental=fundamental,
            combined_score=round(combined, 1),
            recommendation=sig_mod.recommendation_label(combined),
            warnings=warnings,
        )

        if with_options:
            try:
                report.option_ideas = self._option_ideas(md, technical.score)
            except data_mod.DataError as exc:
                report.warnings.append(f"Optionsanalyse uebersprungen: {exc}")

        return report

    def _option_ideas(self, md: data_mod.MarketData, tech_score: float) -> list:
        """Leitet aus der Marktrichtung passende Call/Put-Ideen ab.

        Grundprinzip:
        * bullischer Score  -> Long Call (setzt auf steigende Kurse)
        * baerischer Score  -> Long Put  (setzt auf fallende Kurse / Absicherung)
        Ausgewaehlt werden liquide Strikes nahe am Geld (ATM/leicht OTM).
        """
        expiry, calls, puts, _expiries = data_mod.fetch_option_chain(md.ticker)
        S = md.last_price
        import datetime as dt

        exp_date = dt.datetime.strptime(expiry, "%Y-%m-%d").date()
        dte = max(1, (exp_date - dt.date.today()).days)
        T = dte / 365.0
        r = self.risk_free_rate
        q = 0.0

        bullish = tech_score >= 50
        chain = calls if bullish else puts
        option_type = "call" if bullish else "put"

        if chain is None or chain.empty:
            return []

        # Strikes nahe am Geld waehlen (leicht OTM in Trendrichtung).
        chain = chain.dropna(subset=["strike"]).copy()
        if bullish:
            target = S * 1.03   # 3% OTM Call
        else:
            target = S * 0.97   # 3% OTM Put
        chain["dist"] = (chain["strike"] - target).abs()
        chain = chain.sort_values("dist").head(3).sort_values("strike")

        ideas: list = []
        for _, row in chain.iterrows():
            K = float(row["strike"])
            market_price = row.get("lastPrice")
            if not isinstance(market_price, (int, float)) or market_price != market_price or market_price <= 0:
                # Fallback: Mittel aus Bid/Ask
                bid, ask = row.get("bid", 0) or 0, row.get("ask", 0) or 0
                market_price = (bid + ask) / 2 if (bid or ask) else None

            iv = row.get("impliedVolatility")
            if not isinstance(iv, (int, float)) or iv != iv or iv <= 0:
                if market_price:
                    iv = opt_mod.implied_volatility(market_price, S, K, T, r, option_type, q)
                else:
                    iv = ind.annualized_volatility(md.history["Close"], 30)
            iv = float(iv) if iv == iv else 0.3

            fair = opt_mod.black_scholes(S, K, T, r, iv, option_type, q)
            g = opt_mod.greeks(S, K, T, r, iv, option_type, q)

            rationale = (
                f"{'Bullisches' if bullish else 'Baerisches'} technisches Bild "
                f"(Score {tech_score:.0f}/100). {option_type.upper()} ~3% aus dem Geld."
            )
            risk = (
                f"Max. Verlust = gezahlte Praemie. Zeitwertverfall Theta {g.theta:.3f}/Tag. "
                f"IV {iv*100:.0f}% - bei hoher IV sind Optionen teuer."
            )
            ideas.append(
                OptionIdea(
                    option_type=option_type,
                    strike=K,
                    expiry=expiry,
                    dte=dte,
                    fair_price=round(fair, 2),
                    implied_vol=round(iv * 100, 1),
                    delta=round(g.delta, 3),
                    theta=round(g.theta, 3),
                    vega=round(g.vega, 3),
                    rationale=rationale,
                    risk_note=risk,
                )
            )
        return ideas

    def rank(self, tickers, with_options: bool = False):
        """Analysiert mehrere Ticker und sortiert nach kombiniertem Score (absteigend)."""
        reports = []
        for tk in tickers:
            try:
                reports.append(self.analyze(tk, with_options=with_options))
            except data_mod.DataError as exc:
                reports.append(exc)
        ok = [r for r in reports if isinstance(r, StockReport)]
        errors = [(tk, r) for tk, r in zip(tickers, reports) if not isinstance(r, StockReport)]
        ok.sort(key=lambda r: r.combined_score, reverse=True)
        return ok, errors
