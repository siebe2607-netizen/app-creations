"""Portfolio dashboard — live prices, day/week/month performance, sparklines."""
from __future__ import annotations

from pathlib import Path

import yaml
from flask import Flask, render_template

from portfolio_dashboard import data

CONFIG_PATH = Path(__file__).parent / "portfolio.yaml"

app = Flask(__name__)


def load_holdings() -> list[dict]:
    with CONFIG_PATH.open() as f:
        cfg = yaml.safe_load(f)
    return cfg.get("holdings", [])


def spark_svg(values: list[float], width: int = 120, height: int = 32) -> str:
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    rng = hi - lo or 1
    step = width / (len(values) - 1)
    pts = " ".join(
        f"{i * step:.1f},{height - (v - lo) / rng * height:.1f}"
        for i, v in enumerate(values)
    )
    up = values[-1] >= values[0]
    color = "#10b981" if up else "#ef4444"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5"/>'
        f'</svg>'
    )


@app.route("/")
def index():
    holdings = load_holdings()
    tickers = [h["ticker"] for h in holdings]
    quotes = data.fetch_all(tickers)
    by_ticker = {q.ticker: q for q in quotes}

    rows = []
    total_value = 0.0
    total_cost = 0.0
    has_positions = False
    for h in holdings:
        q = by_ticker[h["ticker"]]
        shares = h.get("shares")
        cost = h.get("cost_basis")
        value = (shares * q.price) if (shares and q.price) else None
        pnl = (value - shares * cost) if (value is not None and cost) else None
        pnl_pct = ((q.price - cost) / cost * 100) if (q.price and cost) else None
        if value is not None:
            total_value += value
            has_positions = True
        if shares and cost:
            total_cost += shares * cost
        rows.append({
            "ticker": q.ticker,
            "name": q.name,
            "currency": q.currency,
            "price": q.price,
            "day_pct": q.day_pct,
            "week_pct": q.week_pct,
            "month_pct": q.month_pct,
            "shares": shares,
            "value": value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "spark": spark_svg(q.sparkline),
        })

    total_pnl = (total_value - total_cost) if (has_positions and total_cost) else None
    total_pnl_pct = (total_pnl / total_cost * 100) if (total_pnl is not None and total_cost) else None
    return render_template(
        "index.html",
        rows=rows,
        total_value=total_value if has_positions else None,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5051)
