# ===========================================================================
# Sprout Desktop Application - Main Entry Point
# ===========================================================================

import os
import sys
import platform
import threading

# Guarantee Python finds the local views folder regardless of run directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex as hex_color

import api
from views.dashboard import render_dashboard
from views.my_plants import render_my_plants
from views.schedule import render_schedule
from views.symptom_guide import render_symptom_guide, render_symptom_detail


def _register_emoji_font():
    """Detects system font paths to register system emoji fonts across macOS, Windows, and Linux."""
    local_override = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "emoji_font.ttf"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "emoji_font.ttc"),
    ]
    system = platform.system()
    if system == "Darwin":
        system_candidates = ["/System/Library/Fonts/Apple Color Emoji.ttc"]
    elif system == "Windows":
        system_candidates = ["C:/Windows/Fonts/seguiemj.ttf", "C:/Windows/Fonts/Seguiemj.ttf"]
    else:
        system_candidates = [
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/noto-emoji/NotoColorEmoji.ttf",
        ]

    for path in local_override + system_candidates:
        if os.path.exists(path):
            try:
                LabelBase.register(name="EmojiFont", fn_regular=path)
                return "EmojiFont"
            except Exception:
                continue
    return None


EMOJI_FONT = _register_emoji_font()

# Global Color Palette Definitions
COLOR_DARK_GREEN = hex_color("#284E36")
COLOR_DARKEST = hex_color("#1E2A20")
COLOR_MUTED = hex_color("#788177")
COLOR_MUTED2 = hex_color("#616C60")
COLOR_BORDER = hex_color("#E5E3DC")
COLOR_RED = hex_color("#DC2626")

# Sample species choices for Step 1 of adding a plant
QUICK_SPECIES = [
    ("Fern", "\U0001F33F", "easy \u00b7 indirect"),
    ("Moss", "\U0001F343", "easy \u00b7 low light"),
    ("Cactus", "\U0001F331", "expert \u00b7 indirect"),
    ("Bamboo", "\U0001F33E", "easy \u00b7 low light"),
]


class EmojiLabel(Label):
    """Simple EmojiLabel relying on standard font_size scaling."""
    def __init__(self, **kwargs):
        if EMOJI_FONT:
            kwargs["font_name"] = EMOJI_FONT
        super().__init__(**kwargs)


class RoundedBox(BoxLayout):
    bg_color = ListProperty(hex_color("#FFFFFF"))
    radius = NumericProperty(dp(16))
    border_color = ListProperty(hex_color("#E5E3DC"))
    border_width = NumericProperty(1)


class PillButton(Button):
    bg_color = ListProperty(COLOR_DARK_GREEN)
    fg_color = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(dp(14))


class SideNavItem(BoxLayout):
    icon = StringProperty("")
    text = StringProperty("")
    bg_color = ListProperty([0, 0, 0, 0])
    fg_color = ListProperty(COLOR_DARKEST)


class StatCard(RoundedBox):
    icon = StringProperty("")
    value = StringProperty("0")
    label_text = StringProperty("")


class PlantRow(RoundedBox):
    plant_id = ObjectProperty(None)
    plant_name = StringProperty("")
    subtitle = StringProperty("")
    initials = StringProperty("")
    due_label = StringProperty("")
    on_water_cb = None
    on_delete_cb = None

    def on_water(self):
        if self.on_water_cb:
            self.on_water_cb(self.plant_id)

    def on_delete(self):
        if self.on_delete_cb:
            self.on_delete_cb(self.plant_id, self.plant_name)


class SymptomRow(ButtonBehavior, RoundedBox):
    icon = StringProperty("")
    title = StringProperty("")
    subtitle = StringProperty("4 possible causes \u00b7 4 fixes")
    urgency_text = StringProperty("")
    urgency_color = ListProperty([0, 0, 0, 1])
    urgency_bg = ListProperty([1, 1, 1, 1])


class RootLayout(BoxLayout):
    plant_count_label = StringProperty("0 plants in collection")


class IconButtonRow(ButtonBehavior, RoundedBox):
    icon = StringProperty("")
    label_text = StringProperty("")
    fg_color = ListProperty(COLOR_DARKEST)


