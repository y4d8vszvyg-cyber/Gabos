# Schritt-für-Schritt-Anleitung: lokal starten (mit Live-Daten)

Diese Anleitung ist für **Einsteiger** gedacht. Sie bringt das Programm auf
deinem eigenen Rechner zum Laufen – dort gibt es **keine Netzsperre**, also
bekommst du **echte, aktuelle Kursdaten**. Plane ca. **10–15 Minuten** ein.

> ⚠️ **Zur Erinnerung:** Das Programm ist ein Analyse- und Bildungswerkzeug,
> **keine Anlageberatung**. Es kann Kurse nicht vorhersagen und garantiert keine
> Gewinne. Setze nur Geld ein, dessen Verlust du verkraften kannst.

---

## Überblick – was du tun wirst

1. Python installieren (einmalig)
2. Das Projekt herunterladen
3. Ein Terminal im Projektordner öffnen
4. Eine „virtuelle Umgebung" anlegen (empfohlen, sauberer)
5. Die Bausteine (Bibliotheken) installieren
6. Die erste Analyse mit echten Daten starten
7. Den interaktiven Report erzeugen und im Browser öffnen

Wenn etwas klemmt: unten gibt es einen Abschnitt **„Häufige Probleme"**.

---

## Schritt 1 – Python installieren

Das Programm braucht **Python 3.9 oder neuer**. Prüfe zuerst, ob es schon da ist:

- **Windows:** Drücke `Windows-Taste`, tippe `cmd`, öffne die „Eingabeaufforderung"
  und gib ein:
  ```
  python --version
  ```
- **macOS/Linux:** Öffne das „Terminal" und gib ein:
  ```
  python3 --version
  ```

Erscheint z. B. `Python 3.11.5`, ist alles gut → **weiter zu Schritt 2**.
Erscheint ein Fehler oder eine Version unter 3.9, installiere Python:

### Windows
1. Gehe auf **https://www.python.org/downloads/** und lade Python herunter.
2. Starte den Installer. **Ganz wichtig:** unten das Häkchen bei
   **„Add python.exe to PATH"** setzen, *bevor* du auf „Install Now" klickst.
3. Nach der Installation die Eingabeaufforderung **neu öffnen** und
   `python --version` erneut prüfen.

### macOS
- Einfachster Weg: Installer von **https://www.python.org/downloads/** laden und
  ausführen. Danach im Terminal `python3 --version` prüfen.
- (Alternativ mit Homebrew: `brew install python`.)

### Linux
- Meist schon vorhanden. Sonst z. B. bei Ubuntu/Debian:
  ```
  sudo apt update && sudo apt install python3 python3-pip python3-venv
  ```

---

## Schritt 2 – Das Projekt herunterladen

Du hast zwei Möglichkeiten:

### Variante A: Als ZIP (am einfachsten, ohne Zusatzsoftware)
1. Öffne die Projektseite auf GitHub im Browser.
2. Klicke auf den grünen Button **„Code" → „Download ZIP"**.
3. Entpacke die ZIP-Datei, z. B. nach `Dokumente\Gabos`.

### Variante B: Mit Git (wenn du Git hast)
```
git clone https://github.com/y4d8vszvyg-cyber/Gabos.git
cd Gabos
```

---

## Schritt 3 – Terminal im Projektordner öffnen

Du musst im **Projektordner** sein (dort liegt die Datei `requirements.txt`).

- **Windows:** Öffne den Ordner im Explorer, klicke oben in die Adresszeile,
  tippe `cmd` und drücke Enter. Es öffnet sich ein Terminal genau in diesem Ordner.
- **macOS:** Rechtsklick auf den Ordner → „Neuer Terminal-Tab am Ordner"
  (ggf. vorher in den Einstellungen aktivieren), oder `cd` zum Ordner:
  ```
  cd ~/Dokumente/Gabos
  ```
- **Linux:** Rechtsklick im Ordner → „Im Terminal öffnen", oder `cd <pfad>`.

Prüfe mit `dir` (Windows) bzw. `ls` (Mac/Linux), dass du `requirements.txt`
und den Ordner `stockanalyzer` siehst.

---

## Schritt 4 – Virtuelle Umgebung anlegen (empfohlen)

Eine „virtuelle Umgebung" hält die Bibliotheken dieses Projekts getrennt vom
Rest deines Systems. Das ist sauberer und vermeidet Konflikte.

**Windows:**
```
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
```

Danach steht am Zeilenanfang `(.venv)`. Das bedeutet: die Umgebung ist aktiv.
(Zum Beenden später einfach `deactivate` eingeben.)

