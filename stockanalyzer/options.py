"""Optionsbewertung: Black-Scholes-Preis, Greeks und implizite Volatilitaet.

Konventionen
------------
* ``S``     aktueller Kurs des Basiswerts
* ``K``     Ausuebungspreis (Strike)
* ``T``     Restlaufzeit in Jahren (z.B. 30 Tage = 30/365)
* ``r``     risikofreier Zins p.a. (dezimal, z.B. 0.03)
* ``sigma`` Volatilitaet p.a. (dezimal, z.B. 0.25 = 25%)
* ``q``     Dividendenrendite p.a. (dezimal), Standard 0
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import norm


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float, q: float):
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        raise ValueError("S, K, T und sigma muessen > 0 sein.")
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2


def black_scholes(S: float, K: float, T: float, r: float, sigma: float,
                  option_type: str = "call", q: float = 0.0) -> float:
    """Fairer Preis einer europaeischen Option nach Black-Scholes-Merton."""
    option_type = option_type.lower()
    if T <= 0:
        # Bei Verfall ist der Wert der innere Wert.
        if option_type == "call":
            return max(0.0, S - K)
        return max(0.0, K - S)

    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    disc_r = math.exp(-r * T)
    disc_q = math.exp(-q * T)

    if option_type == "call":
        return S * disc_q * norm.cdf(d1) - K * disc_r * norm.cdf(d2)
    if option_type == "put":
        return K * disc_r * norm.cdf(-d2) - S * disc_q * norm.cdf(-d1)
    raise ValueError("option_type muss 'call' oder 'put' sein.")


@dataclass
class Greeks:
    """Sensitivitaeten des Optionspreises."""

    delta: float   # d Preis / d Kurs
    gamma: float   # d Delta / d Kurs
    theta: float   # d Preis / d Zeit (pro Tag)
    vega: float    # d Preis / d Vol (pro 1 Prozentpunkt)
    rho: float     # d Preis / d Zins (pro 1 Prozentpunkt)


def greeks(S: float, K: float, T: float, r: float, sigma: float,
           option_type: str = "call", q: float = 0.0) -> Greeks:
    """Berechnet die wichtigsten Greeks (Theta/Vega/Rho in praxisnahen Einheiten)."""
    option_type = option_type.lower()
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    disc_r = math.exp(-r * T)
    disc_q = math.exp(-q * T)
    pdf_d1 = norm.pdf(d1)
    sqrt_t = math.sqrt(T)

    gamma = disc_q * pdf_d1 / (S * sigma * sqrt_t)
    vega = S * disc_q * pdf_d1 * sqrt_t / 100.0  # pro 1 Prozentpunkt Vol

    if option_type == "call":
        delta = disc_q * norm.cdf(d1)
        theta = (
            -S * disc_q * pdf_d1 * sigma / (2 * sqrt_t)
            - r * K * disc_r * norm.cdf(d2)
            + q * S * disc_q * norm.cdf(d1)
        ) / 365.0
        rho = K * T * disc_r * norm.cdf(d2) / 100.0
    elif option_type == "put":
        delta = -disc_q * norm.cdf(-d1)
        theta = (
            -S * disc_q * pdf_d1 * sigma / (2 * sqrt_t)
            + r * K * disc_r * norm.cdf(-d2)
            - q * S * disc_q * norm.cdf(-d1)
        ) / 365.0
        rho = -K * T * disc_r * norm.cdf(-d2) / 100.0
    else:
        raise ValueError("option_type muss 'call' oder 'put' sein.")

    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)


def implied_volatility(price: float, S: float, K: float, T: float, r: float,
                       option_type: str = "call", q: float = 0.0,
                       tol: float = 1e-6, max_iter: int = 100) -> float:
    """Loest die implizite Volatilitaet aus einem Marktpreis (Bisektion).

    Gibt ``nan`` zurueck, wenn kein Wert im Bereich [0.1%, 1000%] passt
    (z.B. Preis unter innerem Wert).
    """
    option_type = option_type.lower()
    if price <= 0 or T <= 0:
        return float("nan")

    intrinsic = max(0.0, S - K) if option_type == "call" else max(0.0, K - S)
    if price < intrinsic - tol:
        return float("nan")

    low, high = 1e-3, 10.0
    price_low = black_scholes(S, K, T, r, low, option_type, q)
    price_high = black_scholes(S, K, T, r, high, option_type, q)
    if not (price_low <= price <= price_high):
        return float("nan")

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        val = black_scholes(S, K, T, r, mid, option_type, q)
        if abs(val - price) < tol:
            return mid
        if val < price:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)
