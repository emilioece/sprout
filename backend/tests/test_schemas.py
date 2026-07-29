# Tests for Pydantic request/response schemas

import pytest
from pydantic import ValidationError

from app.schemas.plants import PlantCreate, PlantUpdate
from app.schemas.care_guide import ChatMessage, ChatRequest, HealthCheckRequest


def test_plant_create_accepts_valid_payload():
    plant = PlantCreate(
            species="Tagetes",
            nickname="Maria",
            location="Bedroom",
            watering_interval_days=7,
            light_requirement="bright indirect",
            )
    assert plant.species == "Tagetes"
    assert plant.nickname == "Maria"


def test_plant_create_requires_species_and_nickname():
    with pytest.raises(ValidationError):
        PlantCreate(nickname="Maria")

    with pytest.raises(ValidationError):
        PlantCreate(species="Tagetes")


def test_plant_create_defaults():
    plant = PlantCreate(species="Tagetes", nickname="Maria")
    assert plant.watering_interval_days == 7
    assert plant.location is None
    assert plant.light_requirement is None


def test_plant_update_allows_partial_fields():
    update = PlantUpdate(nickname="Marigold")
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"nickname": "Marigold"}


def test_health_check_request_requires_symptoms():
    req = HealthCheckRequest(symptoms="Yellow leaves for 3 days")
    assert req.symptoms == "Yellow leaves for 3 days"
    assert req.soil_moisture is None

    with pytest.raises(ValidationError):
        HealthCheckRequest()


def test_chat_request_accepts_messages():
    req = ChatRequest(
            messages=[
                ChatMessage(role="user", content="How often should I water?"),
                ],
            )
    assert len(req.messages) == 1
    assert req.messages[0].role == "user"
