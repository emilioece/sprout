# Tests for AI routes (Gemini mocked — no API key needed)

from unittest.mock import patch

from app.schemas.care_guide import (
    ActionStep,
    CareGuideResponse,
    ChatResponse,
    FertilizingPlan,
    HealthCheckResponse,
    PossibleCause,
    RepottingGuide,
    WateringSchedule,
)
from app.schemas.identify import PlantIdentification


def _sample_care_guide():
    return CareGuideResponse(
            name="Maria",
            species="Tagetes",
            watering_schedule=WateringSchedule(
                    interval_days=7,
                    method_summary="Water when top inch is dry",
                    how_to_check_if_due=["Finger test"],
                    ),
            fertilizing=FertilizingPlan(
                    interval_days=30,
                    fertilizer_type="balanced liquid",
                    dilution_or_strength="half strength",
                    ),
            repotting=RepottingGuide(
                    interval_months=12,
                    best_season="spring",
                    pot_size_change="one size up",
                    soil_mix=["potting mix"],
                    step_by_step=["Remove plant", "Repot"],
                    ),
            )


def _sample_health_check():
    return HealthCheckResponse(
            urgency="moderate",
            summary="Likely overwatering",
            possible_causes=[
                PossibleCause(
                        title="Overwatering",
                        rationale="Soil stays wet",
                        confidence=0.8,
                        ),
                ],
            recommended_actions=[
                ActionStep(
                        title="Let soil dry",
                        instructions="Skip watering for a few days",
                        when="Now",
                        ),
                ],
            )


def _sample_chat():
    return ChatResponse(
            reply="Water when the top inch of soil is dry.",
            suggested_next_actions=["Check soil moisture tomorrow"],
            )


def test_care_guide_not_found(client):
    response = client.post("/plants/9999/care-guide")
    assert response.status_code == 404


@patch("app.routers.ai.generate_json", return_value=_sample_care_guide())
def test_care_guide_returns_200(mock_generate_json, client, sample_plant_payload):
    created = client.post("/plants/", json=sample_plant_payload).json()
    plant_id = created["id"]

    response = client.post(f"/plants/{plant_id}/care-guide")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Maria"
    assert data["watering_schedule"]["interval_days"] == 7
    mock_generate_json.assert_called_once()


def test_health_check_not_found(client):
    response = client.post(
            "/plants/9999/health-check",
            json={"symptoms": "Yellow leaves"},
            )
    assert response.status_code == 404


@patch("app.routers.ai.generate_json", return_value=_sample_health_check())
def test_health_check_returns_200(mock_generate_json, client, sample_plant_payload):
    created = client.post("/plants/", json=sample_plant_payload).json()
    plant_id = created["id"]

    response = client.post(
            f"/plants/{plant_id}/health-check",
            json={"symptoms": "Yellow leaves for a week"},
            )
    assert response.status_code == 200

    data = response.json()
    assert data["urgency"] == "moderate"
    mock_generate_json.assert_called_once()


def test_chat_not_found(client):
    response = client.post(
            "/plants/9999/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
            )
    assert response.status_code == 404


@patch("app.routers.ai.generate_json", return_value=_sample_chat())
def test_chat_returns_200(mock_generate_json, client, sample_plant_payload):
    created = client.post("/plants/", json=sample_plant_payload).json()
    plant_id = created["id"]

    response = client.post(
            f"/plants/{plant_id}/chat",
            json={"messages": [{"role": "user", "content": "How often should I water?"}]},
            )
    assert response.status_code == 200

    data = response.json()
    assert "Water" in data["reply"]
    mock_generate_json.assert_called_once()


# Patch swaps out Gemini so we only test the route + schema wiring
@patch("app.routers.ai.generate_json", return_value=_sample_care_guide())
def test_care_preview_returns_200(mock_generate_json, client):
    response = client.post(
            "/plants/care-preview",
            json={"species": "Tagetes", "name": "Maria"},
            )
    assert response.status_code == 200

    data = response.json()
    assert data["species"] == "Tagetes"
    assert data["watering_schedule"]["interval_days"] == 7
    mock_generate_json.assert_called_once()


def test_care_preview_requires_species(client):
    response = client.post("/plants/care-preview", json={})
    assert response.status_code == 422


def _sample_identification():
    return PlantIdentification(
            species="Fern",
            confidence=0.86,
            is_plant=True,
            )


# Patch swaps out Gemini so we only test the route + schema wiring
@patch("app.routers.ai.generate_json", return_value=_sample_identification())
def test_identify_returns_200(mock_generate_json, client):
    response = client.post(
            "/plants/identify",
            files={"image": ("fern.jpg", b"fake-image-bytes", "image/jpeg")},
            )
    assert response.status_code == 200

    data = response.json()
    assert data["species"] == "Fern"
    assert data["confidence"] == 0.86
    assert data["is_plant"] is True
    mock_generate_json.assert_called_once()
    # Vision path should pass image bytes through to Gemini helper
    assert mock_generate_json.call_args.kwargs["image_bytes"] == b"fake-image-bytes"


def test_identify_rejects_unsupported_type(client):
    response = client.post(
            "/plants/identify",
            files={"image": ("notes.txt", b"not-an-image", "text/plain")},
            )
    assert response.status_code == 400
