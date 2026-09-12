"""Interaktiver HTML-Report: Equity-Kurve (Hover), Drawdown, Strategie-Vergleich.

Erzeugt eine **eigenstaendige** HTML-Datei ohne externe Abhaengigkeiten
(kein CDN, kein Netz noetig) - die Charts sind handgezeichnetes SVG mit
Vanilla-JavaScript fuer Fadenkreuz + Tooltip. Die Datei laesst sich lokal im
Browser oeffnen und ist zugleich als Artifact veroeffentlichbar.

Aufbau:
* ``build_fragment(...)`` -> Inhalt (``<style>`` + Markup + ``<script>``), z.B.
  fuer eine Artifact-Veroeffentlichung.
* ``build_html(...)``     -> vollstaendiges HTML-Dokument fuer die lokale Datei.
"""

from __future__ import annotations

import json
from typing import Optional

import pandas as pd

from .analyzer import StockReport
from .backtest import BacktestResult

# Validierte, farbenblind-sichere Kategorienpalette (Slots 1-4).
_SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


def _payload(report: Optional[StockReport], primary: BacktestResult,
             close: pd.Series, comparison: Optional[list]) -> dict:
    """Baut das JSON-Datenobjekt, das die Charts im Browser zeichnen."""
    dates = [d.strftime("%Y-%m-%d") for d in primary.equity_curve.index]

    def norm100(series: pd.Series) -> list:
        base = float(series.iloc[0])
        return [round(float(v) / base * 100, 3) for v in series.values]

    data = {
        "dates": dates,
        "equity": {
            "strategy": norm100(primary.equity_curve),
            "hold": norm100(close),
        },
        "drawdown": [round(float(v), 3) for v in primary.drawdown.values],
        "primaryStats": {
            "total": primary.total_return_pct, "hold": primary.buy_hold_return_pct,
            "sharpe": primary.sharpe, "maxdd": primary.max_drawdown_pct,
            "exposure": primary.exposure_pct, "trades": primary.num_trades,
            "winrate": primary.win_rate_pct, "annual": primary.annual_return_pct,
            "vol": primary.annual_volatility_pct,
        },
        "seriesColors": _SERIES_COLORS,
    }

    if comparison:
        data["comparison"] = [
            {
                "name": r.name,
                "equity": norm100(r.equity_curve),
                "total": r.total_return_pct, "sharpe": r.sharpe,
                "maxdd": r.max_drawdown_pct, "exposure": r.exposure_pct,
                "trades": r.num_trades, "winrate": r.win_rate_pct,
            }
            for r in comparison
        ]

    if report is not None:
        data["meta"] = {
            "name": report.name, "ticker": report.ticker,
            "price": round(report.last_price, 2), "currency": report.currency,
            "tech": report.technical.score, "fund": report.fundamental.score,
            "combined": report.combined_score, "recommendation": report.recommendation,
            "signals": [
                {"name": n, "dir": ("up" if c > 0 else "down" if c < 0 else "flat"), "reason": reason}
                for (n, c, reason) in report.technical.signals
            ],
            "warnings": report.warnings,
        }
    return data


# --- CSS + Markup + JS (ohne f-string, damit geschweifte Klammern erhalten bleiben) ---

