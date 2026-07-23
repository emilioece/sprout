"""

Setup:
    pip install kivy requests
    python main.py

"""

import os
import platform
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex as hex_color

import api



def _register_emoji_font():
    local_override = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "emoji_font.ttf"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "emoji_font.ttc"),
    ]
    system = platform.system()
    if system == "Darwin":
        system_candidates = ["/System/Library/Fonts/Apple Color Emoji.ttc"]
    elif system == "Windows":
        system_candidates = [
            "C:/Windows/Fonts/seguiemj.ttf",
            "C:/Windows/Fonts/Seguiemj.ttf",
        ]
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
    return None  # falls back to Kivy's default font


EMOJI_FONT = _register_emoji_font()


# ---------------------------------------------------------------------------
# color palette
# ---------------------------------------------------------------------------
COLOR_BG = hex_color("#F3F1EA")
COLOR_DARK_GREEN = hex_color("#284E36")
COLOR_DARKEST = hex_color("#1E2A20")
COLOR_MUTED = hex_color("#788177")
COLOR_MUTED2 = hex_color("#616C60")
COLOR_BORDER = hex_color("#E5E3DC")
COLOR_CARD_GREEN = hex_color("#E9EEE6")
COLOR_RED = hex_color("#DC2626")
COLOR_RED_BG = hex_color("#FEE2E2")

QUICK_SPECIES = [
    ("Fern", "\U0001F33F", "easy \u00b7 indirect"),
    ("Moss", "\U0001F343", "easy \u00b7 low light"),
    ("Cactus", "\U0001F331", "expert \u00b7 indirect"),
    ("Bamboo", "\U0001F33E", "easy \u00b7 low light"),
]


# ---------------------------------------------------------------------------
# buttons
# ---------------------------------------------------------------------------

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


class RootLayout(BoxLayout):
    plant_count_label = StringProperty("0 plants in collection")


