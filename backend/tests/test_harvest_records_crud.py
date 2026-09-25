from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_db, get_test_db, verify_test_db_connection
from app.main import app
from app.models.field import Field
from app.models.harvest_event import HarvestEvent
from app.models.harvest_record import HarvestRecord


def _session_local():
    from app.db.session import testingSessionLocal

    return testingSessionLocal


@pytest.fixture()
def client():
    if not verify_test_db_connection():
        pytest.skip("Testing database is not available. Run TEST_DB_SETUP.sh first.")

    app.dependency_overrides[get_db] = get_test_db
    created_field_ids: list[int] = []
    SessionLocal = _session_local()

    with TestClient(app) as test_client:
        yield test_client, created_field_ids

    db = SessionLocal()
    try:
        for field_id in created_field_ids:
            events = db.scalars(
                select(HarvestEvent).where(HarvestEvent.field_id == field_id)
            ).all()
            for event in events:
                records = db.scalars(
                    select(HarvestRecord).where(HarvestRecord.harvest_event_id == event.id)
                ).all()
                for record in records:
                    db.delete(record)
                db.delete(event)
            field = db.get(Field, field_id)
            if field is not None:
                db.delete(field)
        db.commit()
    finally:
        db.close()

    app.dependency_overrides.clear()


def _make_harvest_event(created_field_ids: list[int]) -> int:
    db = _session_local()()
    try:
        field = Field(name=f"crud-test-{uuid4().hex[:8]}")
        db.add(field)
        db.flush()
        harvest_event = HarvestEvent(field_id=field.id, harvest_date=date(2026, 9, 17))
        db.add(harvest_event)
        db.commit()
        db.refresh(harvest_event)
        created_field_ids.append(field.id)
        return harvest_event.id
    finally:
        db.close()


def test_create_harvest_record(client) -> None:
    test_client, created_field_ids = client
    harvest_event_id = _make_harvest_event(created_field_ids)

    response = test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-1", "dynamic_data": {"genotype": "G1"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] is not None
    assert body["harvest_event_id"] == harvest_event_id
    assert body["plot_number"] == "A-1"
    assert body["dynamic_data"] == {"genotype": "G1"}


def test_list_harvest_records(client) -> None:
    test_client, created_field_ids = client
    harvest_event_id = _make_harvest_event(created_field_ids)

    test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-1", "dynamic_data": {}},
    )
    test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-2", "dynamic_data": {"count": 3}},
    )

    response = test_client.get(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_filters_by_harvest_event_id(client) -> None:
    test_client, created_field_ids = client
    event_a = _make_harvest_event(created_field_ids)

    db = _session_local()()
    try:
        field = db.get(Field, created_field_ids[-1])
        event_b = HarvestEvent(field_id=field.id, harvest_date=date(2026, 9, 18))
        db.add(event_b)
        db.commit()
        db.refresh(event_b)
        event_b_id = event_b.id
    finally:
        db.close()

    test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": event_a},
        json={"plot_number": "A-1", "dynamic_data": {}},
    )
    test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": event_b_id},
        json={"plot_number": "B-1", "dynamic_data": {}},
    )

    response = test_client.get(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": event_a},
    )

    assert response.status_code == 200
    records = response.json()
    assert len(records) == 1
    assert records[0]["plot_number"] == "A-1"
    assert records[0]["harvest_event_id"] == event_a


def test_update_harvest_record(client) -> None:
    test_client, created_field_ids = client
    harvest_event_id = _make_harvest_event(created_field_ids)

    created = test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-1", "dynamic_data": {"genotype": "G1"}},
    ).json()

    response = test_client.patch(
        f"/api/v1/harvest-records/{created['id']}",
        json={"plot_number": "A-9", "dynamic_data": {"genotype": "G2"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plot_number"] == "A-9"
    assert body["dynamic_data"] == {"genotype": "G2"}


def test_delete_harvest_record(client) -> None:
    test_client, created_field_ids = client
    harvest_event_id = _make_harvest_event(created_field_ids)

    created = test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-1", "dynamic_data": {}},
    ).json()

    delete_response = test_client.delete(f"/api/v1/harvest-records/{created['id']}")
    assert delete_response.status_code == 204

    list_response = test_client.get(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
    )
    assert list_response.json() == []


def test_update_missing_record_returns_404(client) -> None:
    test_client, _created_field_ids = client

    response = test_client.patch(
        "/api/v1/harvest-records/2147483647",
        json={"plot_number": "X"},
    )

    assert response.status_code == 404


def test_delete_missing_record_returns_404(client) -> None:
    test_client, _created_field_ids = client

    response = test_client.delete("/api/v1/harvest-records/2147483647")

    assert response.status_code == 404


def test_create_rejects_missing_harvest_event(client) -> None:
    test_client, _created_field_ids = client

    response = test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": 2147483647},
        json={"plot_number": "A-1", "dynamic_data": {}},
    )

    assert response.status_code == 404


def test_patch_rejects_null_dynamic_data(client) -> None:
    test_client, created_field_ids = client
    harvest_event_id = _make_harvest_event(created_field_ids)

    created = test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-1", "dynamic_data": {"genotype": "G1"}},
    ).json()

    response = test_client.patch(
        f"/api/v1/harvest-records/{created['id']}",
        json={"dynamic_data": None},
    )

    assert response.status_code == 422


def test_patch_clears_dynamic_data_with_empty_object(client) -> None:
    test_client, created_field_ids = client
    harvest_event_id = _make_harvest_event(created_field_ids)

    created = test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-1", "dynamic_data": {"genotype": "G1"}},
    ).json()

    response = test_client.patch(
        f"/api/v1/harvest-records/{created['id']}",
        json={"dynamic_data": {}},
    )

    assert response.status_code == 200
    assert response.json()["dynamic_data"] == {}


def test_empty_patch_rejected(client) -> None:
    test_client, created_field_ids = client
    harvest_event_id = _make_harvest_event(created_field_ids)

    created = test_client.post(
        "/api/v1/harvest-records/",
        params={"harvest_event_id": harvest_event_id},
        json={"plot_number": "A-1", "dynamic_data": {}},
    ).json()

    response = test_client.patch(f"/api/v1/harvest-records/{created['id']}", json={})

    assert response.status_code == 400
    assert "No fields to update" in response.json()["detail"]
