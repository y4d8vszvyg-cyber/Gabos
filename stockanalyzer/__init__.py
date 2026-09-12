"""stockanalyzer - Aktien- und Optionsanalyse mit datenbasierten Signalen.

WICHTIG / DISCLAIMER
--------------------
Dieses Programm ist ein Werkzeug zur *Analyse* und *Bildung*. Es ist KEINE
Anlageberatung und kann Kursentwicklungen nicht vorhersagen. Kein Modell
garantiert Gewinne. An der Börse (und besonders bei Optionen) kannst du dein
gesamtes eingesetztes Kapital verlieren. Triff keine Anlageentscheidung allein
auf Basis dieser Ausgaben. Nutze die Ergebnisse als eine von vielen
Informationsquellen und ziehe im Zweifel eine lizenzierte Beratung hinzu.
"""

__version__ = "0.1.0"

from .analyzer import Analyzer, StockReport
from .options import black_scholes, greeks, implied_volatility

__all__ = [
    "Analyzer",
    "StockReport",
    "black_scholes",
    "greeks",
    "implied_volatility",
    "__version__",
]