_STYLE_AND_BODY = r"""
<style>
  :root {
    --bg: #f4f4f2; --surface: #ffffff; --ink: #0b0b0b; --muted: #52514e;
    --line: #e6e6e3; --up: #008300; --down: #e34948; --dd: #e34948;
    --shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04);
  }
  :root:not([data-theme="light"]) { }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #121211; --surface: #1f1f1d; --ink: #f5f5f0; --muted: #b8b7ad;
      --line: #33332f; --up: #46c246; --down: #e66767; --dd: #e66767;
      --shadow: 0 1px 3px rgba(0,0,0,.4);
    }
  }
  :root[data-theme="dark"] {
    --bg: #121211; --surface: #1f1f1d; --ink: #f5f5f0; --muted: #b8b7ad;
    --line: #33332f; --up: #46c246; --down: #e66767; --dd: #e66767;
    --shadow: 0 1px 3px rgba(0,0,0,.4);
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--ink);
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; }
  .wrap { max-width: 1000px; margin: 0 auto; padding-block: 24px; padding-inline: 16px; }
  .card { background: var(--surface); border-radius: 12px; box-shadow: var(--shadow);
    padding: 20px; margin-bottom: 20px; }
  h1 { font-size: 22px; margin: 0 0 2px; }
  h2 { font-size: 16px; margin: 0 0 14px; }
  .sub { color: var(--muted); font-size: 13px; margin: 0; }
  .disclaimer { background: #fff7ed; border: 1px solid #fed7aa; color: #7c2d12;
    border-radius: 10px; padding: 12px 14px; font-size: 12.5px; margin-bottom: 20px; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .disclaimer {
    background: #2a1c0e; border-color: #6b4423; color: #fdba74; } }
  .kpis { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 8px; }
  .kpi { flex: 1; min-width: 120px; background: var(--bg); border-radius: 10px; padding: 12px 14px; }
  .kpi .label { color: var(--muted); font-size: 12px; }
  .kpi .value { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .reco { display: inline-block; padding: 6px 12px; border-radius: 999px;
    font-weight: 700; font-size: 14px; }
  .legend { display: flex; flex-wrap: wrap; gap: 16px; margin: 4px 0 10px; font-size: 13px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); }
  .swatch { width: 14px; height: 3px; border-radius: 2px; display: inline-block; }
  svg { width: 100%; height: auto; display: block; touch-action: none; }
  .tt { position: fixed; pointer-events: none; background: var(--surface); color: var(--ink);
    border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow);
    padding: 8px 10px; font-size: 12.5px; opacity: 0; transition: opacity .08s; z-index: 10; white-space: nowrap; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: right; padding: 8px 10px; border-bottom: 1px solid var(--line); }
  th:first-child, td:first-child { text-align: left; }
  thead th { color: var(--muted); font-weight: 600; }
  tbody tr.best td { background: rgba(42,120,214,.07); }
  .sig { display: flex; gap: 8px; padding: 5px 0; align-items: baseline; font-size: 13px; }
  .sig .dot { font-weight: 800; width: 14px; }
  .sig .up { color: var(--up); } .sig .down { color: var(--down); }
  .sig .nm { min-width: 150px; font-weight: 600; }
  .sig .rs { color: var(--muted); }
  .foot { color: var(--muted); font-size: 12px; text-align: center; margin-top: 8px; }
  .overflow { overflow-x: auto; }
</style>

<div class="wrap">
  <div class="disclaimer" id="disc"></div>
  <div class="card" id="header"></div>
  <div class="card">
    <h2>Equity-Kurve &middot; Strategie vs. Buy &amp; Hold</h2>
    <div class="legend" id="eqLegend"></div>
    <div id="eqChart"></div>
  </div>
  <div class="card">
    <h2>Drawdown der Strategie (Verlust vom letzten Hoch)</h2>
    <div id="ddChart"></div>
  </div>
  <div class="card" id="cmpCard" hidden>
    <h2>Strategie-Vergleich</h2>
    <div class="legend" id="cmpLegend"></div>
    <div id="cmpChart"></div>
    <div class="overflow"><table id="cmpTable"></table></div>
  </div>
  <div class="card" id="signals" hidden></div>
  <p class="foot">Erstellt mit stockanalyzer &middot; Keine Anlageberatung &middot;
     Historische Ergebnisse sind keine Garantie fuer die Zukunft.</p>
</div>

<div class="tt" id="tt"></div>

<script>
(function () {
  const R = REPORT;
  const NS = "http://www.w3.org/2000/svg";
  const W = 1000, H = 320, PAD = { l: 48, r: 60, t: 16, b: 28 };
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const fmt = (x, d = 1) => (x >= 0 ? "+" : "") + x.toFixed(d);
  const tt = document.getElementById("tt");

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  // Generischer Linien-Chart mit Fadenkreuz + Tooltip.
  function lineChart(mountId, opts) {
    const { dates, series, height = H, yLabel = "", area = false, baseline = null,
            fmtVal = (v) => v.toFixed(1) } = opts;
    const h = height;
    const mount = document.getElementById(mountId);
    mount.innerHTML = "";
    const svg = el("svg", { viewBox: `0 0 ${W} ${h}`, preserveAspectRatio: "none" }, mount);
    svg.style.height = h + "px"; svg.style.maxHeight = h + "px";

    let lo = Infinity, hi = -Infinity;
    series.forEach((s) => s.values.forEach((v) => { if (v < lo) lo = v; if (v > hi) hi = v; }));
    if (baseline !== null) { lo = Math.min(lo, baseline); hi = Math.max(hi, baseline); }
    const padY = (hi - lo) * 0.08 || 1; lo -= padY; hi += padY;
    const n = dates.length;
    const X = (i) => PAD.l + (W - PAD.l - PAD.r) * (n <= 1 ? 0 : i / (n - 1));
    const Y = (v) => PAD.t + (h - PAD.t - PAD.b) * (1 - (v - lo) / (hi - lo));

    // Y-Gitter + Beschriftung.
    const ticks = 4;
    for (let t = 0; t <= ticks; t++) {
      const val = lo + (hi - lo) * t / ticks, y = Y(val);
      el("line", { x1: PAD.l, y1: y, x2: W - PAD.r, y2: y, stroke: css("--line"), "stroke-width": 1 }, svg);
      const tx = el("text", { x: PAD.l - 8, y: y + 4, "text-anchor": "end",
        "font-size": 11, fill: css("--muted") }, svg);
      tx.textContent = fmtVal(val);
    }
    if (baseline !== null) {
      el("line", { x1: PAD.l, y1: Y(baseline), x2: W - PAD.r, y2: Y(baseline),
        stroke: css("--muted"), "stroke-width": 1, "stroke-dasharray": "4 4", opacity: .55 }, svg);
    }

    // X-Beschriftung (Anfang, Mitte, Ende).
    [0, Math.floor((n - 1) / 2), n - 1].forEach((i) => {
      const tx = el("text", { x: X(i), y: h - 8, "text-anchor": i === 0 ? "start" : i === n - 1 ? "end" : "middle",
        "font-size": 11, fill: css("--muted") }, svg);
      tx.textContent = (dates[i] || "").slice(0, 7);
    });

    // Flaeche (nur Drawdown) + Linien.
    series.forEach((s) => {
      if (area) {
        let d = `M ${X(0)} ${Y(baseline || 0)}`;
        s.values.forEach((v, i) => { d += ` L ${X(i)} ${Y(v)}`; });
        d += ` L ${X(n - 1)} ${Y(baseline || 0)} Z`;
        el("path", { d, fill: s.color, opacity: .16 }, svg);
      }
      let d = "";
      s.values.forEach((v, i) => { d += (i ? " L " : "M ") + X(i) + " " + Y(v); });
      el("path", { d, fill: "none", stroke: s.color, "stroke-width": 2,
        "stroke-linejoin": "round", "stroke-linecap": "round",
        "vector-effect": "non-scaling-stroke" }, svg);
      // Direktes End-Label.
      const last = s.values[n - 1];
      const lb = el("text", { x: X(n - 1) + 6, y: Y(last) + 4, "font-size": 11.5,
        "font-weight": 700, fill: s.color }, svg);
      lb.textContent = s.short || fmtVal(last);
    });

    // Fadenkreuz + Marker + Tooltip.
    const cross = el("line", { x1: 0, y1: PAD.t, x2: 0, y2: h - PAD.b,
      stroke: css("--muted"), "stroke-width": 1, opacity: 0 }, svg);
    const markers = series.map((s) => el("circle", { r: 4, fill: s.color,
      stroke: css("--surface"), "stroke-width": 2, opacity: 0 }, svg));
    const pt = svg.createSVGPoint();
    function idxFromEvent(ev) {
      pt.x = ev.clientX; pt.y = ev.clientY;
      const p = pt.matrixTransform(svg.getScreenCTM().inverse());
      const frac = (p.x - PAD.l) / (W - PAD.l - PAD.r);
      return Math.max(0, Math.min(n - 1, Math.round(frac * (n - 1))));
    }
    function move(ev) {
      const i = idxFromEvent(ev);
      cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("opacity", .6);
      let rows = `<b>${dates[i]}</b>`;
      series.forEach((s, k) => {
        markers[k].setAttribute("cx", X(i)); markers[k].setAttribute("cy", Y(s.values[i]));
        markers[k].setAttribute("opacity", 1);
        rows += `<br><span style="color:${s.color}">&#9632;</span> ${s.name}: <b>${fmtVal(s.values[i])}</b>`;
      });
      tt.innerHTML = rows; tt.style.opacity = 1;
      let tx = ev.clientX + 14, ty = ev.clientY + 14;
      const r = tt.getBoundingClientRect();
      if (tx + r.width > innerWidth) tx = ev.clientX - r.width - 14;
      if (ty + r.height > innerHeight) ty = ev.clientY - r.height - 14;
      tt.style.left = tx + "px"; tt.style.top = ty + "px";
    }
    function leave() { cross.setAttribute("opacity", 0); markers.forEach((m) => m.setAttribute("opacity", 0)); tt.style.opacity = 0; }
    svg.addEventListener("pointermove", move);
    svg.addEventListener("pointerleave", leave);
  }

  // --- Disclaimer ---
  document.getElementById("disc").innerHTML =
    "<b>Hinweis:</b> Analyse- und Bildungswerkzeug, <b>keine Anlageberatung</b>. " +
    "Kursprognosen sind unmoeglich, Verluste (bei Optionen Totalverlust) moeglich. " +
    "Triff keine Entscheidung allein auf Basis dieser Ausgabe.";

  // --- Kopf / KPIs ---
  const cP = R.seriesColors;
  if (R.meta) {
    const m = R.meta;
    const recoColor = m.combined >= 58 ? css("--up") : m.combined < 42 ? css("--down") : css("--muted");
    document.getElementById("header").innerHTML =
      `<h1>${m.name} <span class="sub">(${m.ticker})</span></h1>
       <p class="sub">Letzter Kurs: <b>${m.price} ${m.currency}</b></p>
       <div class="kpis">
         <div class="kpi"><div class="label">Technik</div><div class="value">${m.tech}</div></div>
         <div class="kpi"><div class="label">Fundamental</div><div class="value">${m.fund}</div></div>
         <div class="kpi"><div class="label">Gesamt-Score</div><div class="value">${m.combined}</div></div>
         <div class="kpi"><div class="label">Empfehlung</div>
           <div class="value" style="font-size:15px"><span class="reco" style="background:${recoColor}22;color:${recoColor}">${m.recommendation}</span></div></div>
       </div>`;
    if (m.signals && m.signals.length) {
      const sc = document.getElementById("signals"); sc.hidden = false;
      sc.innerHTML = "<h2>Technische Signale</h2>" + m.signals.map((s) =>
        `<div class="sig"><span class="dot ${s.dir}">${s.dir === "up" ? "▲" : s.dir === "down" ? "▼" : "•"}</span>`
        + `<span class="nm">${s.name}</span><span class="rs">${s.reason}</span></div>`).join("");
    }
  } else {
    const st = R.primaryStats;
    document.getElementById("header").innerHTML =
      `<h1>Backtest-Report</h1><p class="sub">Trendfolge-Strategie vs. Buy &amp; Hold</p>
       <div class="kpis">
         <div class="kpi"><div class="label">Strategie</div><div class="value">${fmt(st.total)}%</div></div>
         <div class="kpi"><div class="label">Buy &amp; Hold</div><div class="value">${fmt(st.hold)}%</div></div>
         <div class="kpi"><div class="label">Sharpe</div><div class="value">${st.sharpe}</div></div>
         <div class="kpi"><div class="label">Max Drawdown</div><div class="value">${st.maxdd}%</div></div>
       </div>`;
  }

  // --- Equity-Chart ---
  document.getElementById("eqLegend").innerHTML =
    `<span><i class="swatch" style="background:${cP[0]}"></i>Strategie</span>
     <span><i class="swatch" style="background:${cP[1]}"></i>Buy &amp; Hold</span>`;
  lineChart("eqChart", {
    dates: R.dates, baseline: 100, yLabel: "Kapital",
    fmtVal: (v) => v.toFixed(0),
    series: [
      { name: "Strategie", short: R.equity.strategy[R.equity.strategy.length - 1].toFixed(0), color: cP[0], values: R.equity.strategy },
      { name: "Buy & Hold", short: R.equity.hold[R.equity.hold.length - 1].toFixed(0), color: cP[1], values: R.equity.hold },
    ],
  });

  // --- Drawdown-Chart ---
  lineChart("ddChart", {
    dates: R.dates, height: 200, baseline: 0, area: true,
    fmtVal: (v) => v.toFixed(0) + "%",
    series: [{ name: "Drawdown", short: "", color: css("--dd"), values: R.drawdown }],
  });

  // --- Strategie-Vergleich ---
  if (R.comparison && R.comparison.length) {
    document.getElementById("cmpCard").hidden = false;
    const series = R.comparison.map((c, i) => ({
      name: c.name, short: "", color: cP[i % cP.length], values: c.equity,
    }));
    document.getElementById("cmpLegend").innerHTML = series.map((s) =>
      `<span><i class="swatch" style="background:${s.color}"></i>${s.name}</span>`).join("");
    lineChart("cmpChart", { dates: R.dates, baseline: 100, fmtVal: (v) => v.toFixed(0), series });

    const best = R.comparison.reduce((a, b) => (b.sharpe > a.sharpe ? b : a), R.comparison[0]);
    let rows = "<thead><tr><th>Strategie</th><th>Rendite</th><th>Sharpe</th>"
      + "<th>Max DD</th><th>Trefferq.</th><th>Investiert</th><th>Trades</th></tr></thead><tbody>";
    R.comparison.forEach((c) => {
      rows += `<tr class="${c === best ? "best" : ""}"><td>${c.name}</td>`
        + `<td>${fmt(c.total)}%</td><td>${c.sharpe}</td><td>${c.maxdd}%</td>`
        + `<td>${c.winrate}%</td><td>${c.exposure}%</td><td>${c.trades}</td></tr>`;
    });
    document.getElementById("cmpTable").innerHTML = rows + "</tbody>";
  }
})();
</script>
"""


