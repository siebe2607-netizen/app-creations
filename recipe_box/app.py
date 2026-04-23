"""Recipe box with 'what's for dinner?' random picker."""
from __future__ import annotations

import io
import json
import random
import zipfile
from datetime import date
from pathlib import Path
from uuid import uuid4

from flask import Flask, Response, abort, flash, get_flashed_messages, redirect, render_template, request, url_for

DATA_FILE = Path(__file__).parent / "recipes.json"

app = Flask(__name__)
app.secret_key = "recipe-box-dev-key"


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


PER_PAGE = 24


def _matches(r: dict, q: str) -> bool:
    """Case-insensitive search across name, ingredients, tags, notes."""
    hay = " ".join([
        r.get("name", ""),
        " ".join(r.get("ingredients") or []),
        " ".join(r.get("tags") or []),
        r.get("notes", ""),
    ]).lower()
    return all(tok in hay for tok in q.lower().split())


@app.route("/")
def index():
    data = load()
    tag = request.args.get("tag", "").strip()
    q = request.args.get("q", "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    recipes = list(data["recipes"].values())
    if tag:
        recipes = [r for r in recipes if tag in r.get("tags", [])]
    if q:
        recipes = [r for r in recipes if _matches(r, q)]
    recipes.sort(key=lambda r: (not r.get("favorite"), r["name"].lower()))

    total = len(recipes)
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(page, pages)
    start = (page - 1) * PER_PAGE
    page_recipes = recipes[start:start + PER_PAGE]

    return render_template(
        "index.html",
        recipes=page_recipes,
        total=total,
        page=page,
        pages=pages,
        tags=all_tags(data["recipes"]),
        current_tag=tag,
        query=q,
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


@app.route("/export")
def export():
    """Download all recipes as JSON."""
    data = load()
    return Response(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": 'attachment; filename="recipes.json"'},
    )


def _is_tandoor(raw: dict) -> bool:
    """Heuristic: Tandoor recipes have a list of step-objects with nested ingredients."""
    if not isinstance(raw, dict):
        return False
    steps = raw.get("steps")
    if not isinstance(steps, list) or not steps:
        return False
    first = steps[0]
    if not isinstance(first, dict):
        return False
    return "instruction" in first or "ingredients" in first


def _format_tandoor_ingredient(ing: dict) -> str:
    """Turn Tandoor {amount, unit, food, note} → 'amount unit food, note'."""
    amount = ing.get("amount")
    unit = (ing.get("unit") or {}).get("name") if isinstance(ing.get("unit"), dict) else ing.get("unit")
    food = (ing.get("food") or {}).get("name") if isinstance(ing.get("food"), dict) else ing.get("food")
    note = ing.get("note")
    parts = []
    if amount:
        # strip trailing .0
        a = f"{amount:g}" if isinstance(amount, (int, float)) else str(amount)
        parts.append(a)
    if unit: parts.append(str(unit))
    if food: parts.append(str(food))
    line = " ".join(parts).strip()
    if note:
        line = f"{line}, {note}" if line else str(note)
    return line or "(ingredient)"


def _parse_tandoor(raw: dict) -> dict:
    """Convert a Tandoor recipe JSON → our recipe format."""
    ingredients: list[str] = []
    step_texts: list[str] = []
    for step in raw.get("steps") or []:
        if not isinstance(step, dict):
            continue
        for ing in step.get("ingredients") or []:
            if isinstance(ing, dict):
                ingredients.append(_format_tandoor_ingredient(ing))
        instr = (step.get("instruction") or "").strip()
        if instr:
            # split on double newlines — Tandoor often has multi-paragraph steps
            for para in instr.split("\n\n"):
                para = para.strip()
                if para:
                    step_texts.append(para)

    tags: list[str] = []
    for kw in raw.get("keywords") or []:
        if isinstance(kw, dict) and kw.get("name"):
            tags.append(str(kw["name"]).lower())
        elif isinstance(kw, str):
            tags.append(kw.lower())

    working = raw.get("working_time") or 0
    waiting = raw.get("waiting_time") or 0
    total = int(working) + int(waiting) if (working or waiting) else None

    description = raw.get("description") or ""
    notes = description.strip() if isinstance(description, str) else ""

    return {
        "name": str(raw.get("name") or "Untitled")[:200],
        "emoji": "🍽️",
        "ingredients": ingredients,
        "steps": step_texts,
        "tags": tags,
        "time_min": total,
        "favorite": False,
        "notes": notes,
        "last_cooked": None,
        "times_cooked": 0,
    }


def _normalize_native(raw: dict) -> dict:
    """Normalize a recipe in our own format, fixing/filling fields."""
    return {
        "name": str(raw["name"])[:200],
        "emoji": raw.get("emoji") or "🍽️",
        "ingredients": [str(s) for s in (raw.get("ingredients") or [])],
        "steps": [str(s) for s in (raw.get("steps") or [])],
        "tags": [str(t).lower() for t in (raw.get("tags") or [])],
        "time_min": raw.get("time_min") if isinstance(raw.get("time_min"), int) else None,
        "favorite": bool(raw.get("favorite", False)),
        "notes": str(raw.get("notes") or ""),
        "last_cooked": raw.get("last_cooked"),
        "times_cooked": int(raw.get("times_cooked") or 0),
    }


def _collect_from_payload(payload) -> list[dict]:
    """Return a list of recipe dicts in our format from any supported source."""
    out: list[dict] = []
    # Case 1: our format {"recipes": {id: {...}}} or {"recipes": [...]}
    if isinstance(payload, dict) and "recipes" in payload:
        items = payload["recipes"]
        items = list(items.values()) if isinstance(items, dict) else items
        for raw in items or []:
            if isinstance(raw, dict) and raw.get("name"):
                out.append(_normalize_native(raw) if not _is_tandoor(raw) else _parse_tandoor(raw))
        return out
    # Case 2: single Tandoor recipe object
    if isinstance(payload, dict) and _is_tandoor(payload):
        return [_parse_tandoor(payload)]
    # Case 3: our format single recipe
    if isinstance(payload, dict) and payload.get("name"):
        return [_normalize_native(payload)]
    # Case 4: plain list
    if isinstance(payload, list):
        for raw in payload:
            if not isinstance(raw, dict) or not raw.get("name"):
                continue
            out.append(_parse_tandoor(raw) if _is_tandoor(raw) else _normalize_native(raw))
        return out
    return []


@app.post("/import")
def import_recipes():
    """Upload a .json or .zip file. Supports:
    - Our native format ({"recipes": {...}} or plain list)
    - Tandoor single-recipe JSON
    - Tandoor .zip export (one folder per recipe, each with recipe.json)"""
    f = request.files.get("file")
    if not f or not f.filename:
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    blob = f.read()
    incoming: list[dict] = []
    skipped = 0

    # Detect by magic bytes / filename
    is_zip = blob[:4] == b"PK\x03\x04" or f.filename.lower().endswith(".zip")

    try:
        if is_zip:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                for name in z.namelist():
                    if not name.lower().endswith(".json"):
                        continue
                    try:
                        payload = json.loads(z.read(name).decode("utf-8"))
                    except Exception:
                        skipped += 1
                        continue
                    incoming.extend(_collect_from_payload(payload))
        else:
            payload = json.loads(blob.decode("utf-8"))
            incoming = _collect_from_payload(payload)
    except Exception as e:
        flash(f"Could not parse file: {e}", "error")
        return redirect(url_for("index"))

    if not incoming:
        flash("No valid recipes found in the file.", "error")
        return redirect(url_for("index"))

    mode = request.form.get("mode", "merge")
    data = load() if mode == "merge" else {"recipes": {}}
    added = 0
    for r in incoming:
        rid = uuid4().hex[:8]
        r["id"] = rid
        data["recipes"][rid] = r
        added += 1
    save(data)
    flash(f"Imported {added} recipe{'s' if added != 1 else ''}"
          + (f" (skipped {skipped} invalid)" if skipped else "")
          + f" — mode: {mode}", "success")
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
