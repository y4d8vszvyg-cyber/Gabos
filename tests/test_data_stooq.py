"""Test des Stooq-CSV-Parsers ohne echtes Netzwerk (urlopen wird simuliert)."""

import io
import urllib.request

import pytest

from stockanalyzer import data


_SAMPLE_CSV = "Date,Open,High,Low,Close,Volume\n" + "\n".join(
    f"2024-01-{d:02d},100,101,99,{100 + d},1000000" for d in range(1, 28)
) + "\n"


class _FakeResp:
    def __init__(self, text):
        self._text = text.encode("utf-8")
    def read(self):
        return self._text
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


def test_stooq_parses_csv(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: _FakeResp(_SAMPLE_CSV))
    md = data.fetch("AAPL", period="1y", source="stooq")
    assert md.ticker == "AAPL"
    assert md.last_price == 127.0            # 100 + 27
    assert len(md.history) == 27
    assert md.info == {}                     # Stooq liefert keine Fundamentaldaten


def test_stooq_empty_response_raises(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: _FakeResp("No data\n"))
    with pytest.raises(data.DataError):
        data.fetch("XYZ", period="1y", source="stooq")


def test_auto_falls_back_to_stooq_without_yfinance(monkeypatch):
    # yfinance-Import scheitern lassen -> auto muss auf Stooq ausweichen.
    def _boom(*a, **k):
        raise data.DataError("yfinance nicht verfuegbar")
    monkeypatch.setattr(data, "_fetch_yahoo", _boom)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: _FakeResp(_SAMPLE_CSV))
    md = data.fetch("AAPL", period="1y", source="auto")
    assert len(md.history) == 27
