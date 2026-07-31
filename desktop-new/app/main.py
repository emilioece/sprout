import os
import sys
import threading

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

import api
from theme import theme
from components.widgets import RootLayout, PillButton, EmojiLabel
from components.modals import AddPlantModal, DeleteConfirmModal, ErrorModal
from views.dashboard import render_dashboard
from views.my_plants import render_my_plants
from views.schedule import render_schedule
from views.symptom_guide import render_symptom_guide, render_symptom_detail

class SproutApp(App):
    dark_mode_label = StringProperty("\U0001F319  Dark mode")

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

    def toggle_dark_mode(self):
        theme.toggle()
        self.dark_mode_label = ("\u2600\uFE0F  Light mode" if theme.dark else "\U0001F319  Dark mode")
        self._update_nav_styles()
        if not self.plants:
            self.render_empty_state()
        else:
            self.render_current_tab()

    def switch_tab(self, tab_name):
        self.active_tab = tab_name
        self.active_symptom = None
        self._update_nav_styles()
        self.render_current_tab()

    def _update_nav_styles(self):
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
                    widget.bg_color = theme.dark_green
                    widget.fg_color = [1, 1, 1, 1]
                else:
                    widget.bg_color = [0, 0, 0, 0]
                    widget.fg_color = theme.text

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
        self.render_current_tab()

    def open_add_modal(self):
        AddPlantModal(on_saved=self._on_plant_added).open()

    def _on_plant_added(self, plant):
        self.plants.append(plant)
        self.render_current_tab()

    def water_plant(self, plant_id):
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
            text="\U0001F331", font_size="28sp",
            size_hint=(None, None), size=(dp(36), dp(36)),
            pos_hint={"center_x": 0.5}
        ))
        wrapper.add_widget(Label(
            text="Welcome to Sprout", bold=True,
            font_size="28sp", color=theme.text,
            size_hint_y=None, height=dp(36), halign="center"
        ))
        desc_lbl = Label(
            text="Add your first plant to get started. Sprout will build your\ncare schedule and remind you what to do and when.",
            font_size="14sp", color=theme.muted2,
            size_hint_y=None, height=dp(44), halign="center", valign="middle"
        )
        desc_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        wrapper.add_widget(desc_lbl)

        add_btn = PillButton(
            text="Add your first plant", bg_color=theme.dark_green,
            fg_color=[1, 1, 1, 1], radius=dp(14),
            size_hint=(None, None), size=(dp(190), dp(46)), pos_hint={"center_x": 0.5}
        )
        add_btn.bind(on_release=lambda *_: self.open_add_modal())
        wrapper.add_widget(add_btn)

        container.add_widget(wrapper)

if __name__ == "__main__":
    SproutApp().run()