class SelectableCard(ButtonBehavior, RoundedBox):
    pass


class IconRow(BoxLayout):
    def __init__(self, icon="", text="", text_color=None, bold=True,
                 icon_size="12sp", text_size="11sp", icon_width=dp(20),
                 halign="left", **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        icon_lbl = EmojiLabel(
            text=icon,
            font_size=icon_size,
            size_hint=(None, None),
            size=(icon_width, dp(20)),
            pos_hint={"center_y": 0.5}
        )
        text_lbl = Label(text=text, font_size=text_size, bold=bold,
                         color=text_color or COLOR_DARKEST, halign=halign,
                         valign="middle")
        text_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        self.add_widget(icon_lbl)
        self.add_widget(text_lbl)


class AddPlantModal(ModalView):
    """Two-step modal window for adding a new plant."""
    def __init__(self, on_saved, **kwargs):
        width = min(dp(480), Window.width * 0.92)
        height = min(dp(620), Window.height * 0.9)
        super().__init__(size_hint=(None, None), size=(width, height), auto_dismiss=False, **kwargs)
        self.on_saved = on_saved
        self.species = ""
        self.nickname_input = None
        self.location_input = None
        self.step = 1
        self._build_step_1()

    def _header(self, title, subtitle, show_back=False):
        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8), padding=(dp(4), 0))
        if show_back:
            back_btn = PillButton(text="<", size_hint=(None, None), size=(dp(32), dp(32)), bg_color=hex_color("#EFECE6"), fg_color=COLOR_MUTED2, radius=dp(16))
            back_btn.bind(on_release=lambda *_: self._build_step_1())
            header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical")
        title_lbl = Label(text=title, bold=True, font_size="18sp", color=COLOR_DARKEST, halign="left", valign="bottom")
        title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        sub_lbl = Label(text=subtitle, font_size="11sp", color=COLOR_MUTED, halign="left", valign="top")
        sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        title_box.add_widget(title_lbl)
        title_box.add_widget(sub_lbl)
        header.add_widget(title_box)

        close_btn = PillButton(text="X", size_hint=(None, None), size=(dp(32), dp(32)), bg_color=hex_color("#EFECE6"), fg_color=COLOR_MUTED2, radius=dp(16))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        header.add_widget(close_btn)
        return header

    def _labeled_input(self, label_text, placeholder="", multiline=False):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(74) if multiline else dp(54), spacing=dp(4))
        if label_text:
            lbl = Label(text=label_text, font_size="11sp", bold=True, color=COLOR_MUTED2, size_hint_y=None, height=dp(16), halign="left")
            lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            box.add_widget(lbl)

        ti = TextInput(
            hint_text=placeholder, multiline=multiline, background_normal="", background_active="",
            background_disabled_normal="", background_color=hex_color("#F6F5F0"),
            foreground_color=COLOR_DARKEST, hint_text_color=hex_color("#9A9E97"),
            cursor_color=COLOR_DARK_GREEN, padding=(dp(14), dp(10)),
            size_hint_y=None, height=dp(40) if not multiline else dp(50)
        )
        box.add_widget(ti)
        return box, ti

    def _build_step_1(self):
        """Step 1: Choose plant species."""
        self.step = 1
        self.clear_widgets()

        root = RoundedBox(orientation="vertical", bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER, radius=dp(20), padding=dp(20))
        root.add_widget(self._header("Identify your plant", "Step 1 of 2"))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, dp(10), 0, dp(10)])
        body.bind(minimum_height=body.setter("height"))

        tab_bar = RoundedBox(orientation="horizontal", size_hint_y=None, height=dp(42), padding=dp(3), spacing=dp(2), bg_color=hex_color("#ECE9E1"), border_color=hex_color("#ECE9E1"), radius=dp(12))
        search_tab = IconButtonRow(icon="\U0001F50D", label_text="Search", bg_color=COLOR_DARK_GREEN, fg_color=[1, 1, 1, 1], radius=dp(10))
        photo_tab = IconButtonRow(icon="\U0001F4F7", label_text="Photo", bg_color=[0, 0, 0, 0], fg_color=COLOR_MUTED2, radius=dp(10))
        describe_tab = IconButtonRow(icon="\U0001F4AC", label_text="Describe", bg_color=[0, 0, 0, 0], fg_color=COLOR_MUTED2, radius=dp(10))

        tab_bar.add_widget(search_tab)
        tab_bar.add_widget(photo_tab)
        tab_bar.add_widget(describe_tab)
        body.add_widget(tab_bar)

        search_box, search_input = self._labeled_input("", "e.g. fern, moss, cactus...")
        search_input.text = self.species
        body.add_widget(search_box)

        for name, icon, tags in QUICK_SPECIES:
            is_selected = (self.species == name)

            card = SelectableCard(
                size_hint_y=None, height=dp(64),
                padding=[dp(14), dp(10)], spacing=dp(12),
                bg_color=hex_color("#E8EFE6") if is_selected else hex_color("#F5F3ED"),
                border_color=COLOR_DARK_GREEN if is_selected else hex_color("#F5F3ED"),
                border_width=1.5 if is_selected else 0,
                radius=dp(16)
            )

            icon_lbl = EmojiLabel(
                text=icon,
                font_size="1sp",
                size_hint=(None, None), size=(dp(24), dp(24)),
                pos_hint={"center_y": 0.5}
            )
            card.add_widget(icon_lbl)

            text_box = BoxLayout(orientation="vertical", spacing=dp(2))
            title_lbl = Label(text=name, bold=True, font_size="14sp", color=COLOR_DARKEST, halign="left", valign="bottom")
            title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

            sub_lbl = Label(text=tags, font_size="11sp", color=COLOR_MUTED, halign="left", valign="top")
            sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

            text_box.add_widget(title_lbl)
            text_box.add_widget(sub_lbl)
            card.add_widget(text_box)

            def make_cb(n=name):
                def _cb(*_):
                    self.species = n
                    search_input.text = n
                    self._build_step_1()
                return _cb

            card.bind(on_release=make_cb())
            body.add_widget(card)

        scroll.add_widget(body)
        root.add_widget(scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(54), padding=[0, dp(8), 0, 0])
        continue_btn = PillButton(text="Continue ->", bg_color=COLOR_DARK_GREEN if self.species else hex_color("#A8BBA2"), radius=dp(14))

        def go_next(*_):
            self.species = search_input.text.strip() or self.species
            if self.species:
                self._build_step_2()

        continue_btn.bind(on_release=go_next)
        footer.add_widget(continue_btn)
        root.add_widget(footer)

        self.add_widget(root)

    def _build_step_2(self):
        """Step 2: Input nickname, location, notes, and view auto-filled care schedule."""
        self.step = 2
        self.clear_widgets()

        root = RoundedBox(orientation="vertical", bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER, radius=dp(20), padding=dp(20))
        root.add_widget(self._header("Plant details", "Step 2 of 2", show_back=True))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, dp(10), 0, dp(10)])
        body.bind(minimum_height=body.setter("height"))

        # Top summary banner
        summary = RoundedBox(orientation="horizontal", size_hint_y=None, height=dp(56),
                             padding=[dp(14), dp(10)], spacing=dp(12),
                             bg_color=hex_color("#E9EEE6"), border_color=hex_color("#E9EEE6"),
                             radius=dp(14))

        icon_lbl = EmojiLabel(
            text="\U0001F335" if self.species == "Cactus" else "\U0001F33F",
            font_size="1sp",
            size_hint=(None, None), size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5}
        )
        summary.add_widget(icon_lbl)

        summary_text = BoxLayout(orientation="vertical", spacing=dp(2))
        title_lbl = Label(text=self.species, bold=True, font_size="14sp",
                          color=COLOR_DARK_GREEN, halign="left", valign="bottom")
        title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

        sub_lbl = Label(text="Care data auto-filled \u00b7 easy", font_size="11sp",
                        color=COLOR_MUTED2, halign="left", valign="top")
        sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

        summary_text.add_widget(title_lbl)
        summary_text.add_widget(sub_lbl)
        summary.add_widget(summary_text)
        body.add_widget(summary)

        # Photo placeholder box
        photo_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), spacing=dp(4))
        photo_lbl = Label(text="Plant photo", font_size="11sp", bold=True, color=COLOR_MUTED2, size_hint_y=None, height=dp(16), halign="left")
        photo_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        photo_box.add_widget(photo_lbl)

        photo_area = RoundedBox(
            bg_color=hex_color("#E8EFE6"), border_color=hex_color("#E8EFE6"),
            radius=dp(14), size_hint_y=None, height=dp(80)
        )
        add_photo_btn = PillButton(
            text="+ Add photo", bg_color=[0, 0, 0, 0], fg_color=COLOR_DARK_GREEN,
            font_size="12sp"
        )
        photo_area.add_widget(add_photo_btn)
        photo_box.add_widget(photo_area)
        body.add_widget(photo_box)

        # Text inputs
        nick_box, nick_input = self._labeled_input("Nickname *", "e.g. Big Leaf, Monty, Corner Plant")
        nick_input.text = self.species
        self.nickname_input = nick_input
        body.add_widget(nick_box)

        loc_box, loc_input = self._labeled_input("Location in home", "e.g. Living room window, Bedroom shelf")
        self.location_input = loc_input
        body.add_widget(loc_box)

        # Care schedule information panel
        schedule = RoundedBox(orientation="vertical", size_hint_y=None, height=dp(105),
                              padding=dp(12), spacing=dp(6),
                              bg_color=hex_color("#F5F3ED"), border_color=hex_color("#F5F3ED"),
                              radius=dp(14))

        sched_title = Label(text="Auto-filled care schedule", bold=True, font_size="11sp",
                            color=COLOR_DARKEST, halign="left", size_hint_y=None, height=dp(16))
        sched_title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        schedule.add_widget(sched_title)

        schedule_items = [
            ("\U0001F4A7", "Watering", "Every 7 days"),
            ("\U0001F33F", "Fertilizing", "Every 30 days"),
            ("\U0001FAB4", "Repotting", "Every 12 months"),
        ]

        for icon, name, freq in schedule_items:
            row = BoxLayout(size_hint_y=None, height=dp(20))

            item_box = BoxLayout(orientation="horizontal", spacing=dp(6))
            ic_lbl = EmojiLabel(
                text=icon,
                font_size="1sp",
                size_hint=(None, None), size=(dp(16), dp(16)),
                pos_hint={"center_y": 0.5}
            )
            nm_lbl = Label(text=name, font_size="11sp", color=COLOR_MUTED2, halign="left", valign="middle")
            nm_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            item_box.add_widget(ic_lbl)
            item_box.add_widget(nm_lbl)

            row.add_widget(item_box)

            freq_lbl = Label(text=freq, font_size="11sp", color=COLOR_DARKEST, halign="right", valign="middle")
            freq_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            row.add_widget(freq_lbl)
            schedule.add_widget(row)

        body.add_widget(schedule)

        notes_box, notes_input = self._labeled_input("Notes (optional)", "Any quirks about this specific plant?", multiline=True)
        body.add_widget(notes_box)

        scroll.add_widget(body)
        root.add_widget(scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(54), padding=[0, dp(8), 0, 0])
        self.save_btn = PillButton(text="Add to my collection", bg_color=COLOR_DARK_GREEN, radius=dp(14))
        self.save_btn.bind(on_release=lambda *_: self._save())
        footer.add_widget(self.save_btn)
        root.add_widget(footer)

        self.add_widget(root)

    def _save(self):
        """Sends new plant payload to the API server in a background thread."""
        nickname = self.nickname_input.text.strip()
        if not nickname:
            return
        location = self.location_input.text.strip()
        species = self.species

        self.save_btn.text = "Adding..."
        self.save_btn.disabled = True

        def worker():
            try:
                plant = api.create_plant(nickname, species, location)
                Clock.schedule_once(lambda dt, p=plant: self._on_success(p))
            except Exception as exc:
                # Capture exc object in lambda parameter err to avoid NameError
                Clock.schedule_once(lambda dt, err=exc: self._on_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, plant):
        self.dismiss()
        if self.on_saved:
            self.on_saved(plant)

    def _on_error(self, exc):
        self.save_btn.text = "Add to my collection"
        self.save_btn.disabled = False
        ErrorModal("Could not save plant.").open()


