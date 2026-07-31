import os
import platform
from kivy.core.text import LabelBase

def register_emoji_font():
    system = platform.system()

    # Standard scalable system candidates
    if system == "Darwin":
        system_candidates = [
            "/System/Library/Fonts/Apple Color Emoji.ttc",
            "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc",
        ]
    elif system == "Windows":
        system_candidates = [
            "C:/Windows/Fonts/seguiemj.ttf",
            "C:/Windows/Fonts/Seguiemj.ttf",
        ]

    for path in system_candidates:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            try:
                LabelBase.register(name="EmojiFont", fn_regular=expanded_path)
                return "EmojiFont"
            except Exception:
                continue

    return None

EMOJI_FONT = register_emoji_font()

def default_picture_dir():
    """
    picks a sensible folder for the file picker to open in
    tries the pictures folder first, then the home folder, and only
    falls back to the current directory if neither exists
    """
    for candidate in (os.path.expanduser("~/Pictures"), os.path.expanduser("~")):
        if os.path.isdir(candidate):
            return candidate
    return os.getcwd()