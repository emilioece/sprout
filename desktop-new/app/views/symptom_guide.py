# ===========================================================================
# Symptom Guide Page View
# ===========================================================================

from components.widgets import SymptomRow, PillButton, RoundedBox
from components.utils import EMOJI_FONT
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_color

from theme import theme

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


    # Header
    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(text="Symptom Guide", bold=True, font_size="30sp", color=theme.text, halign="left", size_hint_y=None, height=dp(40)))
    header.add_widget(Label(text="Describe what you see -- we'll help you figure out what's wrong.", font_size="12sp", color=theme.muted, halign="left", size_hint_y=None, height=dp(18)))
    container.add_widget(header)

    # Search bar input
    ti = TextInput(
        hint_text="e.g. yellow leaves, drooping, brown tips, bugs...",
        background_normal="", background_active="",
        background_color=theme.surface, foreground_color=theme.text,
        padding=(dp(16), dp(12)), size_hint_y=None, height=dp(44)
    )
    container.add_widget(ti)

    # AI Health Check button (Gemini wiring TBD by teammate)
    health_btn = PillButton(
        text="\U0001F4F8  Health Check (AI)",
        size_hint_y=None, height=dp(48),
        bg_color=theme.dark_green, fg_color=[1, 1, 1, 1],
    )
    health_btn.bind(on_release=lambda *_: _open_health_check(app))
    container.add_widget(health_btn)

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


    # Selected symptom header
    header = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    header.add_widget(Label(text=symptom["icon"], font_name=EMOJI_FONT, font_size="28sp", size_hint_x=None, width=dp(36)))
    header.add_widget(Label(text=symptom["title"], bold=True, font_size="24sp", color=theme.text, halign="left"))
    container.add_widget(header)

    # Causes list section
    container.add_widget(Label(text="Possible causes", bold=True, font_size="16sp", color=theme.text, halign="left", size_hint_y=None, height=dp(24)))
    for cause_title, cause_desc in symptom["causes"]:
        card = RoundedBox(orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(60), bg_color=theme.surface, border_color=theme.border)
        card.add_widget(Label(text=cause_title, bold=True, font_size="13sp", color=theme.text, halign="left"))
        card.add_widget(Label(text=cause_desc, font_size="11sp", color=theme.muted2, halign="left"))
        container.add_widget(card)

    # Solutions section
    container.add_widget(Label(text="How to fix it", bold=True, font_size="16sp", color=theme.text, halign="left", size_hint_y=None, height=dp(24)))
    for fix_title, fix_desc in symptom["fixes"]:
        card = RoundedBox(orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(60), bg_color=theme.accent_soft, border_color=theme.accent_soft)
        card.add_widget(Label(text=fix_title, bold=True, font_size="13sp", color=theme.dark_green, halign="left"))
        card.add_widget(Label(text=fix_desc, font_size="11sp", color=theme.muted2, halign="left"))
        container.add_widget(card)


def _open_health_check(app):
    """Let the user pick a photo. AI diagnosis is wired in later."""
    from kivy.uix.filechooser import FileChooserIconView

    picker = ModalView(size_hint=(0.9, 0.9))
    box = RoundedBox(orientation="vertical", spacing=dp(10), padding=dp(10),
                     bg_color=theme.surface, border_color=theme.border)
    box.add_widget(Label(text="Pick a photo of your plant", bold=True,
                         font_size="16sp", color=theme.text,
                         size_hint_y=None, height=dp(30)))

    chooser = FileChooserIconView(filters=["*.jpg", "*.jpeg", "*.png"])
    box.add_widget(chooser)

    btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    cancel = PillButton(text="Cancel", bg_color=theme.input_bg,
                        fg_color=theme.muted2)
    cancel.bind(on_release=lambda *_: picker.dismiss())
    analyze = PillButton(text="Analyze", bg_color=theme.dark_green)

    def do_analyze(*_):
        if not chooser.selection:
            return
        path = chooser.selection[0]
        picker.dismiss()
        _show_result(app, path)

    analyze.bind(on_release=do_analyze)
    btn_row.add_widget(cancel)
    btn_row.add_widget(analyze)
    box.add_widget(btn_row)
    picker.add_widget(box)
    picker.open()


def _show_result(app, image_path):
    """Placeholder result. Teammate will replace this with the Gemini call."""
    from main import RoundedBox, PillButton

    modal = ModalView(size_hint=(None, None), size=(dp(360), dp(220)))
    box = RoundedBox(orientation="vertical", padding=dp(20), spacing=dp(12),
                     bg_color=theme.surface, border_color=theme.border)
    box.add_widget(Label(text="\U0001F33F  Health Check", bold=True,
                         font_size="18sp", color=theme.text,
                         size_hint_y=None, height=dp(30)))
    box.add_widget(Label(
        text="Photo received! AI diagnosis is coming soon.",
        font_size="13sp", color=theme.muted2, halign="center"))

    ok = PillButton(text="OK", bg_color=theme.dark_green, size_hint_y=None, height=dp(44))
    ok.bind(on_release=lambda *_: modal.dismiss())
    box.add_widget(ok)
    modal.add_widget(box)
    modal.open()