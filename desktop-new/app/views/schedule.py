# ===========================================================================
# Care Schedule Page View
# ===========================================================================

import calendar
from components.widgets import RoundedBox, PillButton, EmojiLabel, IconRow
from datetime import date, timedelta

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from theme import theme

_view = {"year": date.today().year, "month": date.today().month}

# One entry per care type: which fields to read off the plant dict, and
# the same emoji already used for that care type's button/toast elsewhere
# in the app, so the calendar, legend, and sidebar all agree visually.
CARE_TYPES = [
    {
        "key": "water",
        "days_field": "daysUntilWater",
        "interval_field": "watering_interval_days",
        "default_interval": 7,
        "icon": "\U0001F4A7",
    },
    {
        "key": "fertilize",
        "days_field": "daysUntilFertilize",
        "interval_field": "fertilizing_interval_days",
        "default_interval": 30,
        "icon": "\U0001F33F",
    },
    {
        "key": "repot",
        "days_field": "daysUntilRepot",
        "interval_field": "repotting_interval_days",
        "default_interval": 365,
        "icon": "\U0001FAB4",
    },
]


def _care_days_this_month(app, year, month, days_field, interval_field, default_interval):
    """
    Projects one care type (water/fertilize/repot) forward across the
    visible month, the same way _watering_days_this_month used to for
    watering alone. Returns {day_of_month: [plant names due that day]}.
    """
    result = {}
    today = date.today()

    for plant in app.plants:
        days_until = plant.get(days_field, 0)
        interval = plant.get(interval_field) or default_interval
        name = plant.get("name") or plant.get("nickname", "Plant")

        cursor = today + timedelta(days=days_until)
        month_end = date(year, month, calendar.monthrange(year, month)[1])

        if interval < 1:
            interval = default_interval

        while cursor <= month_end:
            if cursor.year == year and cursor.month == month:
                result.setdefault(cursor.day, []).append(name)
            cursor += timedelta(days=interval)

    return result


def _all_care_days_this_month(app, year, month):
    """
    Runs the projection for every care type and merges them into one
    per-day structure: {day: {"water": [...], "fertilize": [...], "repot": [...]}}
    Only keys with at least one name are present for a given day.
    """
    merged = {}
    for care in CARE_TYPES:
        days = _care_days_this_month(
            app, year, month,
            care["days_field"], care["interval_field"], care["default_interval"],
        )
        for day, names in days.items():
            merged.setdefault(day, {})[care["key"]] = names
    return merged


def _build_day_cell(day, is_today, day_events):
    """
    Builds one calendar cell: the day number on top, and a small row of
    tiny emoji icons underneath for whichever care types are due that day.
    Every cell (even empty ones) has the same two-part shape, so all rows
    in the grid stay the same height.
    """
    cell = BoxLayout(orientation="vertical", spacing=dp(1))

    day_lbl = Label(
        text=str(day), color=theme.text, font_size="12sp",
        bold=is_today, size_hint_y=None, height=dp(18),
    )
    cell.add_widget(day_lbl)

    icons_row = BoxLayout(size_hint_y=None, height=dp(12), spacing=dp(2))
    for care in CARE_TYPES:
        if care["key"] in day_events:
            icons_row.add_widget(EmojiLabel(
                text=care["icon"], font_size="8sp",
                size_hint=(None, None), size=(dp(11), dp(11)),
            ))
    cell.add_widget(icons_row)

    return cell


