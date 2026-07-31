from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex as hex_color

from theme import theme
from components.utils import EMOJI_FONT

class EmojiLabel(Label):
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
    bg_color = ListProperty(theme.dark_green)
    fg_color = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(dp(14))

class SideNavItem(BoxLayout):
    icon = StringProperty("")
    text = StringProperty("")
    bg_color = ListProperty([0, 0, 0, 0])
    fg_color = ListProperty(theme.text)

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
    subtitle = StringProperty("4 possible causes · 4 fixes")
    urgency_text = StringProperty("")
    urgency_color = ListProperty([0, 0, 0, 1])
    urgency_bg = ListProperty([1, 1, 1, 1])

class RootLayout(BoxLayout):
    plant_count_label = StringProperty("0 plants in collection")

class IconButtonRow(ButtonBehavior, RoundedBox):
    icon = StringProperty("")
    label_text = StringProperty("")
    fg_color = ListProperty(theme.text)

class SelectableCard(ButtonBehavior, RoundedBox):
    pass