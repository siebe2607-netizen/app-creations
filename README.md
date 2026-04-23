# Habit Tracker 🌱

A mobile-friendly Flask app for building daily habits.

## Features

- Add habits with a name and emoji
- Check off habits for today (tap again to undo)
- Current streak 🔥 and longest streak 🏆
- Weekly completion % ring + per-habit weekly grid
- Total completions counter
- Confetti burst when you check off a habit
- Dark/light theme (auto-matches system)
- Works on mobile over local WiFi

## Run it

```bash
python3.12 -m habit_tracker.app
```

Then open http://localhost:5050 (or `http://<your-lan-ip>:5050` on your phone).

Data is saved to `habit_tracker/habits_data.json` (gitignored).

## Shell shortcuts

Aliased in `~/.zshrc`:

- `habits` — start the server
- `habits-stop` — kill it from any terminal
