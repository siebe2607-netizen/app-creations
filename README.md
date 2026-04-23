# Portfolio Dashboard 📈

A mobile-friendly Flask app for tracking stocks and ETFs with live prices.

## Features

- Live prices via yfinance for any ticker (stocks, ETFs, crypto, multi-exchange)
- Day / week / month % change with color-coded trends
- SVG sparkline trend per holding (last ~22 trading days)
- Add/remove tickers directly from the dashboard
- Optional `shares` + `cost_basis` for P&L tracking and portfolio total value
- Weekly progress summary card
- In-memory cache (2 min TTL) so repeated refreshes don't hammer Yahoo
- Dark/light theme, responsive for phone

## Run it

```bash
python3.12 -m portfolio_dashboard.app
```

Open http://localhost:5051 (or `http://<your-lan-ip>:5051` on your phone).

## Configure holdings

`portfolio_dashboard/portfolio.yaml`:

```yaml
holdings:
  - ticker: MSFT
    shares: 10
    cost_basis: 320.50
  - ticker: VWCE.DE   # watchlist-only (no shares)
```

You can also add/remove via the UI — the yaml file is updated automatically.

## Shell shortcuts

- `portfolio` — start the server
- `portfolio-stop` — kill it
