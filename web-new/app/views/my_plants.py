# ===========================================================================
# My Plants Page View
# ===========================================================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_color

COLOR_DARKEST = hex_color("#1E2A20")
COLOR_MUTED = hex_color("#788177")
COLOR_DARK_GREEN = hex_color("#284E36")
COLOR_BORDER = hex_color("#E5E3DC")

def render_my_plants(app):
    """Renders the plant collection grid view with search and filter pills."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    from main import PillButton, EMOJI_FONT

    # Header section
    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(
        text="My Plants", bold=True, font_size="28sp",
        color=COLOR_DARKEST, halign="left", size_hint_y=None, height=dp(36),
        text_size=(container.width if container.width > 0 else dp(600), None)
    ))
    header.add_widget(Label(
        text=f"{len(app.plants)} plants growing happily", font_size="13sp",
        color=COLOR_MUTED, halign="left", size_hint_y=None, height=dp(20),
        text_size=(container.width if container.width > 0 else dp(600), None)
    ))
    container.add_widget(header)

    # Search bar input box
    search_box = BoxLayout(size_hint_y=None, height=dp(42), size_hint_x=None, width=dp(380))
    ti = TextInput(
        hint_text="Search by name, species, or location...",
        multiline=False,
        background_normal="", background_active="",
        background_color=hex_color("#FFFFFF"),
        foreground_color=COLOR_DARKEST,
        hint_text_color=hex_color("#9A9E97"),
        cursor_color=COLOR_DARK_GREEN,
        padding=(dp(16), dp(11)),
        size_hint=(1, 1)
    )
    search_box.add_widget(ti)
    container.add_widget(search_box)

    # Filter tags row
    pills = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(10))
    pills.add_widget(PillButton(text="All plants", bg_color=COLOR_DARK_GREEN, fg_color=[1, 1, 1, 1], radius=dp(17), size_hint_x=None, width=dp(95)))
    pills.add_widget(PillButton(text="Needs water", bg_color=hex_color("#EBE8DF"), fg_color=COLOR_DARKEST, radius=dp(17), size_hint_x=None, width=dp(115)))
    pills.add_widget(PillButton(text="Beginner-friendly", bg_color=hex_color("#EBE8DF"), fg_color=COLOR_DARKEST, radius=dp(17), size_hint_x=None, width=dp(140)))
    pills.add_widget(PillButton(text="Low light", bg_color=hex_color("#EBE8DF"), fg_color=COLOR_DARKEST, radius=dp(17), size_hint_x=None, width=dp(95)))
    container.add_widget(pills)

    # Horizontal divider line
    divider = Widget(size_hint_y=None, height=dp(1))
    with divider.canvas:
        from kivy.graphics import Color, Rectangle
        Color(rgba=COLOR_BORDER)
        Rectangle(pos=divider.pos, size=(dp(2000), dp(1)))
    container.add_widget(divider)

    # Empty state vs populated plant list state
    if not app.plants:
        empty_wrapper = BoxLayout(orientation="vertical", spacing=dp(16), size_hint_y=None, height=dp(350), padding=[0, dp(60), 0, 0])
        empty_wrapper.add_widget(Label(
            text="\U0001F335", font_name=EMOJI_FONT, font_size="52sp",
            size_hint_y=None, height=dp(60)
        ))
        empty_wrapper.add_widget(Label(
            text="No plants yet. Add your first one!", font_size="14sp",
            color=COLOR_MUTED, size_hint_y=None, height=dp(24)
        ))
        add_btn = PillButton(
            text="Add your first plant", bg_color=COLOR_DARK_GREEN,
            fg_color=[1, 1, 1, 1], radius=dp(14),
            size_hint=(None, None), size=(dp(180), dp(44)),
            pos_hint={"center_x": 0.5}
        )
        add_btn.bind(on_release=lambda *_: app.open_add_modal())
        empty_wrapper.add_widget(add_btn)
        container.add_widget(empty_wrapper)
    else:
        from main import PlantRow
        list_box = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        list_box.bind(minimum_height=list_box.setter("height"))

        for plant in app.plants:
            name = plant.get("name") or plant.get("nickname", "")
            row = PlantRow(
                plant_id=plant.get("id"),
                plant_name=name,
                subtitle=plant.get("location") or plant.get("species") or "Unspecified",
                initials=(name[:4] if name else ""),
                due_label=f"In {plant.get('daysUntilWater', 0)}d",
            )
            row.on_water_cb = app.water_plant
            row.on_delete_cb = app.open_delete_modal
            list_box.add_widget(row)

        container.add_widget(list_box)