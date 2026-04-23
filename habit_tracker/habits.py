"""Simple habit tracker CLI with JSON storage."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent / "habits_data.json"


def load() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"habits": {}}


def save(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))


def add_habit(name: str, emoji: str) -> None:
    data = load()
    if name in data["habits"]:
        print(f"Habit '{name}' already exists.")
        return
    data["habits"][name] = {"emoji": emoji, "completions": []}
    save(data)
    print(f"Added {emoji} {name}")


def check_off(name: str) -> None:
    """Toggle today's completion for habit."""
    data = load()
    if name not in data["habits"]:
        print(f"No habit named '{name}'. Add it first.")
        return
    today = date.today().isoformat()
    completions = data["habits"][name]["completions"]
    if today in completions:
        completions.remove(today)
        save(data)
        print(f"Unchecked {name} for today.")
        return
    completions.append(today)
    save(data)
    print(f"{data['habits'][name]['emoji']} {name} — done for today!")


def longest_streak(completions: list[str]) -> int:
    if not completions:
        return 0
    dates = sorted({date.fromisoformat(d) for d in completions})
    best = cur = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def weekly_pct(completions: list[str]) -> int:
    today = date.today()
    week = {(today - timedelta(days=i)).isoformat() for i in range(7)}
    return round(len(set(completions) & week) / 7 * 100)


def streak(completions: list[str]) -> int:
    if not completions:
        return 0
    done = {date.fromisoformat(d) for d in completions}
    today = date.today()
    # Allow streak to count if today not yet checked (grace for "current streak")
    start = today if today in done else today - timedelta(days=1)
    count = 0
    d = start
    while d in done:
        count += 1
        d -= timedelta(days=1)
    return count


def show_streaks() -> None:
    data = load()
    if not data["habits"]:
        print("No habits yet. Add one with: add <name> <emoji>")
        return
    for name, info in data["habits"].items():
        s = streak(info["completions"])
        print(f"{info['emoji']} {name}: {s} day streak")


def weekly_grid() -> None:
    data = load()
    if not data["habits"]:
        print("No habits yet.")
        return
    today = date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    header = "  " + " ".join(d.strftime("%a")[:2] for d in days)
    name_w = max(len(f"{i['emoji']} {n}") for n, i in data["habits"].items())
    print(" " * (name_w + 1) + header)
    for name, info in data["habits"].items():
        done = set(info["completions"])
        label = f"{info['emoji']} {name}".ljust(name_w)
        row = " ".join("[x]" if d.isoformat() in done else "[ ]" for d in days)
        print(f"{label}  {row}")


USAGE = """Usage:
  python -m habit_tracker.habits add <name> <emoji>
  python -m habit_tracker.habits check <name>
  python -m habit_tracker.habits streaks
  python -m habit_tracker.habits week
"""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(USAGE)
        return 1
    cmd = argv[1]
    if cmd == "add" and len(argv) == 4:
        add_habit(argv[2], argv[3])
    elif cmd == "check" and len(argv) == 3:
        check_off(argv[2])
    elif cmd == "streaks":
        show_streaks()
    elif cmd == "week":
        weekly_grid()
    else:
        print(USAGE)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
