import os
import platform
from kivy.core.text import LabelBase

def register_emoji_font():
    local_override = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "emoji_font.ttf"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "emoji_font.ttc"),
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

EMOJI_FONT = register_emoji_font()