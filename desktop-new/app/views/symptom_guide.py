# ===========================================================================
# Symptom Guide Page View
# ===========================================================================

from components.widgets import SymptomRow, PillButton, RoundedBox
from components.utils import EMOJI_FONT, default_picture_dir
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_color

from theme import theme

import threading

import api
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView


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

    header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
    header.add_widget(Label(text="Symptom Guide", bold=True, font_size="30sp", color=theme.text, halign="left", size_hint_y=None, height=dp(40)))
    header.add_widget(Label(text="Describe what you see -- we'll help you figure out what's wrong.", font_size="12sp", color=theme.muted, halign="left", size_hint_y=None, height=dp(18)))
    container.add_widget(header)

    ti = TextInput(
        hint_text="e.g. yellow leaves, drooping, brown tips, bugs...",
        background_normal="", background_active="",
        background_color=theme.surface, foreground_color=theme.text,
        padding=(dp(16), dp(12)), size_hint_y=None, height=dp(44)
    )
    container.add_widget(ti)

    health_btn = PillButton(
        text="\U0001F4F8  Health Check (AI)",
        size_hint_y=None, height=dp(48),
        bg_color=theme.dark_green, fg_color=[1, 1, 1, 1],
    )
    health_btn.bind(on_release=lambda *_: _open_health_check(app))
    container.add_widget(health_btn)

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

    header = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    header.add_widget(Label(text=symptom["icon"], font_name=EMOJI_FONT, font_size="28sp", size_hint_x=None, width=dp(36)))
    header.add_widget(Label(text=symptom["title"], bold=True, font_size="24sp", color=theme.text, halign="left"))
    container.add_widget(header)

    container.add_widget(Label(text="Possible causes", bold=True, font_size="16sp", color=theme.text, halign="left", size_hint_y=None, height=dp(24)))
    for cause_title, cause_desc in symptom["causes"]:
        card = RoundedBox(orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(60), bg_color=theme.surface, border_color=theme.border)
        card.add_widget(Label(text=cause_title, bold=True, font_size="13sp", color=theme.text, halign="left"))
        card.add_widget(Label(text=cause_desc, font_size="11sp", color=theme.muted2, halign="left"))
        container.add_widget(card)

    container.add_widget(Label(text="How to fix it", bold=True, font_size="16sp", color=theme.text, halign="left", size_hint_y=None, height=dp(24)))
    for fix_title, fix_desc in symptom["fixes"]:
        card = RoundedBox(orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(60), bg_color=theme.accent_soft, border_color=theme.accent_soft)
        card.add_widget(Label(text=fix_title, bold=True, font_size="13sp", color=theme.dark_green, halign="left"))
        card.add_widget(Label(text=fix_desc, font_size="11sp", color=theme.muted2, halign="left"))
        container.add_widget(card)


def _open_health_check(app):
    from kivy.uix.filechooser import FileChooserIconView

    picker = ModalView(size_hint=(0.9, 0.9))
    box = RoundedBox(orientation="vertical", spacing=dp(10), padding=dp(10),
                     bg_color=theme.surface, border_color=theme.border)
    box.add_widget(Label(text="Pick a photo of your plant", bold=True,
                         font_size="16sp", color=theme.text,
                         size_hint_y=None, height=dp(30)))

    # start in the pictures folder instead of the c drive root
    chooser = FileChooserIconView(
        filters=["*.jpg", "*.jpeg", "*.png"],
        path=default_picture_dir(),
    )
    box.add_widget(chooser)

    btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    cancel = PillButton(text="Cancel", bg_color=theme.input_bg, fg_color=theme.muted2)
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
    """
    sends the photo to the backend for identification and shows what comes back

    the request goes on a background thread because a vision call takes a few
    seconds and kivy would freeze the window otherwise. the reply comes back
    through Clock so widgets are only ever touched from the main thread
    """
    modal = ModalView(size_hint=(0.75, 0.75))
    box = RoundedBox(orientation="vertical", padding=dp(20), spacing=dp(12),
                     bg_color=theme.surface, border_color=theme.border,
                     radius=dp(18))

    title = Label(text="Health Check", bold=True, font_size="18sp",
                  color=theme.text, size_hint_y=None, height=dp(30))
    box.add_widget(title)

    status = Label(text="Analyzing your photo...", font_size="13sp",
                   color=theme.muted2, halign="center", valign="middle")
    status.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
    box.add_widget(status)

    # the results get poured into here once they arrive
    scroll = ScrollView(size_hint=(1, 1))
    results = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None,
                        padding=(0, dp(4)))
    results.bind(minimum_height=results.setter("height"))
    scroll.add_widget(results)
    box.add_widget(scroll)

    close_btn = PillButton(text="Close", bg_color=theme.dark_green,
                           size_hint_y=None, height=dp(44))
    close_btn.bind(on_release=lambda *_: modal.dismiss())
    box.add_widget(close_btn)

    modal.add_widget(box)
    modal.open()

    def add_line(text, size="13sp", colour=None, bold=False):
        label = Label(text=text, font_size=size, bold=bold,
                      color=colour or theme.text,
                      halign="left", valign="top", size_hint_y=None)
        label.bind(
            width=lambda w, *_: setattr(w, "text_size", (w.width, None)),
            texture_size=lambda w, *_: setattr(w, "height", w.texture_size[1]),
        )
        results.add_widget(label)

    def on_result(data):
        status.text = ""
        status.size_hint_y = None
        status.height = 0

        if not data.get("is_plant", True):
            add_line("That does not look like a plant.", bold=True,
                     colour=theme.red)
            add_line("Try another photo with the plant filling more of the frame.",
                     colour=theme.muted2)
            return

        confidence = round(data.get("confidence", 0) * 100)
        add_line(data.get("species", "Unknown"), size="20sp", bold=True,
                 colour=theme.dark_green)
        add_line(f"{confidence}% confident", size="12sp", colour=theme.muted2)

        if data.get("light_requirement"):
            add_line("")
            add_line("Light", size="11sp", bold=True, colour=theme.muted2)
            add_line(data["light_requirement"])

        alternatives = data.get("alternatives") or []
        if alternatives:
            add_line("")
            add_line("It could also be", size="11sp", bold=True,
                     colour=theme.muted2)
            for alt in alternatives:
                pct = round(alt.get("confidence", 0) * 100)
                add_line(f"{alt.get('species', 'Unknown')}  ({pct}%)",
                         colour=theme.muted2)

    def on_error(message):
        status.text = ""
        status.size_hint_y = None
        status.height = 0

        # a 503 means the server is fine but nobody has set a gemini key,
        # which is a very different problem to the request failing
        if "503" in message:
            add_line("AI is not set up yet.", bold=True, colour=theme.red)
            add_line("A GEMINI_API_KEY needs to be added to the .env file "
                     "in the project root.", colour=theme.muted2)
        elif "400" in message:
            add_line("That file type is not supported.", bold=True,
                     colour=theme.red)
            add_line("Use a JPEG, PNG or WebP image.", colour=theme.muted2)
        else:
            add_line("Could not analyze the photo.", bold=True, colour=theme.red)
            add_line(message, size="11sp", colour=theme.muted2)

    def worker():
        try:
            data = api.identify_plant(image_path)
            Clock.schedule_once(lambda dt, d=data: on_result(d))
        except Exception as exc:
            Clock.schedule_once(lambda dt, e=str(exc): on_error(e))

    threading.Thread(target=worker, daemon=True).start()