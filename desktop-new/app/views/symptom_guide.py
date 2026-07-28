# ===========================================================================
# Symptom Guide Page View
# ===========================================================================

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_color

COLOR_DARKEST = hex_color("#1E2A20")
COLOR_MUTED = hex_color("#788177")
COLOR_MUTED2 = hex_color("#616C60")
COLOR_BORDER = hex_color("#E5E3DC")
COLOR_CARD_GREEN = hex_color("#E9EEE6")
COLOR_DARK_GREEN = hex_color("#284E36")

# Mock database of plant diagnostic symptoms, causes, and step-by-step remedies
SYMPTOMS_DATA = [
    {
        "id": "yellow_leaves",
        "title": "Yellow leaves",
        "icon": "\U0001F7E1",
        "urgency_text": "Moderate urgency",
        "urgency_color": hex_color("#B45309"),
        "urgency_bg": hex_color("#FEF3C7"),
        "causes": [
            ("1. Overwatering", "Roots are suffocated by excess moisture."),
            ("2. Underwatering", "Plant is drawing moisture back from older leaves."),
        ],
        "fixes": [
            ("1. Adjust watering cycle", "Allow top inch of soil to dry out."),
            ("2. Check drainage", "Ensure pot has bottom drainage holes."),
        ]
    },
    {
        "id": "drooping",
        "title": "Drooping / wilting",
        "icon": "\U0001F613",
        "urgency_text": "Urgent",
        "urgency_color": hex_color("#991B1B"),
        "urgency_bg": hex_color("#FEE2E2"),
        "causes": [
            ("1. Underwatered", "Plant cells lose turgor pressure when dehydrated."),
            ("2. Root rot", "Damaged roots cannot absorb water even if soil is wet."),
            ("3. Too much direct sun", "Intense heat causes rapid water loss."),
            ("4. Root-bound", "A pot-bound plant exhausts its water supply quickly."),
        ],
        "fixes": [
            ("1. Water immediately", "If soil is dry, water thoroughly until it drains."),
            ("2. Check for root rot", "If watered and wilting, unpot to inspect roots."),
            ("3. Move from direct sun", "Shift to a shade spot during peak hours."),
            ("4. Consider repotting", "If roots circle the pot, size up one pot size."),
        ]
    },
    {
        "id": "brown_tips",
        "title": "Brown leaf tips",
        "icon": "\U0001F342",
        "urgency_text": "Low urgency",
        "urgency_color": hex_color("#15803D"),
        "urgency_bg": hex_color("#DCFCE7"),
        "causes": [
            ("1. Low humidity", "Dry air causes tip crisping."),
            ("2. Tap water minerals", "Chemicals build up in leaf margins."),
        ],
        "fixes": [
            ("1. Increase humidity", "Group plants together or use a humidifier."),
            ("2. Use filtered water", "Let tap water sit overnight before using."),
        ]
    },
]

def render_symptom_guide(app):
    """Renders the symptom list view with search box."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    from main import SymptomRow

    # Header
    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(text="Symptom Guide", bold=True, font_size="30sp", color=COLOR_DARKEST, halign="left", size_hint_y=None, height=dp(40)))
    header.add_widget(Label(text="Describe what you see -- we'll help you figure out what's wrong.", font_size="12sp", color=COLOR_MUTED, halign="left", size_hint_y=None, height=dp(18)))
    container.add_widget(header)

    # Search bar input
    ti = TextInput(
        hint_text="e.g. yellow leaves, drooping, brown tips, bugs...",
        background_normal="", background_active="",
        background_color=hex_color("#FFFFFF"), foreground_color=COLOR_DARKEST,
        padding=(dp(16), dp(12)), size_hint_y=None, height=dp(44)
    )
    container.add_widget(ti)

    # List of symptom cards
    list_box = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
    list_box.bind(minimum_height=list_box.setter("height"))

    for data in SYMPTOMS_DATA:
        row = SymptomRow(
            icon=data["icon"],
            title=data["title"],
            urgency_text=data["urgency_text"],
            urgency_color=data["urgency_color"],
            urgency_bg=data["urgency_bg"]
        )
        def make_cb(d=data):
            def _cb(*_):
                app.active_symptom = d
                render_symptom_detail(app, d)
            return _cb
        row.bind(on_release=make_cb())
        list_box.add_widget(row)

    container.add_widget(list_box)

def render_symptom_detail(app, symptom):
    """Renders the detailed cause & resolution view for a selected symptom."""
    container = app.root_layout.ids.main_content
    container.clear_widgets()

    from main import RoundedBox, EMOJI_FONT

    # Selected symptom header
    header = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    header.add_widget(Label(text=symptom["icon"], font_name=EMOJI_FONT, font_size="28sp", size_hint_x=None, width=dp(36)))
    header.add_widget(Label(text=symptom["title"], bold=True, font_size="24sp", color=COLOR_DARKEST, halign="left"))
    container.add_widget(header)

    # Causes list section
    container.add_widget(Label(text="Possible causes", bold=True, font_size="16sp", color=COLOR_DARKEST, halign="left", size_hint_y=None, height=dp(24)))
    for cause_title, cause_desc in symptom["causes"]:
        card = RoundedBox(orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(60), bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER)
        card.add_widget(Label(text=cause_title, bold=True, font_size="13sp", color=COLOR_DARKEST, halign="left"))
        card.add_widget(Label(text=cause_desc, font_size="11sp", color=COLOR_MUTED2, halign="left"))
        container.add_widget(card)

    # Solutions section
    container.add_widget(Label(text="How to fix it", bold=True, font_size="16sp", color=COLOR_DARKEST, halign="left", size_hint_y=None, height=dp(24)))
    for fix_title, fix_desc in symptom["fixes"]:
        card = RoundedBox(orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(60), bg_color=COLOR_CARD_GREEN, border_color=COLOR_CARD_GREEN)
        card.add_widget(Label(text=fix_title, bold=True, font_size="13sp", color=COLOR_DARK_GREEN, halign="left"))
        card.add_widget(Label(text=fix_desc, font_size="11sp", color=COLOR_MUTED2, halign="left"))
        container.add_widget(card)