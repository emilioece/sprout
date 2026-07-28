# ===========================================================================
# Care Schedule Page View
# ===========================================================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_color

COLOR_DARKEST = hex_color("#1E2A20")
COLOR_MUTED = hex_color("#788177")
COLOR_BORDER = hex_color("#E5E3DC")
COLOR_CARD_GREEN = hex_color("#E9EEE6")

def render_schedule(app):
    """Renders the monthly care calendar and upcoming task list split-view."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    from main import RoundedBox, PillButton

    # Header section
    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(text="Care Schedule", bold=True, font_size="30sp", color=COLOR_DARKEST, halign="left", size_hint_y=None, height=dp(40)))
    header.add_widget(Label(text=f"{len(app.plants)} plants \u00b7 watering, fertilizing & repotting schedule", font_size="12sp", color=COLOR_MUTED, halign="left", size_hint_y=None, height=dp(18)))
    container.add_widget(header)

    split = BoxLayout(size_hint_y=None, height=dp(380), spacing=dp(24))

    # Left side calendar view
    cal_box = RoundedBox(orientation="vertical", padding=dp(16), bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER)
    cal_header = BoxLayout(size_hint_y=None, height=dp(30))
    cal_header.add_widget(PillButton(text="<", size_hint=(None, None), size=(dp(30), dp(30)), bg_color=hex_color("#EFECE6"), fg_color=COLOR_DARKEST))
    cal_header.add_widget(Label(text="July 2026", bold=True, color=COLOR_DARKEST, font_size="16sp"))
    cal_header.add_widget(PillButton(text=">", size_hint=(None, None), size=(dp(30), dp(30)), bg_color=hex_color("#EFECE6"), fg_color=COLOR_DARKEST))
    cal_box.add_widget(cal_header)

    # Days of week column headers
    grid = GridLayout(cols=7, spacing=dp(4), padding=[0, dp(10)])
    for day in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
        grid.add_widget(Label(text=day, font_size="11sp", bold=True, color=COLOR_MUTED))

    # Spacer offset widgets for calendar start day
    for _ in range(3):
        grid.add_widget(Widget())

    # Build calendar day numbers (1 to 31)
    for day in range(1, 32):
        lbl = Label(text=str(day), color=COLOR_DARKEST, font_size="12sp", bold=(day == 25))
        if day == 25:
            # Highlight current day (e.g. 25th)
            box = RoundedBox(bg_color=COLOR_CARD_GREEN, border_color=COLOR_CARD_GREEN, radius=dp(8))
            box.add_widget(lbl)
            grid.add_widget(box)
        else:
            grid.add_widget(lbl)

    cal_box.add_widget(grid)
    split.add_widget(cal_box)

    # Right side upcoming events panel
    side = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(220), spacing=dp(10))
    side.add_widget(Label(text="Upcoming", bold=True, font_size="16sp", color=COLOR_DARKEST, halign="left", size_hint_y=None, height=dp(24)))
    side.add_widget(Label(text="No upcoming events.", font_size="12sp", color=COLOR_MUTED, halign="left"))
    split.add_widget(side)

    container.add_widget(split)