class DeleteConfirmModal(ModalView):
    """Confirmation modal shown before removing a plant."""
    def __init__(self, plant_id, plant_name, on_deleted, **kwargs):
        width = min(dp(360), Window.width * 0.9)
        height = min(dp(280), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), auto_dismiss=False, **kwargs)
        self.plant_id = plant_id
        self.on_deleted = on_deleted

        root = RoundedBox(orientation="vertical", padding=dp(20), spacing=dp(12), bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER, radius=dp(20))
        root.add_widget(EmojiLabel(
            text="\U0001F5D1",
            font_size="16sp",
            size_hint=(None, None), size=(dp(24), dp(24)),
            pos_hint={"center_x": 0.5}
        ))
        root.add_widget(Label(text=f"Remove {plant_name}?", bold=True, font_size="16sp", color=COLOR_DARKEST, size_hint_y=None, height=dp(28)))
        root.add_widget(Label(text="Are you sure you want to delete this plant?", font_size="11sp", color=COLOR_MUTED2, size_hint_y=None, height=dp(50)))

        btn_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(46))
        cancel_btn = PillButton(text="Cancel", bg_color=hex_color("#F6F5F0"), fg_color=COLOR_MUTED2, radius=dp(16))
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        self.delete_btn = PillButton(text="Delete Plant", bg_color=COLOR_RED, radius=dp(16))
        self.delete_btn.bind(on_release=lambda *_: self._confirm())
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(self.delete_btn)
        root.add_widget(btn_row)
        self.add_widget(root)

    def _confirm(self):
        self.delete_btn.text = "Deleting..."
        self.delete_btn.disabled = True

        def worker():
            try:
                api.delete_plant(self.plant_id)
                Clock.schedule_once(lambda dt: self._on_success())
            except Exception as exc:
                Clock.schedule_once(lambda dt, err=exc: self._on_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self):
        self.dismiss()
        if self.on_deleted:
            self.on_deleted(self.plant_id)

    def _on_error(self, exc):
        self.delete_btn.text = "Delete Plant"
        self.delete_btn.disabled = False
        ErrorModal("Could not delete plant.").open()


