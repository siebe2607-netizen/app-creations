# Weather Dashboard ☀️

A mobile-friendly Flask app that tells you if you can wear short pants today.

## Features

- Current conditions + 4-day forecast (Open-Meteo API, no key needed)
- **Short-pants verdict** — scores max temp, feels-like, rain probability, and wind to give a YES / MAYBE / NO with reasons
- Search any city (defaults to Groningen, NL)
- Sunrise / sunset times
- Humidity, wind, rain probability, daily high/low
- Weather-code emoji indicators
- Gradient card UI, dark/light theme

## Run it

```bash
python3.12 -m weather_dashboard.app
```

Open http://localhost:5052 (or `http://<your-lan-ip>:5052` on your phone).

## How the short-pants verdict works

Scores based on:
- Max temp today (≥22°C = +3, ≥18 = +2, ≥15 = +1, <15 = -2)
- Feels-like right now
- Rain amount + probability
- Wind speed

Verdict: score ≥3 = YES, ≥1 = probably, ≥-1 = risky, else NO.

## Shell shortcuts

- `weather` — start the server
- `weather-stop` — kill it
