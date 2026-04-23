"""Recipe box with 'what's for dinner?' random picker."""
from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request, url_for

DATA_FILE = Path(__file__).parent / "recipes.json"

app = Flask(__name__)


def load() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"recipes": {}}


def save(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))


def all_tags(recipes: dict) -> list[str]:
    tags: set[str] = set()
    for r in recipes.values():
        tags.update(r.get("tags", []))
    return sorted(tags)


@app.route("/")
def index():
    data = load()
    tag = request.args.get("tag", "").strip()
    recipes = list(data["recipes"].values())
    if tag:
        recipes = [r for r in recipes if tag in r.get("tags", [])]
    recipes.sort(key=lambda r: (not r.get("favorite"), r["name"].lower()))
    return render_template(
        "index.html",
        recipes=recipes,
        tags=all_tags(data["recipes"]),
        current_tag=tag,
        highlight_id=request.args.get("pick"),
    )


@app.route("/pick")
def pick():
    data = load()
    tag = request.args.get("tag", "").strip()
    pool = list(data["recipes"].values())
    if tag:
        pool = [r for r in pool if tag in r.get("tags", [])]
    if not pool:
        return redirect(url_for("index"))
    # Weight favorites 2x
    weights = [2 if r.get("favorite") else 1 for r in pool]
    chosen = random.choices(pool, weights=weights, k=1)[0]
    return redirect(url_for("view", rid=chosen["id"]))


@app.route("/r/<rid>")
def view(rid: str):
    data = load()
    r = data["recipes"].get(rid)
    if not r:
        abort(404)
    return render_template("view.html", r=r)


@app.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        return _save_from_form(None)
    return render_template("edit.html", r=None)


@app.route("/edit/<rid>", methods=["GET", "POST"])
def edit(rid: str):
    data = load()
    r = data["recipes"].get(rid)
    if not r:
        abort(404)
    if request.method == "POST":
        return _save_from_form(rid)
    return render_template("edit.html", r=r)


def _save_from_form(rid: str | None):
    data = load()
    rid = rid or uuid4().hex[:8]
    existing = data["recipes"].get(rid, {})
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("index"))
    r = {
        "id": rid,
        "name": name,
        "emoji": request.form.get("emoji", "").strip() or "🍽️",
        "ingredients": [s.strip() for s in request.form.get("ingredients", "").splitlines() if s.strip()],
        "steps": [s.strip() for s in request.form.get("steps", "").splitlines() if s.strip()],
        "tags": [t.strip().lower() for t in request.form.get("tags", "").split(",") if t.strip()],
        "time_min": _as_int(request.form.get("time_min")),
        "favorite": bool(request.form.get("favorite")),
        "notes": request.form.get("notes", "").strip(),
        "last_cooked": existing.get("last_cooked"),
        "times_cooked": existing.get("times_cooked", 0),
    }
    data["recipes"][rid] = r
    save(data)
    return redirect(url_for("view", rid=rid))


def _as_int(v):
    try: return int(v) if v else None
    except ValueError: return None


@app.post("/cooked/<rid>")
def cooked(rid: str):
    data = load()
    r = data["recipes"].get(rid)
    if r:
        r["last_cooked"] = date.today().isoformat()
        r["times_cooked"] = r.get("times_cooked", 0) + 1
        save(data)
    return redirect(url_for("view", rid=rid))


@app.post("/delete/<rid>")
def delete(rid: str):
    data = load()
    data["recipes"].pop(rid, None)
    save(data)
    return redirect(url_for("index"))


@app.post("/favorite/<rid>")
def favorite(rid: str):
    data = load()
    r = data["recipes"].get(rid)
    if r:
        r["favorite"] = not r.get("favorite", False)
        save(data)
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5053)
