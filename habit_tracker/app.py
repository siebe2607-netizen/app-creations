"""Flask web UI for the habit tracker."""
from __future__ import annotations

from datetime import date, timedelta

from flask import Flask, redirect, render_template, request, url_for

from habit_tracker import habits as core

app = Flask(__name__)


@app.route("/")
def index():
    data = core.load()
    today = date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    rows = []
    for name, info in data["habits"].items():
        done = set(info["completions"])
        rows.append({
            "name": name,
            "emoji": info["emoji"],
            "streak": core.streak(info["completions"]),
            "best": core.longest_streak(info["completions"]),
            "weekly_pct": core.weekly_pct(info["completions"]),
            "total": len(info["completions"]),
            "done_today": today.isoformat() in done,
            "week": [{"label": d.strftime("%a"), "done": d.isoformat() in done} for d in days],
        })
    overall_pct = round(sum(r["weekly_pct"] for r in rows) / len(rows)) if rows else 0
    return render_template("index.html", rows=rows, days=days, overall_pct=overall_pct)


@app.post("/add")
def add():
    name = request.form.get("name", "").strip()
    emoji = request.form.get("emoji", "").strip() or "✅"
    if name:
        core.add_habit(name, emoji)
    return redirect(url_for("index"))


@app.post("/check/<name>")
def check(name: str):
    core.check_off(name)
    return redirect(url_for("index"))


@app.post("/delete/<name>")
def delete(name: str):
    data = core.load()
    data["habits"].pop(name, None)
    core.save(data)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5050)
