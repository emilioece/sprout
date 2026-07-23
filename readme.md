# Sprout (Kivy port)

A Kivy desktop port of the Sprout plant-care dashboard, styled to match the
original React/Tailwind version as closely as Kivy's canvas drawing allows
(rounded cards, the green/cream palette, sidebar nav, stat cards, and the
two-step "Add Plant" wizard).

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Make sure your FastAPI backend is running on `http://localhost:8000` first
(same backend the original Next.js app talked to).

## Files

- `main.py` — app logic: screen state, the two-step Add Plant modal, the
  delete confirmation modal, and all the widget classes (StatCard, PlantRow,
  SideNavItem, etc).
- `sprout.kv` — Kivy language file with all the visual styling: rounded
  rectangles for cards/buttons, the sidebar layout, colors. Kivy auto-loads
  this because the App class is named `SproutApp`.
- `api.py` — thin `requests`-based wrapper around the backend
  (`fetch_plants`, `create_plant`, `water_plant`, `delete_plant`).

## About the API endpoints

Your original `lib/api.ts` file wasn't shared, so `api.py` guesses at
reasonable REST endpoints based on the function names used in the React
component:

| Function        | Method & path              |
|------------------|-----------------------------|
| `fetch_plants`   | `GET /plants`               |
| `create_plant`   | `POST /plants`               |
| `water_plant`    | `PATCH /plants/{id}/water`  |
| `delete_plant`   | `DELETE /plants/{id}`       |

If your FastAPI routes are different, just edit the URLs/methods at the top
of `api.py` — nothing else needs to change, since the rest of the app only
calls these four functions.



## Notes on the port

- All network calls run on a background `threading.Thread` and hop back to
  the main/UI thread via `Clock.schedule_once`, since Kivy (like Tk and Qt)
  is single-threaded for UI updates.
- The frosted "backdrop-blur" overlay behind modals isn't replicated (Kivy
  doesn't do blur easily) — modals instead get a plain dim overlay, which
  `ModalView` gives you for free.
- Hover/scale micro-interactions from the original CSS (`hover:scale-105`,
  `active:scale-95`) aren't ported 1:1; buttons darken slightly when
  pressed instead. These would be easy to add with Kivy's `Animation` class
  if you want that later.
- Emoji icons are used in place of the original inline SVG trash icon and
  emoji already used elsewhere in your component, so no icon font/assets
  are required to run this.