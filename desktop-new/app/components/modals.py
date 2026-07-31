import threading
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import api
from theme import theme
from components.widgets import RoundedBox, PillButton, EmojiLabel, IconButtonRow, SelectableCard

QUICK_SPECIES = [
    ("Fern", "\U0001F33F", "easy · indirect"),
    ("Moss", "\U0001F343", "easy · low light"),
    ("Cactus", "\U0001F331", "expert · indirect"),
    ("Bamboo", "\U0001F33E", "easy · low light"),
]

class ErrorModal(ModalView):
    def __init__(self, message, **kwargs):
        width = min(dp(340), Window.width * 0.9)
        height = min(dp(180), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), **kwargs)
        box = RoundedBox(orientation="vertical", padding=dp(16), spacing=dp(10), bg_color=theme.surface, border_color=theme.border, radius=dp(18))
        box.add_widget(Label(text=message, color=theme.text, font_size="12sp"))
        ok_btn = PillButton(text="OK", bg_color=theme.dark_green, radius=dp(14), size_hint_y=None, height=dp(40))
        ok_btn.bind(on_release=lambda *_: self.dismiss())
        box.add_widget(ok_btn)
        self.add_widget(box)

class DeleteConfirmModal(ModalView):
    def __init__(self, plant_id, plant_name, on_deleted, **kwargs):
        width = min(dp(360), Window.width * 0.9)
        height = min(dp(280), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), auto_dismiss=False, **kwargs)
        self.plant_id = plant_id
        self.on_deleted = on_deleted

        root = RoundedBox(orientation="vertical", padding=dp(20), spacing=dp(12), bg_color=theme.surface, border_color=theme.border, radius=dp(20))
        root.add_widget(EmojiLabel(text="\U0001F5D1", font_size="16sp", size_hint=(None, None), size=(dp(24), dp(24)), pos_hint={"center_x": 0.5}))
        root.add_widget(Label(text=f"Remove {plant_name}?", bold=True, font_size="16sp", color=theme.text, size_hint_y=None, height=dp(28)))
        root.add_widget(Label(text="Are you sure you want to delete this plant?", font_size="11sp", color=theme.muted2, size_hint_y=None, height=dp(50)))

        btn_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(46))
        cancel_btn = PillButton(text="Cancel", bg_color=theme.input_bg, fg_color=theme.muted2, radius=dp(16))
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        self.delete_btn = PillButton(text="Delete Plant", bg_color=theme.red, radius=dp(16))
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

