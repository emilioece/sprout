# Tests for JSON parsing helper (no real Gemini calls)

import pytest

from app.services.gemini import _extract_json


def test_extract_json_parses_clean_object():
    data = _extract_json('{"name": "Maria", "species": "Tagetes"}')
    assert data == {"name": "Maria", "species": "Tagetes"}


def test_extract_json_salvages_wrapped_text():
    raw = 'Here is JSON:\n{"interval_days": 7}\nThanks!'
    data = _extract_json(raw)
    assert data == {"interval_days": 7}


def test_extract_json_empty_returns_none():
    assert _extract_json("") is None
    assert _extract_json("   ") is None


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError):
        _extract_json("not json at all")
