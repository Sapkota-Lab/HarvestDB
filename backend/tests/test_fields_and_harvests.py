from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import get_db, testengine
from app.main import app
from app.models.field import Field
from app.models.harvest_event import HarvestEvent


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Field.__table__.create(engine)
    HarvestEvent.__table__.create(engine)

    def database():
        with Session(engine) as db:
            yield db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides = previous
        engine.dispose()


def test_fields_are_saved_and_listed(client):
    assert client.get("/api/v1/fields/").json() == []
    response = client.post("/api/v1/fields/", json={"name": " Lexington ", "location": "Kentucky"})
    assert response.status_code == 200
    field = response.json()
    assert field["id"] > 0
    assert field["name"] == "Lexington"
    assert field["location"] == "Kentucky"
    assert client.get("/api/v1/fields/").json() == [field]


def test_duplicate_field_returns_conflict_without_breaking_later_requests(client):
    client.post("/api/v1/fields/", json={"name": "Lexington"})
    response = client.post("/api/v1/fields/", json={"name": " Lexington "})
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    assert client.post("/api/v1/fields/", json={"name": "Other field"}).status_code == 200
    assert len(client.get("/api/v1/fields/").json()) == 2


@pytest.mark.parametrize("name", ["", "   ", "A" * 129])
def test_invalid_field_names_are_rejected(client, name):
    assert client.post("/api/v1/fields/", json={"name": name}).status_code == 422
    assert client.get("/api/v1/fields/").json() == []


def test_harvests_are_saved_filtered_and_sorted(client):
    field_a = client.post("/api/v1/fields/", json={"name": "Lexington"}).json()["id"]
    field_b = client.post("/api/v1/fields/", json={"name": "Other field"}).json()["id"]
    assert client.get("/api/v1/harvests/").json() == []
    created = []
    for field_id, harvest_date in [(field_a, "2026-09-01"), (field_b, "2026-10-02"), (field_a, "2026-10-01")]:
        response = client.post(
            "/api/v1/harvests/", params={"field_id": field_id},
            json={"harvest_date": harvest_date, "harvest_number": 1, "notes": "Test harvest"},
        )
        assert response.status_code == 200
        created.append(response.json())
    assert len({harvest["id"] for harvest in created}) == 3
    assert client.get("/api/v1/harvests/", params={"field_id": field_a}).json() == [created[2], created[0]]
    assert client.get("/api/v1/harvests/", params={"field_id": field_b}).json() == [created[1]]
    assert len(client.get("/api/v1/harvests/").json()) == 3


def test_harvest_requires_an_existing_field(client):
    response = client.post("/api/v1/harvests/", params={"field_id": 999}, json={"harvest_date": "2026-10-20"})
    assert response.status_code == 404
    assert client.get("/api/v1/harvests/").json() == []


@pytest.mark.parametrize("payload", [
    {}, {"harvest_date": "2026-02-30"},
    {"harvest_date": "2026-10-20", "harvest_number": 0},
    {"harvest_date": "2026-10-20", "notes": "A" * 2049},
])
def test_invalid_harvests_are_rejected(client, payload):
    field_id = client.post("/api/v1/fields/", json={"name": "Lexington"}).json()["id"]
    assert client.post("/api/v1/harvests/", params={"field_id": field_id}, json=payload).status_code == 422
    assert client.get("/api/v1/harvests/").json() == []


def test_postgres_field_entry_workflow():
    with testengine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app) as client:
                response = client.post("/api/v1/fields/", json={"name": f"workflow-test-{uuid4().hex}"})
                assert response.status_code == 200
                field_id = response.json()["id"]
                response = client.post(
                    "/api/v1/harvests/", params={"field_id": field_id},
                    json={"harvest_date": "2026-10-20"},
                )
                assert response.status_code == 200
                event_id = response.json()["id"]
                events = client.get("/api/v1/harvests/", params={"field_id": field_id}).json()
                assert [event["id"] for event in events] == [event_id]
                response = client.post(
                    "/api/v1/harvest-records/", params={"harvest_event_id": event_id},
                    json={"plot_number": "P-1", "dynamic_data": {"weight": 12}},
                )
                assert response.status_code == 200
                response = client.post(
                    "/api/v1/harvest-records/upload", params={"harvest_event_id": event_id},
                    files={"file": ("test.csv", "plot_number\nP-2\n", "text/csv")},
                )
                assert response.status_code == 200
                response = client.get("/api/v1/harvest-records/", params={"harvest_event_id": event_id})
                assert response.status_code == 200
                assert {row["plot_number"] for row in response.json()["records"]} == {"P-1", "P-2"}
        finally:
            app.dependency_overrides = previous
            db.close()
            transaction.rollback()
