"""
ui tests for the desktop client

these test the interface layer itself, the theme system, the custom widgets,
and the logic behind what each screen draws. they do not test the api module.

kivy normally wants a real window before it will build widgets, which is why
ui code is awkward to test. the parts covered here are the ones that do not
touch kivy.core.window, so they run in a plain terminal with no window ever
opening. the modal dialogs in components/modals.py do import Window and are
verified manually instead, which is recorded in section 6.2.

run these from the desktop-new folder:
    python -m pytest tests -v
"""

import os
import sys
from datetime import date, timedelta

import pytest

os.environ.setdefault("KIVY_NO_ARGS", "1")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from theme import theme, LIGHT, DARK  # noqa: E402
from components.widgets import (  # noqa: E402
    RoundedBox,
    PillButton,
    EmojiLabel,
    StatCard,
)
from components.utils import default_picture_dir  # noqa: E402
from views.schedule import _watering_days_this_month  # noqa: E402
from views.symptom_guide import SYMPTOMS_DATA  # noqa: E402


@pytest.fixture(autouse=True)
def reset_theme():
    """
    theme is a single shared object, so a test that leaves it in dark mode
    would change what the next test sees. this puts it back to light after
    every test
    """
    yield
    theme.set_dark(False)


# ---------------------------------------------------------------------------
# ui test 1 - the dark mode toggle
# ---------------------------------------------------------------------------

def test_toggle_switches_between_light_and_dark():
    """
    the toggle in the sidebar calls this. if it stops working the button
    looks like it does nothing at all
    """
    assert theme.dark is False

    theme.toggle()
    assert theme.dark is True

    theme.toggle()
    assert theme.dark is False


def test_toggle_actually_changes_the_colors():
    """
    flipping the flag is not enough, the colour values themselves have to
    change or the interface stays light while claiming to be dark
    """
    light_surface = list(theme.surface)
    light_text = list(theme.text)

    theme.set_dark(True)

    assert list(theme.surface) != light_surface
    assert list(theme.text) != light_text
    assert list(theme.surface) == list(DARK["surface"])
    assert list(theme.text) == list(DARK["text"])


def test_both_palettes_define_the_same_colors():
    """
    if a colour exists in light but not dark, every widget using it keeps
    its light value after the toggle and ends up unreadable on a dark
    background. this is the check that catches a half finished palette
    """
    assert set(LIGHT.keys()) == set(DARK.keys())


def test_every_theme_color_is_a_valid_rgba_value():
    for name in LIGHT:
        for palette_name, palette in (("LIGHT", LIGHT), ("DARK", DARK)):
            colour = palette[name]
            assert len(colour) == 4, f"{palette_name}[{name}] is not rgba"
            for channel in colour:
                assert 0.0 <= channel <= 1.0, f"{palette_name}[{name}] out of range"


def test_set_dark_is_repeatable():
    """
    the toggle gets clicked a lot. calling it repeatedly should always land
    on the same colours rather than drifting
    """
    for _ in range(5):
        theme.set_dark(True)
        assert list(theme.surface) == list(DARK["surface"])
        theme.set_dark(False)
        assert list(theme.surface) == list(LIGHT["surface"])


# ---------------------------------------------------------------------------
# ui test 2 - the reusable widgets
# ---------------------------------------------------------------------------

def test_widgets_build_with_no_arguments():
    """
    every screen is composed out of these. if one cannot be built with its
    defaults then a screen somewhere fails to render
    """
    assert RoundedBox() is not None
    assert PillButton() is not None
    assert EmojiLabel() is not None
    assert StatCard() is not None


def test_pill_button_keeps_the_text_it_is_given():
    button = PillButton(text="Add to my collection")
    assert button.text == "Add to my collection"


def test_rounded_box_accepts_a_custom_color():
    box = RoundedBox(bg_color=[0.1, 0.2, 0.3, 1.0])
    assert list(box.bg_color) == [0.1, 0.2, 0.3, 1.0]


def test_emoji_label_is_given_an_emoji_capable_font():
    """
    the default font renders emoji as empty boxes, which is why this widget
    exists at all. it has to carry a font name of its own
    """
    label = EmojiLabel(text="\U0001F331")
    assert label.font_name is not None
    assert label.font_name != ""


def test_widgets_can_be_nested():
    """
    the interface is built by putting widgets inside other widgets, so a
    container has to accept a child without complaint
    """
    box = RoundedBox()
    box.add_widget(PillButton(text="Save"))
    assert len(box.children) == 1


# ---------------------------------------------------------------------------
# ui test 3 - what the schedule screen draws
# ---------------------------------------------------------------------------

