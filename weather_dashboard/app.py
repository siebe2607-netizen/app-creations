"""Weather dashboard with short-pants verdict. Uses Open-Meteo (no API key)."""
from __future__ import annotations

from datetime import datetime

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Default: Groningen, NL
DEFAULT_LAT = 53.2194
DEFAULT_LON = 6.5665
DEFAULT_CITY = "Groningen"

WEATHER_EMOJI = {
    0: ("☀️", "Clear sky"),
    1: ("🌤️", "Mostly sunny"), 2: ("⛅", "Partly cloudy"), 3: ("☁️", "Overcast"),
    45: ("🌫️", "Fog"), 48: ("🌫️", "Rime fog"),
    51: ("🌦️", "Light drizzle"), 53: ("🌦️", "Drizzle"), 55: ("🌧️", "Heavy drizzle"),
    61: ("🌦️", "Light rain"), 63: ("🌧️", "Rain"), 65: ("🌧️", "Heavy rain"),
    71: ("🌨️", "Light snow"), 73: ("🌨️", "Snow"), 75: ("❄️", "Heavy snow"),
    80: ("🌦️", "Rain showers"), 81: ("🌧️", "Heavy showers"), 82: ("⛈️", "Violent showers"),
    95: ("⛈️", "Thunderstorm"), 96: ("⛈️", "Thunder + hail"), 99: ("⛈️", "Severe thunder"),
}


def describe(code: int) -> tuple[str, str]:
    return WEATHER_EMOJI.get(code, ("🌡️", "Unknown"))


def geocode(city: str) -> tuple[float, float, str] | None:
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en"},
            timeout=5,
        )
        results = r.json().get("results")
        if not results:
            return None
        g = results[0]
        return g["latitude"], g["longitude"], f"{g['name']}, {g.get('country_code', '')}"
    except Exception:
        return None


def fetch_weather(lat: float, lon: float) -> dict:
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,relative_humidity_2m",
            "hourly": "temperature_2m,precipitation_probability,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code,sunrise,sunset",
            "forecast_days": 5,
            "timezone": "auto",
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def short_pants_verdict(current: dict, today_daily: dict) -> dict:
    """Decide whether short pants are a good idea today."""
    temp_now = current["temperature_2m"]
    feels = current["apparent_temperature"]
    wind = current["wind_speed_10m"]
    max_t = today_daily["temperature_2m_max"]
    rain = today_daily["precipitation_sum"]
    rain_prob = today_daily.get("precipitation_probability_max") or 0

    score = 0
    reasons = []

    if max_t >= 22: score += 3; reasons.append(f"High of {max_t:.0f}°C 🌞")
    elif max_t >= 18: score += 2; reasons.append(f"High of {max_t:.0f}°C — warm enough")
    elif max_t >= 15: score += 1; reasons.append(f"High of only {max_t:.0f}°C — borderline")
    else: score -= 2; reasons.append(f"High of only {max_t:.0f}°C — too cold")

    if feels >= 18: score += 1
    elif feels < 12: score -= 1; reasons.append(f"Feels like {feels:.0f}°C right now ❄️")

    if rain >= 5 or rain_prob >= 70:
        score -= 2; reasons.append(f"Rain likely ({rain_prob:.0f}% chance) ☔")
    elif rain >= 1 or rain_prob >= 40:
        score -= 1; reasons.append(f"Some rain possible ({rain_prob:.0f}%)")

    if wind >= 35: score -= 2; reasons.append(f"Very windy ({wind:.0f} km/h) 💨")
    elif wind >= 25: score -= 1; reasons.append(f"Breezy ({wind:.0f} km/h)")

    if score >= 3:
        verdict = "YES — shorts weather! 🩳"
        mood = "yes"
    elif score >= 1:
        verdict = "Probably yes 👍"
        mood = "maybe"
    elif score >= -1:
        verdict = "Risky — maybe long pants"
        mood = "maybe"
    else:
        verdict = "NO — wear long pants 👖"
        mood = "no"

    return {"verdict": verdict, "mood": mood, "score": score, "reasons": reasons}


@app.route("/")
def index():
    city_q = request.args.get("city", "").strip()
    if city_q:
        geo = geocode(city_q)
        if geo:
            lat, lon, label = geo
        else:
            lat, lon, label = DEFAULT_LAT, DEFAULT_LON, f"{DEFAULT_CITY} (couldn't find '{city_q}')"
    else:
        lat, lon, label = DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY

    try:
        w = fetch_weather(lat, lon)
    except Exception as e:
        return render_template("index.html", error=str(e), city=label)

    current = w["current"]
    daily = w["daily"]

    today = {
        "date": daily["time"][0],
        "temperature_2m_max": daily["temperature_2m_max"][0],
        "temperature_2m_min": daily["temperature_2m_min"][0],
        "precipitation_sum": daily["precipitation_sum"][0],
        "precipitation_probability_max": daily["precipitation_probability_max"][0],
        "wind_speed_10m_max": daily["wind_speed_10m_max"][0],
        "weather_code": daily["weather_code"][0],
        "sunrise": daily["sunrise"][0],
        "sunset": daily["sunset"][0],
    }

    emoji, desc = describe(current["weather_code"])
    verdict = short_pants_verdict(current, today)

    forecast = []
    for i in range(1, min(5, len(daily["time"]))):
        d = datetime.fromisoformat(daily["time"][i])
        e, dd = describe(daily["weather_code"][i])
        forecast.append({
            "day": d.strftime("%a"),
            "date": d.strftime("%b %d"),
            "emoji": e, "desc": dd,
            "max": daily["temperature_2m_max"][i],
            "min": daily["temperature_2m_min"][i],
            "rain_prob": daily["precipitation_probability_max"][i] or 0,
        })

    sunrise = datetime.fromisoformat(today["sunrise"]).strftime("%H:%M")
    sunset = datetime.fromisoformat(today["sunset"]).strftime("%H:%M")

    return render_template(
        "index.html",
        city=label,
        current=current, emoji=emoji, desc=desc,
        today=today, verdict=verdict,
        forecast=forecast,
        sunrise=sunrise, sunset=sunset,
        error=None,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5052)
