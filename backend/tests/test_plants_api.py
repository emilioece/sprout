# Tests for /plants CRUD + water endpoints


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