class AddPlantModal(ModalView):
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
            back_btn = PillButton(text="<", size_hint=(None, None), size=(dp(32), dp(32)), bg_color=theme.chip, fg_color=theme.muted2, radius=dp(16))
            back_btn.bind(on_release=lambda *_: self._build_step_1())
            header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical")
        title_lbl = Label(text=title, bold=True, font_size="18sp", color=theme.text, halign="left", valign="bottom")
        title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        sub_lbl = Label(text=subtitle, font_size="11sp", color=theme.muted, halign="left", valign="top")
        sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        title_box.add_widget(title_lbl)
        title_box.add_widget(sub_lbl)
        header.add_widget(title_box)

        close_btn = PillButton(text="X", size_hint=(None, None), size=(dp(32), dp(32)), bg_color=theme.chip, fg_color=theme.muted2, radius=dp(16))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        header.add_widget(close_btn)
        return header

    def _labeled_input(self, label_text, placeholder="", multiline=False):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(74) if multiline else dp(54), spacing=dp(4))
        if label_text:
            lbl = Label(text=label_text, font_size="11sp", bold=True, color=theme.muted2, size_hint_y=None, height=dp(16), halign="left")
            lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            box.add_widget(lbl)

        ti = TextInput(
            hint_text=placeholder, multiline=multiline, background_normal="", background_active="",
            background_disabled_normal="", background_color=theme.input_bg,
            foreground_color=theme.text, hint_text_color=theme.hint,
            cursor_color=theme.dark_green, padding=(dp(14), dp(10)),
            size_hint_y=None, height=dp(40) if not multiline else dp(50)
        )
        box.add_widget(ti)
        return box, ti

    def _build_step_1(self):
        self.step = 1
        self.clear_widgets()

        root = RoundedBox(orientation="vertical", bg_color=theme.surface, border_color=theme.border, radius=dp(20), padding=dp(20))
        root.add_widget(self._header("Identify your plant", "Step 1 of 2"))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, dp(10), 0, dp(10)])
        body.bind(minimum_height=body.setter("height"))

        tab_bar = RoundedBox(orientation="horizontal", size_hint_y=None, height=dp(42), padding=dp(3), spacing=dp(2), bg_color=theme.surface_alt, border_color=theme.surface_alt, radius=dp(12))
        search_tab = IconButtonRow(icon="\U0001F50D", label_text="Search", bg_color=theme.dark_green, fg_color=[1, 1, 1, 1], radius=dp(10))
        photo_tab = IconButtonRow(icon="\U0001F4F7", label_text="Photo", bg_color=[0, 0, 0, 0], fg_color=theme.muted2, radius=dp(10))
        describe_tab = IconButtonRow(icon="\U0001F4AC", label_text="Describe", bg_color=[0, 0, 0, 0], fg_color=theme.muted2, radius=dp(10))

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
                bg_color=theme.accent_soft if is_selected else theme.surface_alt,
                border_color=theme.dark_green if is_selected else theme.surface_alt,
                border_width=1.5 if is_selected else 0,
                radius=dp(16)
            )

            icon_lbl = EmojiLabel(
                text=icon, font_size="1sp",
                size_hint=(None, None), size=(dp(24), dp(24)),
                pos_hint={"center_y": 0.5}
            )
            card.add_widget(icon_lbl)

            text_box = BoxLayout(orientation="vertical", spacing=dp(2))
            title_lbl = Label(text=name, bold=True, font_size="14sp", color=theme.text, halign="left", valign="bottom")
            title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

            sub_lbl = Label(text=tags, font_size="11sp", color=theme.muted, halign="left", valign="top")
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
        continue_btn = PillButton(text="Continue ->", bg_color=theme.dark_green if self.species else theme.disabled_accent, radius=dp(14))

        def go_next(*_):
            self.species = search_input.text.strip() or self.species
            if self.species:
                self._build_step_2()

        continue_btn.bind(on_release=go_next)
        footer.add_widget(continue_btn)
        root.add_widget(footer)

        self.add_widget(root)

    def _build_step_2(self):
        self.step = 2
        self.clear_widgets()

        root = RoundedBox(orientation="vertical", bg_color=theme.surface, border_color=theme.border, radius=dp(20), padding=dp(20))
        root.add_widget(self._header("Plant details", "Step 2 of 2", show_back=True))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, dp(10), 0, dp(10)])
        body.bind(minimum_height=body.setter("height"))

        summary = RoundedBox(
            orientation="horizontal", size_hint_y=None, height=dp(56),
            padding=[dp(14), dp(10)], spacing=dp(12),
            bg_color=theme.accent_soft, border_color=theme.accent_soft, radius=dp(14)
        )

        icon_lbl = EmojiLabel(
            text="\U0001F335" if self.species == "Cactus" else "\U0001F33F",
            font_size="1sp", size_hint=(None, None), size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5}
        )
        summary.add_widget(icon_lbl)

        summary_text = BoxLayout(orientation="vertical", spacing=dp(2))
        title_lbl = Label(text=self.species, bold=True, font_size="14sp", color=theme.dark_green, halign="left", valign="bottom")
        title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

        sub_lbl = Label(text="Care data auto-filled · easy", font_size="11sp", color=theme.muted2, halign="left", valign="top")
        sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

        summary_text.add_widget(title_lbl)
        summary_text.add_widget(sub_lbl)
        summary.add_widget(summary_text)
        body.add_widget(summary)

        photo_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), spacing=dp(4))
        photo_lbl = Label(text="Plant photo", font_size="11sp", bold=True, color=theme.muted2, size_hint_y=None, height=dp(16), halign="left")
        photo_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        photo_box.add_widget(photo_lbl)

        photo_area = RoundedBox(bg_color=theme.accent_soft, border_color=theme.accent_soft, radius=dp(14), size_hint_y=None, height=dp(80))
        add_photo_btn = PillButton(text="+ Add photo", bg_color=[0, 0, 0, 0], fg_color=theme.dark_green, font_size="12sp")
        photo_area.add_widget(add_photo_btn)
        photo_box.add_widget(photo_area)
        body.add_widget(photo_box)

        nick_box, nick_input = self._labeled_input("Nickname *", "e.g. Big Leaf, Monty, Corner Plant")
        nick_input.text = self.species
        self.nickname_input = nick_input
        body.add_widget(nick_box)

        loc_box, loc_input = self._labeled_input("Location in home", "e.g. Living room window, Bedroom shelf")
        self.location_input = loc_input
        body.add_widget(loc_box)

        schedule = RoundedBox(
            orientation="vertical", size_hint_y=None, height=dp(105),
            padding=dp(12), spacing=dp(6),
            bg_color=theme.surface_alt, border_color=theme.surface_alt, radius=dp(14)
        )

        sched_title = Label(text="Auto-filled care schedule", bold=True, font_size="11sp", color=theme.text, halign="left", size_hint_y=None, height=dp(16))
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
            ic_lbl = EmojiLabel(text=icon, font_size="1sp", size_hint=(None, None), size=(dp(16), dp(16)), pos_hint={"center_y": 0.5})
            nm_lbl = Label(text=name, font_size="11sp", color=theme.muted2, halign="left", valign="middle")
            nm_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            item_box.add_widget(ic_lbl)
            item_box.add_widget(nm_lbl)
            row.add_widget(item_box)

            freq_lbl = Label(text=freq, font_size="11sp", color=theme.text, halign="right", valign="middle")
            freq_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            row.add_widget(freq_lbl)
            schedule.add_widget(row)

        body.add_widget(schedule)

        notes_box, notes_input = self._labeled_input("Notes (optional)", "Any quirks about this specific plant?", multiline=True)
        body.add_widget(notes_box)

        scroll.add_widget(body)
        root.add_widget(scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(54), padding=[0, dp(8), 0, 0])
        self.save_btn = PillButton(text="Add to my collection", bg_color=theme.dark_green, radius=dp(14))
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
                Clock.schedule_once(lambda dt, p=plant: self._on_success(p))
            except Exception as exc:
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