def build_fragment(primary: BacktestResult, close: pd.Series,
                   report: Optional[StockReport] = None,
                   comparison: Optional[list] = None) -> str:
    """Inhalt (Style + Markup + Script) - ohne <html>/<head>/<body>."""
    data = _payload(report, primary, close, comparison)
    inject = "<script>const REPORT = " + json.dumps(data) + ";</script>\n"
    return inject + _STYLE_AND_BODY


def build_html(primary: BacktestResult, close: pd.Series,
               report: Optional[StockReport] = None,
               comparison: Optional[list] = None,
               title: str = "stockanalyzer - Report") -> str:
    """Vollstaendiges, eigenstaendiges HTML-Dokument fuer eine lokale Datei."""
    fragment = build_fragment(primary, close, report, comparison)
    return (
        "<!doctype html>\n<html lang=\"de\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{title}</title>\n</head>\n<body>\n"
        + fragment
        + "\n</body>\n</html>\n"
    )


def write_html(path: str, primary: BacktestResult, close: pd.Series,
               report: Optional[StockReport] = None,
               comparison: Optional[list] = None,
               title: str = "stockanalyzer - Report") -> str:
    """Schreibt den Report als HTML-Datei und gibt den Pfad zurueck."""
    html = build_html(primary, close, report, comparison, title)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path