class IconRow(BoxLayout):

    def __init__(self, icon="", text="", text_color=None, bold=True,
                 icon_size="16sp", text_size="12sp", icon_width=dp(26),
                 halign="left", **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        icon_lbl = Label(text=icon, font_name=EMOJI_FONT, font_size=icon_size,
                         size_hint_x=None, width=icon_width, halign=halign,
                         valign="middle")
        icon_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        text_lbl = Label(text=text, font_size=text_size, bold=bold,
                         color=text_color or COLOR_DARKEST, halign=halign,
                         valign="middle")
        text_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        self.add_widget(icon_lbl)
        self.add_widget(text_lbl)


class IconButtonRow(ButtonBehavior, RoundedBox):


    icon = StringProperty("")
    label_text = StringProperty("")
    fg_color = ListProperty(COLOR_DARKEST)


# ---------------------------------------------------------------------------
# Add Plant modal
# ---------------------------------------------------------------------------

class AddPlantModal(ModalView):
    def __init__(self, on_saved, **kwargs):
        # Size relative to the actual window instead of a fixed pixel value --
        # a fixed dp(...) size can end up taller than the window on some
        # displays/DPI settings, which clips the modal off the top/bottom.
        width = min(dp(480), Window.width * 0.92)
        height = min(dp(620), Window.height * 0.9)
        super().__init__(size_hint=(None, None), size=(width, height),
                         auto_dismiss=False, **kwargs)
        self.on_saved = on_saved
        self.species = ""
        self.nickname_input = None
        self.location_input = None
        self.step = 1
        self._build_step_1()

    # ---- shared chrome -----------------------------------------------
    def _header(self, title, subtitle, show_back=False):
        header = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8),
                           padding=(dp(4), 0))
        if show_back:
            back_btn = PillButton(text="<", size_hint=(None, None),
                                  size=(dp(32), dp(32)), bg_color=hex_color("#EFECE6"),
                                  fg_color=COLOR_MUTED2, radius=dp(16))
            back_btn.bind(on_release=lambda *_: self._build_step_1())
            header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical")
        title_lbl = Label(text=title, bold=True, font_size="18sp",
                          color=COLOR_DARKEST, halign="left", valign="bottom")
        title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        sub_lbl = Label(text=subtitle, font_size="11sp", color=COLOR_MUTED,
                        halign="left", valign="top")
        sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        title_box.add_widget(title_lbl)
        title_box.add_widget(sub_lbl)
        header.add_widget(title_box)

        close_btn = PillButton(text="X", size_hint=(None, None), size=(dp(32), dp(32)),
                               bg_color=hex_color("#EFECE6"), fg_color=COLOR_MUTED2,
                               radius=dp(16))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        header.add_widget(close_btn)
        return header

    def _labeled_input(self, label_text, placeholder="", multiline=False):
        box = BoxLayout(orientation="vertical", size_hint_y=None,
                        height=dp(74) if multiline else dp(54), spacing=dp(4))
        lbl = Label(text=label_text, font_size="11sp", bold=True, color=COLOR_MUTED2,
                    size_hint_y=None, height=dp(16), halign="left")
        lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        box.add_widget(lbl)
        ti = TextInput(hint_text=placeholder, multiline=multiline,
                       background_normal="", background_active="", background_disabled_normal="",
                       background_color=hex_color("#F6F5F0"),
                       foreground_color=COLOR_DARKEST, hint_text_color=hex_color("#9A9E97"),
                       cursor_color=COLOR_DARK_GREEN, padding=(dp(12), dp(10)),
                       size_hint_y=None, height=dp(38) if not multiline else dp(50))
        box.add_widget(ti)
        return box, ti

    # ---- step 1: choose species ---------------------------------------
    def _build_step_1(self):
        self.step = 1
        self.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self._header("Identify your plant", "Step 1 of 2"))


        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12),
                         size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        # search, photo, and descriptions

        tab_bar = RoundedBox(orientation="horizontal", size_hint_y=None, height=dp(44),
                             padding=dp(4), spacing=dp(4),
                             bg_color=hex_color("#EFECE6"), border_color=hex_color("#EFECE6"),
                             radius=dp(16))
        tab_bar.add_widget(IconButtonRow(icon="\U0001F50D", label_text="Search",
                                         bg_color=COLOR_DARK_GREEN, fg_color=[1, 1, 1, 1],
                                         radius=dp(12)))
        tab_bar.add_widget(IconButtonRow(icon="\U0001F4F7", label_text="Photo",
                                         bg_color=[0, 0, 0, 0], fg_color=COLOR_MUTED2,
                                         radius=dp(12)))
        tab_bar.add_widget(IconButtonRow(icon="\U0001F4AC", label_text="Describe",
                                         bg_color=[0, 0, 0, 0], fg_color=COLOR_MUTED2,
                                         radius=dp(12)))
        body.add_widget(tab_bar)

        search_box, search_input = self._labeled_input(
            "Species", "e.g. monstera, snake plant, cactus...")
        search_input.text = self.species
        body.add_widget(search_box)

        for name, icon, tags in QUICK_SPECIES:
            row = IconButtonRow(
                icon=icon, label_text=f"{name}   ({tags})",
                size_hint_y=None, height=dp(52),
                bg_color=hex_color("#E9EEE6") if self.species == name else hex_color("#F6F5F0"),
                fg_color=COLOR_DARKEST, radius=dp(16),
            )

            def make_cb(n=name):
                def _cb(*_):
                    self.species = n
                    search_input.text = n
                    self._build_step_1()
                return _cb

            row.bind(on_release=make_cb())
            body.add_widget(row)

        scroll.add_widget(body)
        root.add_widget(scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(16))
        continue_btn = PillButton(text="Continue ->", bg_color=COLOR_DARK_GREEN,
                                  radius=dp(16))

        def go_next(*_):
            self.species = search_input.text.strip() or self.species
            if self.species:
                self._build_step_2()

        continue_btn.bind(on_release=go_next)
        footer.add_widget(continue_btn)
        root.add_widget(footer)

        self.add_widget(root)

    # ---- step 2: nickname + details -------------------------------------
    def _build_step_2(self):
        self.step = 2
        self.clear_widgets()
        root = BoxLayout(orientation="vertical")
        root.add_widget(self._header("Plant details", "Step 2 of 2", show_back=True))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10),
                         size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        summary = RoundedBox(size_hint_y=None, height=dp(50), padding=dp(10),
                             bg_color=COLOR_CARD_GREEN, border_color=COLOR_CARD_GREEN,
                             radius=dp(16))
        summary.add_widget(IconRow(icon="\U0001F343", text=self.species,
                                   text_color=COLOR_DARK_GREEN, icon_size="18sp",
                                   text_size="13sp"))
        body.add_widget(summary)

        nick_box, nick_input = self._labeled_input("Nickname *", self.species)
        nick_input.text = self.species
        self.nickname_input = nick_input
        body.add_widget(nick_box)

        loc_box, loc_input = self._labeled_input(
            "Location in home", "e.g. Living room window, Bedroom shelf")
        self.location_input = loc_input
        body.add_widget(loc_box)

        schedule = RoundedBox(orientation="vertical", size_hint_y=None, height=dp(96),
                              padding=dp(12), bg_color=hex_color("#F6F5F0"),
                              border_color=hex_color("#F6F5F0"), radius=dp(16))
        schedule.add_widget(Label(text="Auto-filled care schedule", bold=True,
                                  font_size="11sp", color=COLOR_DARKEST, halign="left"))
        for icon, name, freq in [
            ("\U0001F4A7", "Watering", "Every 7 days"),
            ("\U0001F33F", "Fertilizing", "Every 60 days"),
            ("\U0001FAB4", "Repotting", "Every 18 months"),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(20))
            row.add_widget(IconRow(icon=icon, text=name, text_color=COLOR_MUTED2,
                                   bold=False, icon_size="12sp", text_size="10sp",
                                   icon_width=dp(20)))
            row.add_widget(Label(text=freq, font_size="10sp", bold=True,
                                 color=COLOR_DARKEST, halign="right"))
            schedule.add_widget(row)
        body.add_widget(schedule)

        scroll.add_widget(body)
        root.add_widget(scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(70), padding=dp(16))
        self.save_btn = PillButton(text="Add to my collection", bg_color=COLOR_DARK_GREEN,
                                   radius=dp(16))
        self.save_btn.bind(on_release=lambda *_: self._save())
        footer.add_widget(self.save_btn)
        root.add_widget(footer)

        self.add_widget(root)

    def _save(self):
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
                Clock.schedule_once(lambda dt: self._on_success(plant))
            except Exception as exc:
                Clock.schedule_once(lambda dt: self._on_error(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, plant):
        self.dismiss()
        if self.on_saved:
            self.on_saved(plant)

    def _on_error(self, exc):
        self.save_btn.text = "Add to my collection"
        self.save_btn.disabled = False
        ErrorModal("Could not save plant. Make sure your backend server is running!").open()


# ---------------------------------------------------------------------------
# Delete button
# ---------------------------------------------------------------------------

class DeleteConfirmModal(ModalView):
    def __init__(self, plant_id, plant_name, on_deleted, **kwargs):
        width = min(dp(360), Window.width * 0.9)
        height = min(dp(280), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height),
                         auto_dismiss=False, **kwargs)
        self.plant_id = plant_id
        self.on_deleted = on_deleted

        root = RoundedBox(orientation="vertical", padding=dp(20), spacing=dp(12),
                          bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER, radius=dp(20))
        root.add_widget(Label(text="\U0001F5D1", font_name=EMOJI_FONT, font_size="26sp",
                              color=COLOR_RED, size_hint_y=None, height=dp(40)))
        root.add_widget(Label(text=f"Remove {plant_name}?", bold=True, font_size="16sp",
                              color=COLOR_DARKEST, size_hint_y=None, height=dp(28)))
        root.add_widget(Label(
            text="Are you sure you want to delete this plant? This cannot be undone.",
            font_size="11sp", color=COLOR_MUTED2, size_hint_y=None, height=dp(50)))

        btn_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(46))
        cancel_btn = PillButton(text="Cancel", bg_color=hex_color("#F6F5F0"),
                                fg_color=COLOR_MUTED2, radius=dp(16))
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        self.delete_btn = PillButton(text="Delete Plant", bg_color=COLOR_RED,
                                     radius=dp(16))
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
                Clock.schedule_once(lambda dt: self._on_error(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self):
        self.dismiss()
        if self.on_deleted:
            self.on_deleted(self.plant_id)

    def _on_error(self, exc):
        self.delete_btn.text = "Delete Plant"
        self.delete_btn.disabled = False
        ErrorModal("Could not delete plant. Make sure your backend server is running!").open()


class ErrorModal(ModalView):
    def __init__(self, message, **kwargs):
        width = min(dp(340), Window.width * 0.9)
        height = min(dp(180), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), **kwargs)
        box = RoundedBox(orientation="vertical", padding=dp(16), spacing=dp(10),
                         bg_color=[1, 1, 1, 1], border_color=COLOR_BORDER, radius=dp(18))
        lbl = Label(text=message, color=COLOR_DARKEST, font_size="12sp")
        box.add_widget(lbl)
        ok_btn = PillButton(text="OK", bg_color=COLOR_DARK_GREEN, radius=dp(14),
                            size_hint_y=None, height=dp(40))
        ok_btn.bind(on_release=lambda *_: self.dismiss())
        box.add_widget(ok_btn)
        self.add_widget(box)


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class SproutApp(App):
    def build(self):
        self.title = "Sprout"
        self.plants = []
        self.root_layout = RootLayout()
        self._render_empty_state()
        self._fetch_plants()
        return self.root_layout

    # ---- data loading ---------------------------------------------------
    def _fetch_plants(self):
        def worker():
            try:
                plants = api.fetch_plants()
                Clock.schedule_once(lambda dt: self._on_plants_loaded(plants or []))
            except Exception:
                print("Backend not running? Could not reach", api.API_BASE_URL)

        threading.Thread(target=worker, daemon=True).start()

    def _on_plants_loaded(self, plants):
        self.plants = plants
        self._render_dashboard()

    # ---- add plant flow ---------------------------------------------------
    def open_add_modal(self):
        AddPlantModal(on_saved=self._on_plant_added).open()

    def _on_plant_added(self, plant):
        self.plants.append(plant)
        self._render_dashboard()

    # ---- water / delete actions --------------------------------------------
    def water_plant(self, plant_id):
        def worker():
            try:
                updated = api.water_plant(plant_id)
                Clock.schedule_once(lambda dt: self._on_plant_watered(updated))
            except Exception as exc:
                Clock.schedule_once(lambda dt: ErrorModal(
                    "Could not water plant. Make sure your backend server is running!"
                ).open())

        threading.Thread(target=worker, daemon=True).start()

    def _on_plant_watered(self, updated):
        for i, p in enumerate(self.plants):
            if p.get("id") == updated.get("id"):
                self.plants[i] = updated
                break
        self._render_dashboard()

    def open_delete_modal(self, plant_id, plant_name):
        DeleteConfirmModal(plant_id, plant_name, on_deleted=self._on_plant_deleted).open()

    def _on_plant_deleted(self, plant_id):
        self.plants = [p for p in self.plants if p.get("id") != plant_id]
        if self.plants:
            self._render_dashboard()
        else:
            self._render_empty_state()

    # ---- rendering ---------------------------------------------------------
    @staticmethod
    def _water_label(days):
        if days < 0:
            return "Overdue"
        if days == 0:
            return "Due today"
        return f"In {days}d"

    def _render_empty_state(self):
        container = self.root_layout.ids.main_content
        container.clear_widgets()
        self.root_layout.plant_count_label = "0 plants in collection"

        wrapper = BoxLayout(orientation="vertical", spacing=dp(12),
                            size_hint_y=None, height=dp(500))
        wrapper.add_widget(Label(text="\U0001F331", font_name=EMOJI_FONT, font_size="46sp",
                                 size_hint_y=None, height=dp(70)))
        wrapper.add_widget(Label(text="Welcome to Sprout", bold=True, font_size="24sp",
                                 color=COLOR_DARKEST, size_hint_y=None, height=dp(36)))
        wrapper.add_widget(Label(
            text="Add your first plant to get started. Sprout will build your "
                 "care schedule and remind you what to do and when.",
            font_size="12sp", color=COLOR_MUTED2, size_hint_y=None, height=dp(50)))
        add_btn = PillButton(text="Add your first plant", bg_color=COLOR_DARK_GREEN,
                             radius=dp(16), size_hint=(None, None),
                             size=(dp(220), dp(48)), pos_hint={"center_x": 0.5})
        add_btn.bind(on_release=lambda *_: self.open_add_modal())
        wrapper.add_widget(add_btn)
        container.add_widget(wrapper)

    def _render_dashboard(self):
        container = self.root_layout.ids.main_content
        container.clear_widgets()
        self.root_layout.plant_count_label = (
            f"{len(self.plants)} {'plant' if len(self.plants) == 1 else 'plants'} in collection"
        )

        if not self.plants:
            self._render_empty_state()
            return

        # header
        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
        header.add_widget(Label(text="Dashboard", bold=True, font_size="30sp",
                                color=COLOR_DARKEST, halign="left",
                                size_hint_y=None, height=dp(40)))
        header.add_widget(Label(text="Wednesday, July 22", font_size="12sp",
                                color=COLOR_MUTED, halign="left",
                                size_hint_y=None, height=dp(18)))
        container.add_widget(header)

        # stat cards
        overdue = sum(1 for p in self.plants if p.get("daysUntilWater", 0) < 0)
        due_today = sum(1 for p in self.plants if p.get("daysUntilWater", 0) == 0)

        stats_row = BoxLayout(size_hint_y=None, height=dp(120), spacing=dp(16))
        stats_row.add_widget(StatCard(icon="\U0001FAB4", value=str(len(self.plants)),
                                      label_text="Plants"))
        stats_row.add_widget(StatCard(icon="\u26A0\uFE0F", value=str(overdue),
                                      label_text="Overdue tasks"))
        stats_row.add_widget(StatCard(icon="\U0001F4CB", value=str(due_today),
                                      label_text="Due today"))
        container.add_widget(stats_row)

        # banner
        banner = RoundedBox(orientation="horizontal", size_hint_y=None, height=dp(70),
                            padding=dp(16), spacing=dp(12), bg_color=hex_color("#E8EFE6"),
                            border_color=hex_color("#E8EFE6"), radius=dp(16))
        banner.add_widget(Label(text="\u2728", font_name=EMOJI_FONT, font_size="20sp",
                                size_hint_x=None, width=dp(30)))
        banner_text = BoxLayout(orientation="vertical")
        banner_text.add_widget(Label(text="All caught up!", bold=True, font_size="13sp",
                                     color=COLOR_DARKEST, halign="left"))
        banner_text.add_widget(Label(
            text="No tasks due today. Check the Schedule to see what's coming next.",
            font_size="11sp", color=COLOR_MUTED2, halign="left"))
        banner.add_widget(banner_text)
        container.add_widget(banner)

        # upcoming watering list
        container.add_widget(Label(text="Upcoming watering", bold=True, font_size="18sp",
                                   color=COLOR_DARKEST, halign="left", size_hint_y=None,
                                   height=dp(30)))

        list_box = BoxLayout(orientation="vertical", spacing=dp(10),
                             size_hint_y=None)
        list_box.bind(minimum_height=list_box.setter("height"))

        for plant in self.plants:
            name = plant.get("name") or plant.get("nickname", "")
            row = PlantRow(
                plant_id=plant.get("id"),
                plant_name=name,
                subtitle=plant.get("location") or plant.get("species") or "Unspecified",
                initials=(name[:4] if name else ""),
                due_label=self._water_label(plant.get("daysUntilWater", 0)),
            )
            row.on_water_cb = self.water_plant
            row.on_delete_cb = self.open_delete_modal
            list_box.add_widget(row)

        container.add_widget(list_box)


if __name__ == "__main__":
    SproutApp().run()