# app-creations

A collection of small Flask web apps — one per branch. All run locally, all mobile-friendly.

## Apps

| Branch | App | Port | Description |
|---|---|---|---|
| [`habit-tracker`](../../tree/habit-tracker) | 🌱 Habit Tracker | 5050 | Daily habits with streaks, weekly grid, confetti |
| [`portfolio-dashboard`](../../tree/portfolio-dashboard) | 📈 Portfolio Dashboard | 5051 | Live stock/ETF prices, P&L, sparklines |
| [`weather-dashboard`](../../tree/weather-dashboard) | ☀️ Weather + Short Pants | 5052 | Forecast with "can I wear shorts?" verdict |
| [`recipe-box`](../../tree/recipe-box) | 🍽️ Recipe Box | 5053 | Recipe collection with random dinner picker |

Each branch has its own `README.md` with details.

## Running locally

```bash
git checkout <branch>
python3.12 -m <module_name>.app
```

Then visit `http://localhost:<port>` on your Mac, or `http://<your-lan-ip>:<port>` on your phone (same WiFi).

## Shell shortcuts

Aliases in `~/.zshrc` for quick start/stop from any terminal:

```
habits     habits-stop
portfolio  portfolio-stop
weather    weather-stop
recipes    recipes-stop
```

## Requirements

- Python 3.12
- Flask, requests, PyYAML, yfinance (for portfolio)
