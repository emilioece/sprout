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
    return plant


def fetch_plants():
    """GET /plants/ -> list of plant dicts."""
    resp = requests.get(f"{API_BASE_URL}/plants/", timeout=TIMEOUT)
    plants = _handle(resp) or []
    return [_decorate(p) for p in plants]


def create_plant(nickname, species, location, care_guide=None,
                 light_requirement=None):
    payload = {
        "nickname": nickname,
        "species": species,
        "location": location or None,
    }

    # when a guide is present the server takes the watering interval from it,
    # so we do not send a hard coded one alongside it
    if care_guide:
        payload["care_guide"] = care_guide
    if light_requirement:
        payload["light_requirement"] = light_requirement

    resp = requests.post(f"{API_BASE_URL}/plants/", json=payload,
                         timeout=TIMEOUT)
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


# ---------------------------------------------------------------------------
# phone upload over the local network
# ---------------------------------------------------------------------------

def lan_ip():
    """
    finds the ip address other devices on the wifi can reach this computer on

    opens a udp socket pointed at a public address and asks the os which
    local interface it would use. nothing is actually sent, it just makes
    the os pick a route for us
    """
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


def start_phone_upload():
    """asks the backend for a token and builds the url the phone should open"""
    resp = requests.post(f"{API_BASE_URL}/m/new", timeout=TIMEOUT)
    data = _handle(resp)
    token = data["token"]
    port = API_BASE_URL.rsplit(":", 1)[-1]
    return token, f"http://{lan_ip()}:{port}/m/{token}"


def phone_upload_ready(token):
    """true once the phone has sent a photo. the desktop polls this"""
    resp = requests.get(f"{API_BASE_URL}/m/{token}/status", timeout=TIMEOUT)
    return bool(_handle(resp).get("ready"))


def download_phone_photo(token, dest_dir=None):
    """
    pulls the staged photo down to a temp file and gives back its path

    the extension has to match what the file actually is. gemini is told the
    mime type based on the file name, so saving a png as .jpg makes it send
    png bytes labelled as jpeg, and gemini then reports the photo is not a
    plant. the content type header is trusted first, and the magic bytes at
    the start of the file are used as a fallback
    """
    import os
    import tempfile

    resp = requests.get(f"{API_BASE_URL}/m/{token}/file", timeout=30)
    if not resp.ok:
        raise ApiError(f"{resp.status_code} {resp.reason}")

    data = resp.content

    by_content_type = {
        "image/png": ".png",
        "image/webp": ".webp",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
    }
    ext = by_content_type.get((resp.headers.get("content-type") or "").lower())

    # every image format starts with its own signature, so this works even
    # when the server sends no useful headers at all
    if ext is None:
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = ".png"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            ext = ".webp"
        else:
            ext = ".jpg"

    fd, path = tempfile.mkstemp(prefix="sprout_phone_", suffix=ext, dir=dest_dir)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    return path


def make_qr_png(url, dest_path):
    """renders the url as a qr code png that kivy can show in an Image widget"""
    import qrcode
    img = qrcode.make(url)
    img.save(dest_path)
    return dest_path


# ---------------------------------------------------------------------------
# ai features
# ---------------------------------------------------------------------------

def identify_plant(file_path):
    """
    POST /plants/identify -> what plant is in this photo

    comes back with species, a confidence between 0 and 1, whether it looks
    like a plant at all, some alternative guesses, and a light hint.

    note the form field is called image here, not file. the plant photo
    endpoint uses file, so they are not interchangeable
    """
    mime = mimetypes.guess_type(file_path)[0] or "image/jpeg"
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as fh:
        resp = requests.post(
            f"{API_BASE_URL}/plants/identify",
            files={"image": (filename, fh, mime)},
            timeout=60,          # vision calls are slower than normal requests
        )

    return _handle(resp)


def health_check(plant_id, symptoms, soil_moisture=None, light=None):
    """
    POST /plants/{id}/health-check -> a triage for one plant

    this one is text based. it needs a plant that already exists, because the
    server builds the prompt from that plant's species, location and watering
    history as well as the symptoms typed in
    """
    payload = {"symptoms": symptoms}
    if soil_moisture:
        payload["soil_moisture"] = soil_moisture
    if light:
        payload["light"] = light

    resp = requests.post(
        f"{API_BASE_URL}/plants/{plant_id}/health-check",
        json=payload,
        timeout=60,
    )
    return _handle(resp)

def get_care_preview(species, nickname=None):
    """
    POST /plants/care-preview -> a full care guide for a species

    this runs before the plant is saved, so the schedule shown in the add
    plant form is the real one rather than a placeholder. the guide is then
    sent along with the plant on create, and the backend pulls the watering
    interval out of it
    """
    payload = {"species": species}
    if nickname:
        payload["name"] = nickname

    resp = requests.post(
        f"{API_BASE_URL}/plants/care-preview",
        json=payload,
        timeout=60,          # gemini takes a few seconds
    )
    return _handle(resp)