# Tests for /plants CRUD + water endpoints

from app.models.care_guide import PlantCareGuide, PlantCareGuideItem


def test_create_plant_returns_201(client, sample_plant_payload):
    response = client.post("/plants/", json=sample_plant_payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["nickname"] == "Maria"
    assert data["species"] == "Tagetes"
    assert data["location"] == "Bedroom"
    assert data["watering_interval_days"] == 7
    assert data["light_requirement"] == "bright indirect"
    assert data["last_watered_at"] is None
    assert "created_at" in data


def test_create_plant_with_care_guide_persists_rows(client, db_session, sample_plant_payload):
    payload = {
            **sample_plant_payload,
            # Intentionally different from guide so we can prove sync
            "watering_interval_days": 99,
            "care_guide": {
                "name": "Maria",
                "species": "Tagetes",
                "watering_schedule": {
                    "interval_days": 5,
                    "method_summary": "Water when top inch is dry",
                    "how_to_check_if_due": ["Finger test"],
                    },
                "fertilizing": {
                    "interval_days": 30,
                    "fertilizer_type": "balanced liquid",
                    "dilution_or_strength": "half strength",
                    },
                "repotting": {
                    "interval_months": 12,
                    "best_season": "spring",
                    "pot_size_change": "one size up",
                    "soil_mix": ["potting mix"],
                    "step_by_step": ["Remove plant", "Repot"],
                    },
                },
            }

    response = client.post("/plants/", json=payload)
    assert response.status_code == 201

    data = response.json()
    plant_id = data["id"]
    # watering_interval_days comes from the care guide, not the raw payload field
    assert data["watering_interval_days"] == 5

    guide = db_session.query(PlantCareGuide).filter_by(plant_id=plant_id).one()
    assert guide.watering_interval_days == 5
    assert guide.fertilizer_type == "balanced liquid"
    assert guide.repotting_interval_months == 12

    items = db_session.query(PlantCareGuideItem).filter_by(care_guide_id=guide.id).all()
    assert len(items) >= 3
    texts = {item.text for item in items}
    assert "Finger test" in texts
    assert "potting mix" in texts


def test_list_plants_empty(client):
    response = client.get("/plants/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_plants_after_create(client, sample_plant_payload):
    client.post("/plants/", json=sample_plant_payload)

    response = client.get("/plants/")
    assert response.status_code == 200

    plants = response.json()
    assert len(plants) == 1
    assert plants[0]["nickname"] == "Maria"


def test_get_plant_by_id(client, sample_plant_payload):
    created = client.post("/plants/", json=sample_plant_payload).json()
    plant_id = created["id"]

    response = client.get(f"/plants/{plant_id}")
    assert response.status_code == 200
    assert response.json()["id"] == plant_id


def test_get_plant_not_found(client):
    response = client.get("/plants/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Plant not found"


def test_update_plant_partial(client, sample_plant_payload):
    created = client.post("/plants/", json=sample_plant_payload).json()
    plant_id = created["id"]

    response = client.put(
            f"/plants/{plant_id}",
            json={"nickname": "Marigold"},
            )
    assert response.status_code == 200

    data = response.json()
    assert data["nickname"] == "Marigold"
    # species should stay unchanged
    assert data["species"] == "Tagetes"


def test_update_plant_not_found(client):
    response = client.put("/plants/9999", json={"nickname": "Ghost"})
    assert response.status_code == 404


def test_delete_plant(client, sample_plant_payload):
    created = client.post("/plants/", json=sample_plant_payload).json()
    plant_id = created["id"]

    response = client.delete(f"/plants/{plant_id}")
    assert response.status_code == 204

    assert client.get(f"/plants/{plant_id}").status_code == 404


def test_delete_plant_not_found(client):
    response = client.delete("/plants/9999")
    assert response.status_code == 404


def test_water_plant_sets_last_watered_at(client, sample_plant_payload):
    created = client.post("/plants/", json=sample_plant_payload).json()
    plant_id = created["id"]
    assert created["last_watered_at"] is None

    response = client.post(f"/plants/{plant_id}/water")
    assert response.status_code == 200
    assert response.json()["last_watered_at"] is not None


def test_water_plant_not_found(client):
    response = client.post("/plants/9999/water")
    assert response.status_code == 404
