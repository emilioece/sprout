"""
api.py - talks to the Sprout FastAPI backend.

Backend must be running:
    cd backend
    uvicorn app.main:app --reload
"""

import mimetypes
import os

import requests
from datetime import datetime, timezone

API_BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds


class ApiError(Exception):
    """Raised whenever the backend returns a non-2xx response or is unreachable."""


def _handle(resp: requests.Response):
    if not resp.ok:
        raise ApiError(f"{resp.status_code} {resp.reason}: {resp.text[:200]}")
    if resp.content:
        try:
            return resp.json()
        except ValueError:
            return None
    return None


def _days_until_water(last_watered_at, interval_days):
    """
    How many days until this plant needs water.
    Negative = overdue. Never watered = due today (0).

    The backend stores last_watered_at + watering_interval_days,
    so the countdown is calculated here rather than sent by the API.
    """
    if not last_watered_at:
        return 0

    try:
        # Backend sends ISO format, sometimes ending in Z for UTC
        last = datetime.fromisoformat(str(last_watered_at).replace("Z", "+00:00"))
    except ValueError:
        return 0

    # Treat naive timestamps as UTC so the subtraction doesn't blow up
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    next_water = last.timestamp() + (interval_days * 86400)
    now = datetime.now(timezone.utc).timestamp()

    return round((next_water - now) / 86400)


def _decorate(plant: dict) -> dict:
    """
    Add the fields the UI expects on top of what the backend returns.

    Backend gives:  nickname, watering_interval_days, last_watered_at
    UI wants:       name, daysUntilWater
    """
    if not plant:
        return plant

    plant["name"] = plant.get("nickname", "")
    plant["daysUntilWater"] = _days_until_water(
        plant.get("last_watered_at"),
        plant.get("watering_interval_days") or 7,
    )
    plant["daysUntilFertilize"] = _days_until_water(
        plant.get("last_fertilized_at"),
        plant.get("fertilizing_interval_days") or 30,
    )
    plant["daysUntilRepot"] = _days_until_water(
        plant.get("last_repotted_at"),
        plant.get("repotting_interval_days") or 365,
    )
    return plant


def fetch_plants():
    """GET /plants/ -> list of plant dicts."""
    resp = requests.get(f"{API_BASE_URL}/plants/", timeout=TIMEOUT)
    plants = _handle(resp) or []
    return [_decorate(p) for p in plants]


def create_plant(nickname: str, species: str, location: str):
    """POST /plants/ -> the newly created plant dict."""
    payload = {
        "nickname": nickname,
        "species": species,
        "location": location or None,
        "watering_interval_days": 7,
    }
    resp = requests.post(f"{API_BASE_URL}/plants/", json=payload, timeout=TIMEOUT)
    return _decorate(_handle(resp))


def water_plant(plant_id):
    """
    Mark a plant as watered right now.

    The backend has no dedicated /water endpoint - watering is just a
    partial update that sets last_watered_at to the current time.
    """
    payload = {"last_watered_at": datetime.now(timezone.utc).isoformat()}
    resp = requests.put(
        f"{API_BASE_URL}/plants/{plant_id}", json=payload, timeout=TIMEOUT
    )
    return _decorate(_handle(resp))

def fertilize_plant(plant_id):
    """Mark a plant as fertilized right now."""
    payload = {"last_fertilized_at": datetime.now(timezone.utc).isoformat()}
    resp = requests.put(
        f"{API_BASE_URL}/plants/{plant_id}", json=payload, timeout=TIMEOUT
    )
    return _decorate(_handle(resp))


def repot_plant(plant_id):
    """Mark a plant as repotted right now."""
    payload = {"last_repotted_at": datetime.now(timezone.utc).isoformat()}
    resp = requests.put(
        f"{API_BASE_URL}/plants/{plant_id}", json=payload, timeout=TIMEOUT
    )
    return _decorate(_handle(resp))


def delete_plant(plant_id):
    #DELETE /plants/{id} -> None."""
    resp = requests.delete(f"{API_BASE_URL}/plants/{plant_id}", timeout=TIMEOUT)
    return _handle(resp)

def login(email, password):
    #POST /login -> user data dict or auth token.
    
    payload = {
        "email": email,
        "password": password
    }
    resp = requests.post(f"{API_BASE_URL}/login", json=payload, timeout=TIMEOUT)
    return _handle(resp)


def register(email, password):
    #POST /register -> newly created user data dict.
    
    payload = {
        "email": email,
        "password": password
    }
    resp = requests.post(f"{API_BASE_URL}/register", json=payload, timeout=TIMEOUT)
    return _handle(resp)


def upload_plant_photo(plant_id, file_path):
    """
    sends one image file to POST /plants/{id}/photo
    comes back with the updated plant dict which now has photo_url on it

    the server only takes jpeg, png and webp, and it rejects anything
    bigger than 5 mb
    """
    # work out the content type from the file extension so the server
    # knows what it is getting. falls back to jpeg if we cannot tell
    mime = mimetypes.guess_type(file_path)[0] or "image/jpeg"
    filename = os.path.basename(file_path)

    # this goes up as multipart form data, not json, because it is a file
    with open(file_path, "rb") as fh:
        resp = requests.post(
            f"{API_BASE_URL}/plants/{plant_id}/photo",
            files={"file": (filename, fh, mime)},
            timeout=TIMEOUT,
        )

    return _decorate(_handle(resp))