> Dieser Schritt ist optional. Wenn du ihn überspringst, funktioniert es meist
> auch – ersetze in den nächsten Schritten `python` ggf. durch `python3`.

---

## Schritt 5 – Bibliotheken installieren

```
pip install -r requirements.txt
```

Das lädt einmalig alles Nötige herunter (yfinance, pandas, numpy, scipy,
matplotlib, tabulate). Beim ersten Mal dauert das ein paar Minuten.

> Falls `pip` nicht gefunden wird, probiere `python -m pip install -r requirements.txt`
> (Windows) bzw. `python3 -m pip ...` (Mac/Linux).

---

## Schritt 6 – Die erste Analyse (mit echten, aktuellen Daten)

```
python -m stockanalyzer AAPL
```

Du bekommst für **Apple** (Symbol `AAPL`) den aktuellen Kurs, technische Signale,
Fundamentaldaten, einen Gesamt-Score und eine Empfehlung – auf Basis **echter
Live-Daten** von Yahoo Finance.

Weitere Beispiele:
```
python -m stockanalyzer MSFT NVDA GOOGL --rank      # mehrere vergleichen (Ranking)
python -m stockanalyzer TSLA --options              # inkl. Call/Put-Optionsideen
python -m stockanalyzer SAP.DE --period 2y          # deutsche Aktie, 2 Jahre
```

**Symbol-Hinweis:** US-Aktien nutzen ihr reines Kürzel (`AAPL`, `MSFT`).
Deutsche Aktien brauchen ein Börsen-Suffix, z. B. `SAP.DE`, `BMW.DE`, `BAS.DE`
(`.DE` = Xetra).

---

## Schritt 7 – Den interaktiven Report erzeugen und öffnen

```
python -m stockanalyzer AAPL --report report.html --compare --options
```

