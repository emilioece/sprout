import requests

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


def fetch_plants():
    """GET /plants -> list of plant dicts."""
    resp = requests.get(f"{API_BASE_URL}/plants", timeout=TIMEOUT)
    return _handle(resp)


def create_plant(nickname: str, species: str, location: str):
    """POST /plants -> the newly created plant dict."""
    payload = {"nickname": nickname, "species": species, "location": location}
    resp = requests.post(f"{API_BASE_URL}/plants", json=payload, timeout=TIMEOUT)
    return _handle(resp)


def water_plant(plant_id):
    """PATCH /plants/{id}/water -> the updated plant dict."""
    resp = requests.patch(f"{API_BASE_URL}/plants/{plant_id}/water", timeout=TIMEOUT)
    return _handle(resp)


def delete_plant(plant_id):
    """DELETE /plants/{id} -> None."""
    resp = requests.delete(f"{API_BASE_URL}/plants/{plant_id}", timeout=TIMEOUT)
    return _handle(resp)