# ===========================================================================
# App Theme - Reactive Light / Dark Color Palette
# ===========================================================================
#
# `theme` is a single shared object with Kivy properties. Widgets built in
# Python read `theme.text`, `theme.surface`, etc. at render time, so any
# view that gets rebuilt after a toggle automatically picks up the new
# colors. Widgets declared in the .kv file bind directly to these
# properties (e.g. `color: theme.text`), so they update live even without
# being rebuilt.

from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ListProperty
from kivy.utils import get_color_from_hex as hex_color

LIGHT = {
    "bg": hex_color("#F3F1EA"),
    "surface": hex_color("#FFFFFF"),
    "surface_alt": hex_color("#F5F3ED"),
    "chip": hex_color("#EFECE6"),
    "pill_inactive": hex_color("#EBE8DF"),
    "accent_soft": hex_color("#E9EEE6"),
    "border": hex_color("#E5E3DC"),
    "text": hex_color("#1E2A20"),
    "muted": hex_color("#788177"),
    "muted2": hex_color("#616C60"),
    "dark_green": hex_color("#284E36"),
    "red": hex_color("#DC2626"),
    "hint": hex_color("#9A9E97"),
    "input_bg": hex_color("#F6F5F0"),
    "disabled_accent": hex_color("#A8BBA2"),
    "water_highlight": hex_color("#DBEAFE"),
}

DARK = {
    "bg": hex_color("#141B16"),
    "surface": hex_color("#1E2620"),
    "surface_alt": hex_color("#242D27"),
    "chip": hex_color("#2A332C"),
    "pill_inactive": hex_color("#2A332C"),
    "accent_soft": hex_color("#24352B"),
    "border": hex_color("#34413A"),
    "text": hex_color("#EDEDE7"),
    "muted": hex_color("#93A199"),
    "muted2": hex_color("#AAB6AF"),
    "dark_green": hex_color("#4C8562"),
    "red": hex_color("#F87171"),
    "hint": hex_color("#6B786F"),
    "input_bg": hex_color("#242D27"),
    "disabled_accent": hex_color("#3A473F"),
    "water_highlight": hex_color("#1E3A5F"),
}


class Theme(EventDispatcher):
    """Holds the current palette as bindable Kivy properties."""

    dark = BooleanProperty(False)

    bg = ListProperty(LIGHT["bg"])
    surface = ListProperty(LIGHT["surface"])
    surface_alt = ListProperty(LIGHT["surface_alt"])
    chip = ListProperty(LIGHT["chip"])
    pill_inactive = ListProperty(LIGHT["pill_inactive"])
    accent_soft = ListProperty(LIGHT["accent_soft"])
    border = ListProperty(LIGHT["border"])
    text = ListProperty(LIGHT["text"])
    muted = ListProperty(LIGHT["muted"])
    muted2 = ListProperty(LIGHT["muted2"])
    dark_green = ListProperty(LIGHT["dark_green"])
    red = ListProperty(LIGHT["red"])
    hint = ListProperty(LIGHT["hint"])
    input_bg = ListProperty(LIGHT["input_bg"])
    disabled_accent = ListProperty(LIGHT["disabled_accent"])
    water_highlight = ListProperty(LIGHT["water_highlight"])

    def set_dark(self, is_dark):
        palette = DARK if is_dark else LIGHT
        self.dark = is_dark
        for key, value in palette.items():
            setattr(self, key, value)

    def toggle(self):
        self.set_dark(not self.dark)


# Single shared instance imported everywhere (main.py + all view modules + the .kv file)
theme = Theme()