# stockanalyzer

Ein Kommandozeilen-Werkzeug, das **Aktienkurse und Optionen analysiert** und
daraus **transparente, datenbasierte Signale** ableitet (Kaufen / Halten /
Verkaufen) – inklusive Bewertung von **Call- und Put-Optionen** per
Black-Scholes-Modell mit allen wichtigen Greeks.

> ⚠️ **WICHTIGER HINWEIS – bitte lesen**
>
> Dies ist ein **Analyse- und Bildungswerkzeug, KEINE Anlageberatung.**
> Niemand – kein Mensch und kein Programm – kann Börsenkurse zuverlässig
> vorhersagen. Dieses Tool garantiert **keine Gewinne**. An der Börse und
> besonders bei Optionen kannst du dein **gesamtes eingesetztes Kapital
> verlieren** (bei Optionen droht Totalverlust der Prämie). Nutze die
> Ausgaben als *eine von mehreren* Informationsquellen und triff keine
> Anlageentscheidung allein auf ihrer Basis. Im Zweifel: lizenzierte
> Beratung hinzuziehen.

## Was das Programm macht

1. **Kursdaten holen** (via Yahoo Finance / `yfinance`) – Historie beliebiger
   Aktien, ETFs, Indizes (auch deutsche, z. B. `SAP.DE`).
2. **Technische Analyse** – Trend (SMA50/SMA200, Golden/Death Cross),
   Momentum (RSI, MACD), Bollinger-Bänder, Performance über mehrere
   Zeitfenster, Volatilität, Max Drawdown, ATR.
3. **Fundamentale Analyse** – KGV, PEG, Nettomarge, Eigenkapitalrendite,
   Verschuldung, Umsatzwachstum, Dividende.
4. **Gesamt-Score & Empfehlung** – jede Regel liefert einen nachvollziehbaren
   Beitrag mit Begründung; die Summe wird auf 0–100 skaliert und in ein Label
   übersetzt (STARK KAUFEN … VERKAUFEN). **Keine Black-Box.**
5. **Optionsanalyse** – Black-Scholes-Preis, implizite Volatilität und Greeks
   (Delta, Gamma, Theta, Vega, Rho). Aus der Marktrichtung wird eine passende
   Call- (bullisch) oder Put-Idee (bärisch) abgeleitet, inkl. Risikohinweis.

## Installation

```bash
pip install -r requirements.txt
```

Python ≥ 3.9.

## Nutzung

```bash
# Eine Aktie analysieren
python -m stockanalyzer AAPL

# Mehrere Aktien vergleichen und als Ranking ausgeben
python -m stockanalyzer AAPL MSFT NVDA GOOGL --rank

# Mit Optionsideen (Call/Put)
python -m stockanalyzer TSLA --options

# Deutsche Aktie, längerer Zeitraum
python -m stockanalyzer SAP.DE --period 2y

# Fundamentaldaten stärker gewichten
python -m stockanalyzer KO --fundamental-weight 0.6
```

### Optionen (CLI-Flags)

| Flag                   | Bedeutung                                             | Standard |
|------------------------|-------------------------------------------------------|----------|
| `--period`             | Zeitraum der Historie (`6mo`,`1y`,`2y`,`5y`,`max`)    | `1y`     |
| `--rank`               | Mehrere Ticker als sortiertes Ranking                 | aus      |
| `--options`            | Zusätzlich Call/Put-Optionsideen                      | aus      |
| `--fundamental-weight` | Gewicht Fundamentaldaten im Gesamt-Score (`0`–`1`)    | `0.4`    |
| `--risk-free-rate`     | Risikofreier Zins p. a. für die Optionsbewertung      | `0.03`   |

## Offline-Demo (ohne Internet)

Wenn kein Netzzugriff besteht, zeigt die Demo die komplette Ausgabe mit
synthetischen Daten:

```bash
python examples/demo_offline.py
```

## Als Bibliothek verwenden

```python
from stockanalyzer import Analyzer, black_scholes, greeks

report = Analyzer(period="1y").analyze("AAPL", with_options=True)
print(report.recommendation, report.combined_score)

# Einzelne Option fair bewerten (S, K, T[Jahre], r, sigma)
preis = black_scholes(S=190, K=200, T=30/365, r=0.03, sigma=0.28, option_type="call")
g = greeks(S=190, K=200, T=30/365, r=0.03, sigma=0.28, option_type="call")
print(preis, g.delta, g.theta)
```

## Tests

```bash
pip install pytest
python -m pytest tests/ -q
```

Die Tests prüfen die Mathematik netzunabhängig (u. a. Put-Call-Parität,
Black-Scholes-Referenzwert, RSI-Grenzen, implizite Vola per Roundtrip).

## Hinweis zum Datenzugriff

`yfinance` benötigt Zugriff auf Yahoo-Finance-Hosts
(`query1/query2.finance.yahoo.com`). In abgeschotteten Umgebungen (z. B. hinter
einer restriktiven Proxy-Policy) kann das blockiert sein; das Programm meldet
das dann mit einer klaren Fehlermeldung. Führe es in dem Fall lokal aus oder
erlaube die Yahoo-Hosts in der Netzwerk-Policy.

## Wie du damit vernünftig umgehst

- **Diversifikation** schlägt Einzelwetten. Ein hoher Score ist kein
  Freifahrtschein.
- **Optionen sind Hebelprodukte.** Der Zeitwert (Theta) arbeitet gegen
  Käufer; hohe implizite Volatilität macht Optionen teuer.
- **Backtesting ≠ Zukunft.** Vergangene Signale garantieren nichts.
- Setze nur Kapital ein, dessen Verlust du verkraften kannst.