class FakeApp:
    """stands in for SproutApp, which cannot be built without a window"""

    def __init__(self, plants):
        self.plants = plants


def test_schedule_marks_a_plant_on_its_watering_days():
    """
    the calendar highlights the days a plant needs water. this is the
    calculation behind those highlights
    """
    today = date.today()
    app = FakeApp([
        {"name": "Monty", "daysUntilWater": 0, "watering_interval_days": 7},
    ])

    days = _watering_days_this_month(app, today.year, today.month)

    assert today.day in days
    assert "Monty" in days[today.day]


def test_schedule_repeats_a_plant_across_the_month():
    """
    a plant on a seven day cycle should appear several times in one month,
    not only once
    """
    app = FakeApp([
        {"name": "Monty", "daysUntilWater": 0, "watering_interval_days": 7},
    ])
    today = date.today()

    days = _watering_days_this_month(app, today.year, today.month)
    appearances = sum(1 for names in days.values() if "Monty" in names)

    assert appearances >= 2


def test_schedule_shows_two_plants_due_on_the_same_day():
    app = FakeApp([
        {"name": "Monty", "daysUntilWater": 0, "watering_interval_days": 7},
        {"name": "Spike", "daysUntilWater": 0, "watering_interval_days": 7},
    ])
    today = date.today()

    days = _watering_days_this_month(app, today.year, today.month)

    assert sorted(days[today.day]) == ["Monty", "Spike"]


def test_schedule_is_empty_with_no_plants():
    app = FakeApp([])
    today = date.today()

    assert _watering_days_this_month(app, today.year, today.month) == {}


def test_schedule_survives_a_zero_interval():
    """
    an interval of zero would loop forever, so it has to be replaced with a
    sensible default rather than hanging the interface
    """
    app = FakeApp([
        {"name": "Broken", "daysUntilWater": 0, "watering_interval_days": 0},
    ])
    today = date.today()

    days = _watering_days_this_month(app, today.year, today.month)
    assert len(days) > 0


def test_schedule_falls_back_to_nickname_when_name_is_missing():
    """
    plants coming straight from the backend have nickname but not name, so
    the calendar must not label them blank
    """
    app = FakeApp([
        {"nickname": "Fern", "daysUntilWater": 0, "watering_interval_days": 7},
    ])
    today = date.today()

    days = _watering_days_this_month(app, today.year, today.month)
    assert "Fern" in days[today.day]


# ---------------------------------------------------------------------------
# ui test 4 - the symptom guide content
# ---------------------------------------------------------------------------

def test_every_symptom_has_the_fields_the_screen_draws():
    """
    the symptom screen reads these keys directly. a missing one raises a
    keyerror while the user is looking at the page
    """
    required = {"id", "title", "icon", "urgency_text",
                "urgency_color", "urgency_bg", "causes", "fixes"}

    assert len(SYMPTOMS_DATA) > 0
    for symptom in SYMPTOMS_DATA:
        missing = required - set(symptom.keys())
        assert not missing, f"{symptom.get('id')} is missing {missing}"


def test_symptom_ids_are_unique():
    ids = [s["id"] for s in SYMPTOMS_DATA]
    assert len(ids) == len(set(ids))


def test_every_symptom_lists_at_least_one_cause_and_one_fix():
    """
    the detail view shows counts like "4 possible causes, 4 fixes", so an
    empty list would render as a blank section
    """
    for symptom in SYMPTOMS_DATA:
        assert len(symptom["causes"]) >= 1, symptom["id"]
        assert len(symptom["fixes"]) >= 1, symptom["id"]


def test_causes_and_fixes_are_title_and_description_pairs():
    for symptom in SYMPTOMS_DATA:
        for entry in symptom["causes"] + symptom["fixes"]:
            assert len(entry) == 2, f"{symptom['id']} has a malformed entry"
            assert all(isinstance(part, str) for part in entry)


def test_urgency_colors_are_valid_rgba():
    for symptom in SYMPTOMS_DATA:
        for key in ("urgency_color", "urgency_bg"):
            colour = symptom[key]
            assert len(colour) == 4
            assert all(0.0 <= channel <= 1.0 for channel in colour)


# ---------------------------------------------------------------------------
# supporting check - the photo picker opens somewhere sensible
# ---------------------------------------------------------------------------

def test_picker_opens_in_a_real_folder():
    """
    the file picker used to open at the c drive root, which is not where
    anyone keeps photos. this confirms it lands on a folder that exists
    """
    path = default_picture_dir()
    assert os.path.isdir(path)