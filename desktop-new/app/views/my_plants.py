# ===========================================================================
# My Plants Page View
# ===========================================================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.metrics import dp

from theme import theme
from components.widgets import PillButton, PlantRow, EmojiLabel

def render_my_plants(app):
    """Renders the plant collection grid view with search and filter pills."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    # Header section
    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(
        text="My Plants", bold=True, font_size="28sp",
        color=theme.text, halign="left", size_hint_y=None, height=dp(36),
        text_size=(container.width if container.width > 0 else dp(600), None)
    ))
    header.add_widget(Label(
        text=f"{len(app.plants)} plants growing happily", font_size="13sp",
        color=theme.muted, halign="left", size_hint_y=None, height=dp(20),
        text_size=(container.width if container.width > 0 else dp(600), None)
    ))
    container.add_widget(header)

    # Search bar input box
    search_box = BoxLayout(size_hint_y=None, height=dp(42), size_hint_x=None, width=dp(380))
    ti = TextInput(
        hint_text="Search by name, species, or location...",
        multiline=False,
        background_normal="", background_active="",
        background_color=theme.surface,
        foreground_color=theme.text,
        hint_text_color=theme.hint,
        cursor_color=theme.dark_green,
        padding=(dp(16), dp(11)),
        size_hint=(1, 1)
    )
    search_box.add_widget(ti)
    container.add_widget(search_box)

    # Filter tags row
    pills = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(10))
    pills.add_widget(PillButton(text="All plants", bg_color=theme.dark_green, fg_color=[1, 1, 1, 1], radius=dp(17), size_hint_x=None, width=dp(95)))
    pills.add_widget(PillButton(text="Needs water", bg_color=theme.pill_inactive, fg_color=theme.text, radius=dp(17), size_hint_x=None, width=dp(115)))
    pills.add_widget(PillButton(text="Beginner-friendly", bg_color=theme.pill_inactive, fg_color=theme.text, radius=dp(17), size_hint_x=None, width=dp(140)))
    pills.add_widget(PillButton(text="Low light", bg_color=theme.pill_inactive, fg_color=theme.text, radius=dp(17), size_hint_x=None, width=dp(95)))
    container.add_widget(pills)

    # Horizontal divider line
    divider = Widget(size_hint_y=None, height=dp(1))
    with divider.canvas:
        from kivy.graphics import Color, Rectangle
        Color(rgba=theme.border)
        Rectangle(pos=divider.pos, size=(dp(2000), dp(1)))
    container.add_widget(divider)

    # Empty state vs populated plant list state
    if not app.plants:
        empty_wrapper = BoxLayout(orientation="vertical", spacing=dp(16), size_hint_y=None, height=dp(350), padding=[0, dp(60), 0, 0])

        # EmojiLabel automatically handles NotoColorEmoji if registered
        empty_wrapper.add_widget(EmojiLabel(
            text="\U0001F335",
            font_size="52sp",
            size_hint_y=None,
            height=dp(60)
        ))
        empty_wrapper.add_widget(Label(
            text="No plants yet. Add your first one!", font_size="14sp",
            color=theme.muted, size_hint_y=None, height=dp(24)
        ))
        add_btn = PillButton(
            text="Add your first plant", bg_color=theme.dark_green,
            fg_color=[1, 1, 1, 1], radius=dp(14),
            size_hint=(None, None), size=(dp(180), dp(44)),
            pos_hint={"center_x": 0.5}
        )
        add_btn.bind(on_release=lambda *_: app.open_add_modal())
        empty_wrapper.add_widget(add_btn)
        container.add_widget(empty_wrapper)
    else:
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