Das erzeugt die Datei **`report.html`** im Projektordner. Öffne sie per
**Doppelklick** (oder Rechtsklick → „Öffnen mit" → dein Browser). Du siehst:

- die **Equity-Kurve** (Strategie vs. Buy & Hold) mit **Hover** – fahre mit der
  Maus über den Chart, dann erscheinen Datum und Werte,
- das **Drawdown-Panel** (Verlustphasen),
- den **Strategie-Vergleich** mit Tabelle,
- die technischen Signale und die Empfehlung.

Nur das PNG-Bild (statt HTML) willst du?
```
python -m stockanalyzer AAPL --plot chart.png --backtest
```

---

## Auf dem iPad oder Smartphone

**Kurz gesagt: Ja, es geht – aber anders als am PC.** Ein iPad/iPhone hat kein
normales Terminal. Es gibt zwei realistische Wege:

### Weg 1: In der Cloud (empfohlen, am einfachsten) – Google Colab

Hier läuft alles auf Googles Rechnern, dein iPad ist nur der Bildschirm. **Volle
Leistung, echte Live-Daten, keine Installations-Probleme.** Kostenlos, nur ein
Google-Konto nötig.

1. In **Safari** (oder Chrome) auf **https://colab.research.google.com** gehen und
   mit Google-Konto anmelden.
2. **„+ Neues Notebook"** erstellen.
3. In die erste Zelle das hier eintippen und mit dem ▶-Knopf ausführen
   (Projekt laden + Bibliotheken installieren):
   ```
   !git clone https://github.com/y4d8vszvyg-cyber/Gabos.git
   %cd Gabos
   !pip install -r requirements.txt
   ```
4. In eine **neue Zelle** die Analyse starten (Text-Ausgabe mit Live-Daten):
   ```
   !python -m stockanalyzer AAPL --options
   ```
5. Chart **direkt im Notebook anzeigen** (PNG wird in Colab zuverlässig gerendert):
   ```
   !python -m stockanalyzer AAPL --plot chart.png --backtest
   from IPython.display import Image
   Image("chart.png")
   ```
6. Den **interaktiven** HTML-Report erzeugen und herunterladen (dann im Browser öffnen):
   ```
   !python -m stockanalyzer AAPL --report report.html --compare
   from google.colab import files
   files.download("report.html")
   ```
   > Hinweis: Colab zeigt die interaktive HTML-Datei nicht direkt inline an
   > (Sicherheits-Sandbox). Deshalb herunterladen und öffnen. Der PNG-Chart aus
   > Schritt 5 wird dagegen sofort angezeigt.

### Weg 2: Direkt auf dem iPad mit **Pyto**

Pyto bringt Python inkl. `pandas`, `numpy` und `matplotlib` mit und hat
Internetzugang. **Aber Achtung – die wichtigste Info für Pyto:**

> ⚠️ **`yfinance` (Yahoo) lässt sich in Pyto meist NICHT installieren**, weil es
> eine kompilierte Komponente (`curl_cffi`) braucht, die auf dem iPad nicht
> baubar ist. **Lösung:** Nutze die eingebaute zweite Datenquelle **Stooq** –
> die braucht nur `pandas` (in Pyto vorhanden) und liefert echte
> Börsen-Tageskurse (US, DE, Indizes, Forex, Krypto).
>
> Was über Stooq **nicht** geht: Optionsketten (`--options`) und
> Fundamentaldaten. Dafür brauchst du Yahoo – am einfachsten in **Colab (Weg 1)**
> oder am PC.

**So geht's in Pyto – Schritt für Schritt:**

1. **Code aufs iPad holen:** Auf GitHub den grünen Button **„Code" → „Download
   ZIP"** (in Safari). Die ZIP in der **Dateien-App** entpacken und den Ordner
   `Gabos` nach **„Auf meinem iPad → Pyto"** verschieben.
2. **Pyto öffnen**, links auf den Ordner `Gabos` navigieren und die Datei
   **`examples/pyto_start.py`** öffnen.
3. Oben rechts auf **▶ (Run)** drücken. Es lädt echte Kurse über Stooq und zeigt
   Analyse, Signale und einen Backtest an.
4. **Andere Aktie?** In `pyto_start.py` ganz oben die Zeile
   `SYMBOL = "AAPL"` ändern (z. B. `"SAP.DE"` oder `"NVDA"`) und wieder ▶ drücken.

Das Skript speichert außerdem eine **`report.html`** im Projektordner – die kannst
du in Pyto über das Teilen-Menü bzw. in der Dateien-App im Browser öffnen (dann
mit Hover-Charts).

**Alternative App – a-Shell** (kostenlos, hat ein echtes Terminal):
```
pip install pandas numpy tabulate
python -m stockanalyzer AAPL --source stooq
```

> Für den **vollen** Funktionsumfang (Yahoo-Daten, Optionen, Fundamentaldaten)
> bleibt **Weg 1 (Google Colab)** die einfachste Wahl auf dem iPad.

---

## Häufige Probleme & Lösungen

| Problem / Meldung | Ursache & Lösung |
|---|---|
| `python` wird nicht gefunden | Bei der Installation das Häkchen **„Add to PATH"** vergessen. Python neu installieren und das Häkchen setzen. Oder `python3` statt `python` probieren. |
| `pip` wird nicht gefunden | Stattdessen `python -m pip ...` (Windows) bzw. `python3 -m pip ...` (Mac/Linux) verwenden. |
| `No module named stockanalyzer` | Du bist nicht im Projektordner. Mit `cd` in den Ordner wechseln, in dem `requirements.txt` liegt. |
| `Keine Kursdaten für '…' gefunden` | Symbol falsch. US-Aktien: reines Kürzel. Deutsche Aktien mit Suffix (`SAP.DE`). |
| `403` / `CONNECT tunnel failed` / kein Abruf | Netzwerk blockiert Yahoo (z. B. Firmen-/Sandbox-Netz). Zu Hause im normalen WLAN klappt es. Als Fallback: `--source stooq`. |
| Report/Chart wird nicht erzeugt | `matplotlib` fehlt. `pip install -r requirements.txt` erneut ausführen. |
| Optionsdaten fehlen | Nicht jede Aktie hat Optionen bei Yahoo; Stooq liefert keine Optionen. |

**Alternative Datenquelle ohne API-Key** (falls Yahoo mal zickt):
```
python -m stockanalyzer AAPL --source stooq
```

**Ohne Internet ausprobieren** (synthetische Beispieldaten):
```
python examples/demo_offline.py
```

---

## Spickzettel (die wichtigsten Befehle)

```
# Umgebung aktivieren (falls in Schritt 4 angelegt)
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # Mac/Linux

# Einzelanalyse
python -m stockanalyzer AAPL

# Ranking mehrerer Werte
python -m stockanalyzer AAPL MSFT NVDA --rank

# Optionen (Call/Put)
python -m stockanalyzer AAPL --options

# Interaktiver Report + Strategie-Vergleich
python -m stockanalyzer AAPL --report report.html --compare

# Positionsgröße (10.000 € Depot, 1 % Risiko je Trade)
python -m stockanalyzer AAPL --capital 10000 --risk-per-trade 1

# Watchlist aus Datei
python -m stockanalyzer --watchlist examples/watchlist.txt --rank

# Hilfe / alle Optionen anzeigen
python -m stockanalyzer --help
```

Viel Erfolg – und denk dran: Risikomanagement (Positionsgröße, Diversifikation)
ist langfristig wichtiger als jedes einzelne Kaufsignal.
