from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, inspect

from app.db.session import (
    get_db,
    get_test_db,
    verify_test_db_connection,
    testingSessionLocal,
    testengine,
)
from app.main import app
from app.models.seed_inventory import SeedInventory


BASE_URL = "/api/v1/seeds"


# --------------------------------------------------
# Test database setup and cleanup
# --------------------------------------------------

@pytest.fixture()
def client():
    if not verify_test_db_connection():
        pytest.skip(
            "Testing database is not available."
        )

    # Make sure we are testing against testing_db
    with testengine.connect() as connection:
        database_name = connection.exec_driver_sql(
            "SELECT current_database()"
        ).scalar_one()

    assert database_name == "testing_db", (
        f"Refusing to run tests against {database_name}"
    )

    # Verify the table exists
    assert inspect(testengine).has_table("seed_inventory"), (
        "seed_inventory table does not exist in testing_db."
    )

    # Unique crop type for this test's records
    test_crop = f"pytest-tomato-{uuid4().hex[:8]}"

    # Override the main database with the testing database
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = get_test_db

    try:
        with TestClient(app) as test_client:
            yield test_client, test_crop

    finally:
        # Only delete records created by this test
        db = testingSessionLocal()

        try:
            db.execute(
                delete(SeedInventory).where(
                    SeedInventory.crop_type == test_crop
                )
            )
            db.commit()

        finally:
            db.close()

            if previous_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous_override


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def _seed_data(crop_type):
    return {
        "crop_type": crop_type,
        "variety_name": "Roma",
        "breeding_line": "R12",
        "seed_weight_g": "25.5000",
        "seed_count": 150,
        "date_recorded": "2026-11-05T12:00:00+00:00",
        "notes": "Seed inventory test",
    }


def _make_seed(test_client, crop_type):
    response = test_client.post(
        f"{BASE_URL}/",
        json=_seed_data(crop_type),
    )

    assert response.status_code in (200, 201), response.text

    return response.json()["id"]


# --------------------------------------------------
# Test 1: Create a seed inventory record
# --------------------------------------------------

def test_create_seed_inventory(client):
    test_client, crop_type = client

    response = test_client.post(
        f"{BASE_URL}/",
        json=_seed_data(crop_type),
    )

    assert response.status_code in (200, 201)

    data = response.json()

    assert data["crop_type"] == crop_type
    assert data["variety_name"] == "Roma"
    assert data["seed_count"] == 150
    assert "id" in data


# --------------------------------------------------
# Test 2: Retrieve all seed inventory records
# --------------------------------------------------

def test_get_seed_inventory(client):
    test_client, crop_type = client

    seed_id = _make_seed(test_client, crop_type)

    response = test_client.get(f"{BASE_URL}/")

    assert response.status_code == 200

    seeds = response.json()

    assert isinstance(seeds, list)
    assert any(seed["id"] == seed_id for seed in seeds)


# --------------------------------------------------
# Test 3: Retrieve seed inventory by ID
# --------------------------------------------------

def test_get_seed_inventory_by_id(client):
    test_client, crop_type = client

    seed_id = _make_seed(test_client, crop_type)

    response = test_client.get(
        f"{BASE_URL}/{seed_id}"
    )

    assert response.status_code == 200

    seed = response.json()

    assert seed["id"] == seed_id
    assert seed["crop_type"] == crop_type
    assert seed["variety_name"] == "Roma"


# --------------------------------------------------
# Test 4: Update seed inventory using PUT
# --------------------------------------------------

def test_update_seed_inventory(client):
    test_client, crop_type = client

    seed_id = _make_seed(test_client, crop_type)

    updated_data = _seed_data(crop_type)
    updated_data["seed_count"] = 200
    updated_data["seed_weight_g"] = "30.5000"
    updated_data["notes"] = "Updated seed inventory"

    response = test_client.put(
        f"{BASE_URL}/{seed_id}",
        json=updated_data,
    )

    assert response.status_code in (200, 204), response.text

    # Retrieve the record to verify changes
    response = test_client.get(
        f"{BASE_URL}/{seed_id}"
    )

    assert response.status_code == 200

    seed = response.json()

    assert seed["seed_count"] == 200
    assert float(seed["seed_weight_g"]) == 30.5
    assert seed["notes"] == "Updated seed inventory"


# --------------------------------------------------
# Test 5: Delete seed inventory record
# --------------------------------------------------

def test_delete_seed_inventory(client):
    test_client, crop_type = client

    seed_id = _make_seed(test_client, crop_type)

    response = test_client.delete(
        f"{BASE_URL}/{seed_id}"
    )

    assert response.status_code in (200, 204), response.text

    # Verify the record was deleted
    response = test_client.get(
        f"{BASE_URL}/{seed_id}"
    )

    assert response.status_code == 404


# --------------------------------------------------
# Test 6: Retrieve nonexistent seed inventory
# --------------------------------------------------

def test_get_unknown_seed_inventory(client):
    test_client, _ = client

    response = test_client.get(
        f"{BASE_URL}/2147483647"
    )

    assert response.status_code == 404


# --------------------------------------------------
# Test 7: Reject missing required crop type
# --------------------------------------------------

def test_create_seed_missing_crop_type(client):
    test_client, crop_type = client

    data = _seed_data(crop_type)
    del data["crop_type"]

    response = test_client.post(
        f"{BASE_URL}/",
        json=data,
    )

    assert response.status_code == 422


# --------------------------------------------------
# Test 8: Reject negative seed count
# --------------------------------------------------

def test_create_seed_negative_count(client):
    test_client, crop_type = client

    data = _seed_data(crop_type)
    data["seed_count"] = -10

    response = test_client.post(
        f"{BASE_URL}/",
        json=data,
    )

    assert response.status_code == 422