def render_schedule(app):
    """Renders the monthly care calendar and upcoming task list split-view."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    year = _view["year"]
    month = _view["month"]
    today = date.today()

    all_days = _all_care_days_this_month(app, year, month)

    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(text="Care Schedule", bold=True, font_size="30sp",
                            color=theme.text, halign="left",
                            size_hint_y=None, height=dp(40)))
    header.add_widget(Label(
        text=f"{len(app.plants)} plants Â· watering, fertilizing & repotting schedule",
        font_size="12sp", color=theme.muted, halign="left",
        size_hint_y=None, height=dp(18)))
    container.add_widget(header)

    # Small legend using the same emoji + label style as the sidebar rows,
    # so the calendar icons are explained rather than guessed at.
    legend = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(16))
    for care in CARE_TYPES:
        legend.add_widget(IconRow(
            icon=care["icon"],
            text=care["key"].capitalize(),
            text_color=theme.muted,
            icon_size="14sp",
            text_size="11sp",
            icon_width=dp(18),
            size_hint_x=None,
            width=dp(100),
        ))
    container.add_widget(legend)

    split = BoxLayout(size_hint_y=None, height=dp(380), spacing=dp(24))

    cal_box = RoundedBox(orientation="vertical", padding=dp(16),
                         bg_color=theme.surface, border_color=theme.border)

    cal_header = BoxLayout(size_hint_y=None, height=dp(30))

    prev_btn = PillButton(text="<", size_hint=(None, None), size=(dp(30), dp(30)),
                          bg_color=theme.chip, fg_color=theme.text)
    prev_btn.bind(on_release=lambda *_: _change_month(app, -1))
    cal_header.add_widget(prev_btn)

    month_name = calendar.month_name[month]
    cal_header.add_widget(Label(text=f"{month_name} {year}", bold=True,
                                color=theme.text, font_size="16sp"))

    next_btn = PillButton(text=">", size_hint=(None, None), size=(dp(30), dp(30)),
                          bg_color=theme.chip, fg_color=theme.text)
    next_btn.bind(on_release=lambda *_: _change_month(app, 1))
    cal_header.add_widget(next_btn)

    cal_box.add_widget(cal_header)

    grid = GridLayout(cols=7, spacing=dp(4), padding=[0, dp(10)])
    for day in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
        grid.add_widget(Label(text=day, font_size="11sp", bold=True, color=theme.muted))

    first_weekday = (calendar.weekday(year, month, 1) + 1) % 7
    for _ in range(first_weekday):
        grid.add_widget(Widget())

    days_in_month = calendar.monthrange(year, month)[1]

    for day in range(1, days_in_month + 1):
        is_today = (day == today.day and month == today.month and year == today.year)
        day_events = all_days.get(day, {})

        cell = _build_day_cell(day, is_today, day_events)

        if is_today:
            box = RoundedBox(bg_color=theme.accent_soft, border_color=theme.accent_soft, radius=dp(8))
            box.add_widget(cell)
            grid.add_widget(box)
        else:
            grid.add_widget(cell)

    cal_box.add_widget(grid)
    split.add_widget(cal_box)

    side = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(220), spacing=dp(10))
    side.add_widget(Label(text="Upcoming", bold=True, font_size="16sp",
                          color=theme.text, halign="left",
                          size_hint_y=None, height=dp(24)))

    # Flatten every (day, care type, plant name) across the month, in date order
    events = []
    for day in sorted(all_days.keys()):
        cell_date = date(year, month, day)
        if cell_date < today:
            continue
        for care in CARE_TYPES:
            for name in all_days[day].get(care["key"], []):
                events.append((day, care, name))

    if events:
        scroll = ScrollView(do_scroll_x=False)
        events_box = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        events_box.bind(minimum_height=events_box.setter("height"))

        for day, care, name in events:
            row = RoundedBox(orientation="horizontal", size_hint_y=None,
                             height=dp(44), padding=dp(8), spacing=dp(8),
                             bg_color=theme.input_bg,
                             border_color=theme.input_bg, radius=dp(10))
            row.add_widget(EmojiLabel(text=care["icon"], size_hint_x=None, width=dp(24), font_size="14sp"))
            info = BoxLayout(orientation="vertical")
            info.add_widget(Label(text=name, bold=True, font_size="12sp", color=theme.text, halign="left"))
            info.add_widget(Label(text=f"{month_name} {day}", font_size="10sp", color=theme.muted, halign="left"))
            row.add_widget(info)
            events_box.add_widget(row)

        scroll.add_widget(events_box)
        side.add_widget(scroll)
    else:
        side.add_widget(Label(text="No upcoming events.", font_size="12sp", color=theme.muted, halign="left"))

    split.add_widget(side)
    container.add_widget(split)


def _change_month(app, delta):
    month = _view["month"] + delta
    year = _view["year"]

    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1

    _view["month"] = month
    _view["year"] = year
    render_schedule(app)