# ===========================================================================
# Care Schedule Page View
# ===========================================================================

import calendar
from datetime import date, timedelta

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_color

from theme import theme

# The month the calendar is showing. Module-level so the < > buttons can
# change it and re-render. Starts on the current month.
_view = {"year": date.today().year, "month": date.today().month}


def _watering_days_this_month(app, year, month):
    """
    Returns a dict: { day_number: [plant_name, ...] }
    for every watering that falls in the given month.

    Projects each plant's next watering date forward by its interval,
    the same logic the dashboard uses for 'days until water'.
    """
    result = {}
    today = date.today()

    for plant in app.plants:
        days_until = plant.get("daysUntilWater", 0)
        interval = plant.get("watering_interval_days") or 7
        name = plant.get("name") or plant.get("nickname", "Plant")

        # First upcoming watering date, then repeat every `interval` days
        cursor = today + timedelta(days=days_until)
        month_end = date(year, month, calendar.monthrange(year, month)[1])

        # Don't loop forever on a bad interval
        if interval < 1:
            interval = 7

        while cursor <= month_end:
            if cursor.year == year and cursor.month == month:
                result.setdefault(cursor.day, []).append(name)
            cursor += timedelta(days=interval)

    return result


def render_schedule(app):
    """Renders the monthly care calendar and upcoming task list split-view."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    from main import RoundedBox, PillButton

    year = _view["year"]
    month = _view["month"]
    today = date.today()

    watering = _watering_days_this_month(app, year, month)

    # Header section
    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(text="Care Schedule", bold=True, font_size="30sp",
                            color=theme.text, halign="left",
                            size_hint_y=None, height=dp(40)))
    header.add_widget(Label(
        text=f"{len(app.plants)} plants \u00b7 watering, fertilizing & repotting schedule",
        font_size="12sp", color=theme.muted, halign="left",
        size_hint_y=None, height=dp(18)))
    container.add_widget(header)

    split = BoxLayout(size_hint_y=None, height=dp(380), spacing=dp(24))

    # Left side calendar view
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

    # Days of week column headers
    grid = GridLayout(cols=7, spacing=dp(4), padding=[0, dp(10)])
    for day in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
        grid.add_widget(Label(text=day, font_size="11sp", bold=True, color=theme.muted))

    # Real start-of-month offset. calendar.weekday(): Mon=0..Sun=6.
    # Our columns start on Sunday, so convert.
    first_weekday = (calendar.weekday(year, month, 1) + 1) % 7
    for _ in range(first_weekday):
        grid.add_widget(Widget())

    days_in_month = calendar.monthrange(year, month)[1]

    for day in range(1, days_in_month + 1):
        is_today = (day == today.day and month == today.month and year == today.year)
        has_watering = day in watering

        lbl = Label(text=str(day), color=theme.text, font_size="12sp",
                    bold=is_today)

        if is_today:
            box = RoundedBox(bg_color=theme.accent_soft, border_color=theme.accent_soft,
                             radius=dp(8))
            box.add_widget(lbl)
            grid.add_widget(box)
        elif has_watering:
            # Blue-tinted cell = a plant needs water that day
            box = RoundedBox(bg_color=theme.water_highlight,
                             border_color=theme.water_highlight, radius=dp(8))
            box.add_widget(lbl)
            grid.add_widget(box)
        else:
            grid.add_widget(lbl)

    cal_box.add_widget(grid)
    split.add_widget(cal_box)

    # Right side upcoming events panel
    side = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(220),
                     spacing=dp(10))
    side.add_widget(Label(text="Upcoming", bold=True, font_size="16sp",
                          color=theme.text, halign="left",
                          size_hint_y=None, height=dp(24)))

    # Build a sorted list of upcoming waterings for the current month
    events = []
    for day in sorted(watering.keys()):
        # Only show today and future days in the list
        cell_date = date(year, month, day)
        if cell_date >= today:
            for name in watering[day]:
                events.append((day, name))

    if events:
        scroll = ScrollView(do_scroll_x=False)
        events_box = BoxLayout(orientation="vertical", spacing=dp(8),
                               size_hint_y=None)
        events_box.bind(minimum_height=events_box.setter("height"))

        for day, name in events:
            row = RoundedBox(orientation="horizontal", size_hint_y=None,
                             height=dp(44), padding=dp(8), spacing=dp(8),
                             bg_color=theme.input_bg,
                             border_color=theme.input_bg, radius=dp(10))
            row.add_widget(Label(text="\U0001F4A7", size_hint_x=None, width=dp(24),
                                 font_size="14sp"))
            info = BoxLayout(orientation="vertical")
            info.add_widget(Label(text=name, bold=True, font_size="12sp",
                                  color=theme.text, halign="left"))
            info.add_widget(Label(text=f"{month_name} {day}", font_size="10sp",
                                  color=theme.muted, halign="left"))
            row.add_widget(info)
            events_box.add_widget(row)

        scroll.add_widget(events_box)
        side.add_widget(scroll)
    else:
        side.add_widget(Label(text="No upcoming events.", font_size="12sp",
                              color=theme.muted, halign="left"))

    split.add_widget(side)
    container.add_widget(split)


def _change_month(app, delta):
    """Move the calendar forward or back a month and re-render."""
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