class ErrorModal(ModalView):
    """Generic error alert dialog modal."""
    def __init__(self, message, **kwargs):
        width = min(dp(340), Window.width * 0.9)
        height = min(dp(180), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), **kwargs)
        box = RoundedBox(orientation="vertical", padding=dp(16), spacing=dp(10), bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER, radius=dp(18))
        lbl = Label(text=message, color=COLOR_DARKEST, font_size="12sp")
        box.add_widget(lbl)
        ok_btn = PillButton(text="OK", bg_color=COLOR_DARK_GREEN, radius=dp(14), size_hint_y=None, height=dp(40))
        ok_btn.bind(on_release=lambda *_: self.dismiss())
        box.add_widget(ok_btn)
        self.add_widget(box)


class SproutApp(App):
    """Main App Controller Class."""
    def build(self):
        self.title = "Sprout"
        self.plants = []
        self.active_tab = "dashboard"
        self.active_symptom = None
        self.root_layout = RootLayout()
        self._update_nav_styles()
        self.render_empty_state()
        self._fetch_plants()
        return self.root_layout

    def switch_tab(self, tab_name):
        """Switches current navigation tab and updates view content."""
        self.active_tab = tab_name
        self.active_symptom = None
        self._update_nav_styles()
        self.render_current_tab()

    def _update_nav_styles(self):
        """Updates active/inactive button colors on the left sidebar."""
        nav_ids = {
            "dashboard": "nav_dashboard",
            "plants": "nav_plants",
            "schedule": "nav_schedule",
            "symptoms": "nav_symptoms",
        }
        for name, nav_id in nav_ids.items():
            if nav_id in self.root_layout.ids:
                widget = self.root_layout.ids[nav_id]
                if name == self.active_tab:
                    widget.bg_color = COLOR_DARK_GREEN
                    widget.fg_color = [1, 1, 1, 1]
                else:
                    widget.bg_color = [0, 0, 0, 0]
                    widget.fg_color = COLOR_DARKEST

    def _fetch_plants(self):
        """Asynchronously fetches plants list from backend API."""
        def worker():
            try:
                plants = api.fetch_plants()
                Clock.schedule_once(lambda dt: self._on_plants_loaded(plants or []))
            except Exception:
                print("Backend not running? Could not reach", api.API_BASE_URL)

        threading.Thread(target=worker, daemon=True).start()

    def _on_plants_loaded(self, plants):
        self.plants = plants
        self.render_current_tab()

    def open_add_modal(self):
        AddPlantModal(on_saved=self._on_plant_added).open()

    def _on_plant_added(self, plant):
        self.plants.append(plant)
        self.render_current_tab()

    def water_plant(self, plant_id):
        """Triggers watering event API call for a specific plant."""
        def worker():
            try:
                updated = api.water_plant(plant_id)
                Clock.schedule_once(lambda dt: self._on_plant_watered(updated))
            except Exception:
                Clock.schedule_once(lambda dt: ErrorModal("Could not water plant.").open())

        threading.Thread(target=worker, daemon=True).start()

    def _on_plant_watered(self, updated):
        for i, p in enumerate(self.plants):
            if p.get("id") == updated.get("id"):
                self.plants[i] = updated
                break
        self.render_current_tab()

    def open_delete_modal(self, plant_id, plant_name):
        DeleteConfirmModal(plant_id, plant_name, on_deleted=self._on_plant_deleted).open()

    def _on_plant_deleted(self, plant_id):
        self.plants = [p for p in self.plants if p.get("id") != plant_id]
        self.render_current_tab()

    def render_current_tab(self):
        """Delegates rendering to the appropriate view module."""
        self.root_layout.plant_count_label = f"{len(self.plants)} plants in collection"
        if self.active_tab == "dashboard":
            render_dashboard(self)
        elif self.active_tab == "plants":
            render_my_plants(self)
        elif self.active_tab == "schedule":
            render_schedule(self)
        elif self.active_tab == "symptoms":
            if self.active_symptom:
                render_symptom_detail(self, self.active_symptom)
            else:
                render_symptom_guide(self)

    def render_empty_state(self):
        """Renders the empty welcome layout when 0 plants exist."""
        container = self.root_layout.ids.main_content
        container.clear_widgets()

        wrapper = BoxLayout(
            orientation="vertical",
            spacing=dp(16),
            size_hint_y=None,
            height=dp(380),
            padding=[dp(20), dp(80), dp(20), 0]
        )
        wrapper.add_widget(EmojiLabel(
            text="\U0001F331",
            font_size="28sp",
            size_hint=(None, None), size=(dp(36), dp(36)),
            pos_hint={"center_x": 0.5}
        ))
        wrapper.add_widget(Label(
            text="Welcome to Sprout",
            bold=True,
            font_size="28sp",
            color=COLOR_DARKEST,
            size_hint_y=None,
            height=dp(36),
            halign="center"
        ))
        desc_lbl = Label(
            text="Add your first plant to get started. Sprout will build your\ncare schedule and remind you what to do and when.",
            font_size="14sp",
            color=COLOR_MUTED2,
            size_hint_y=None,
            height=dp(44),
            halign="center",
            valign="middle"
        )
        desc_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        wrapper.add_widget(desc_lbl)

        add_btn = PillButton(
            text="Add your first plant",
            bg_color=COLOR_DARK_GREEN,
            fg_color=[1, 1, 1, 1],
            radius=dp(14),
            size_hint=(None, None),
            size=(dp(190), dp(46)),
            pos_hint={"center_x": 0.5}
        )
        add_btn.bind(on_release=lambda *_: self.open_add_modal())
        wrapper.add_widget(add_btn)

        container.add_widget(wrapper)


if __name__ == "__main__":
    SproutApp().run()