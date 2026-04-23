# Recipe Box 🍽️

A mobile-friendly Flask app for your recipe collection with a "what's for dinner?" picker.

## Features

- Add recipes with emoji, name, ingredients, steps, prep time, tags, notes
- 🎲 **"Pick for me"** — random dinner picker (favorites weighted 2×)
- ⭐ Favorite toggle on each recipe
- 🏷️ Filter by tag; picker respects the active filter
- 🍳 "Mark cooked today" → tracks last-cooked date + times-cooked count
- Edit / delete / search
- 26 starter recipes seeded (Italian, Asian, Indian, Mexican, French, American)
- Warm orange theme, dark/light support, mobile-friendly

## Run it

```bash
python3.12 -m recipe_box.app
```

Open http://localhost:5053 (or `http://<your-lan-ip>:5053` on your phone).

Data lives in `recipe_box/recipes.json`.

## Shell shortcuts

- `recipes` — start the server
- `recipes-stop` — kill it
