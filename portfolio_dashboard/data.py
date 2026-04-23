"""Fetch price data via yfinance with simple in-memory caching."""
from __future__ import annotations

import time
from dataclasses import dataclass

import yfinance as yf

_CACHE: dict[str, tuple[float, dict]] = {}
_TTL = 120  # seconds


@dataclass
class Quote:
    ticker: str
    name: str
    currency: str
    price: float | None
    prev_close: float | None
    week_ago: float | None
    month_ago: float | None
    sparkline: list[float]

    @property
    def day_pct(self) -> float | None:
        if self.price is None or not self.prev_close:
            return None
        return (self.price - self.prev_close) / self.prev_close * 100

    @property
    def week_pct(self) -> float | None:
        if self.price is None or not self.week_ago:
            return None
        return (self.price - self.week_ago) / self.week_ago * 100

    @property
    def month_pct(self) -> float | None:
        if self.price is None or not self.month_ago:
            return None
        return (self.price - self.month_ago) / self.month_ago * 100


def fetch_quote(ticker: str) -> Quote:
    now = time.time()
    cached = _CACHE.get(ticker)
    if cached and now - cached[0] < _TTL:
        return Quote(**cached[1])

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1mo", interval="1d")
        info = getattr(t, "fast_info", None) or {}
        closes = [float(x) for x in hist["Close"].tolist() if x == x]  # filter NaN
        price = closes[-1] if closes else None
        prev_close = closes[-2] if len(closes) >= 2 else None
        week_ago = closes[-6] if len(closes) >= 6 else (closes[0] if closes else None)
        month_ago = closes[0] if closes else None
        currency = (info.get("currency") if isinstance(info, dict) else getattr(info, "currency", None)) or "USD"
        name = ticker
        try:
            name = t.info.get("shortName") or t.info.get("longName") or ticker
        except Exception:
            pass
        q = Quote(
            ticker=ticker, name=name, currency=currency,
            price=price, prev_close=prev_close,
            week_ago=week_ago, month_ago=month_ago,
            sparkline=closes[-22:],
        )
    except Exception:
        q = Quote(ticker=ticker, name=ticker, currency="",
                  price=None, prev_close=None, week_ago=None, month_ago=None, sparkline=[])

    _CACHE[ticker] = (now, q.__dict__)
    return q


def fetch_all(tickers: list[str]) -> list[Quote]:
    return [fetch_quote(t) for t in tickers]
