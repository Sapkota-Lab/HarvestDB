from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1.endpoints import record_images
from app.db.session import get_db, get_test_db, verify_test_db_connection
from app.main import app
from app.models.field import Field
from app.models.harvest_event import HarvestEvent
from app.models.harvest_record import HarvestRecord
from app.models.record_image import RecordImage
from app.services import storage_service

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _session_local():
    from app.db.session import testingSessionLocal

    return testingSessionLocal


def _image_count(image_id: int) -> int:
    db = _session_local()()
    try:
        return len(list(db.scalars(select(RecordImage).where(RecordImage.id == image_id))))
    finally:
        db.close()


@pytest.fixture()
def client():
    if not verify_test_db_connection():
        pytest.skip("Testing database is not available. Run TEST_DB_SETUP.sh first.")

    app.dependency_overrides[get_db] = get_test_db
    created_field_ids: list[int] = []

    with TestClient(app) as test_client:
        yield test_client, created_field_ids

    db = _session_local()()
    try:
        for field_id in created_field_ids:
            for event in db.scalars(select(HarvestEvent).where(HarvestEvent.field_id == field_id)):
                for record in db.scalars(
                    select(HarvestRecord).where(HarvestRecord.harvest_event_id == event.id)
                ):
                    db.delete(record)
                db.flush()
                db.delete(event)
                db.flush()
            field = db.get(Field, field_id)
            if field is not None:
                db.delete(field)
        db.commit()
    finally:
        db.close()
    app.dependency_overrides.clear()


def _make_record(test_client, created_field_ids) -> int:
    db = _session_local()()
    try:
        field = Field(name=f"img-test-{uuid4().hex[:8]}")
        db.add(field)
        db.flush()
        event = HarvestEvent(field_id=field.id, harvest_date=date(2026, 9, 17))
        db.add(event)
        db.commit()
        created_field_ids.append(field.id)
        event_id = event.id
    finally:
        db.close()
    response = test_client.post(
        f"/api/v1/harvest-records/?harvest_event_id={event_id}", json={"plot_number": "A1"}
    )
    return response.json()["id"]


def test_detect_image_type():
    assert storage_service.detect_image_type(PNG_BYTES) == "image/png"
    assert storage_service.detect_image_type(b"\xff\xd8\xff\xe0abc") == "image/jpeg"
    assert storage_service.detect_image_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert storage_service.detect_image_type(b"not an image") is None


def test_upload_list_get_delete_image(client):
    test_client, field_ids = client
    record_id = _make_record(test_client, field_ids)

    response = test_client.post(
        f"/api/v1/harvest-records/{record_id}/images",
        data={"category": "Leaf", "caption": "blight"},
        files=[("files", ("leaf.png", PNG_BYTES, "image/png"))],
    )
    assert response.status_code == 201
    image = response.json()[0]
    assert image["category"] == "Leaf"
    assert image["content_type"] == "image/png"

    listed = test_client.get(f"/api/v1/harvest-records/{record_id}/images").json()
    assert [i["id"] for i in listed] == [image["id"]]

    fetched = test_client.get(f"/api/v1/harvest-records/images/{image['id']}")
    assert fetched.status_code == 200
    assert fetched.content == PNG_BYTES

    deleted = test_client.delete(f"/api/v1/harvest-records/images/{image['id']}")
    assert deleted.status_code == 204
    assert _image_count(image["id"]) == 0


def test_upload_rejects_non_image(client):
    test_client, field_ids = client
    record_id = _make_record(test_client, field_ids)
    response = test_client.post(
        f"/api/v1/harvest-records/{record_id}/images",
        files=[("files", ("x.png", b"plain text", "image/png"))],
    )
    assert response.status_code == 400


def test_upload_rejects_oversized(client, monkeypatch):
    test_client, field_ids = client
    record_id = _make_record(test_client, field_ids)
    monkeypatch.setattr(record_images.settings, "max_image_bytes", 16)
    response = test_client.post(
        f"/api/v1/harvest-records/{record_id}/images",
        files=[("files", ("big.png", PNG_BYTES, "image/png"))],
    )
    assert response.status_code == 413


def test_upload_unknown_record(client):
    test_client, _ = client
    response = test_client.post(
        "/api/v1/harvest-records/999999/images",
        files=[("files", ("a.png", PNG_BYTES, "image/png"))],
    )
    assert response.status_code == 404


def test_deleting_record_removes_images(client):
    test_client, field_ids = client
    record_id = _make_record(test_client, field_ids)
    image_id = test_client.post(
        f"/api/v1/harvest-records/{record_id}/images",
        files=[("files", ("a.png", PNG_BYTES, "image/png"))],
    ).json()[0]["id"]
    assert _image_count(image_id) == 1
    assert test_client.delete(f"/api/v1/harvest-records/{record_id}").status_code == 204
    assert _image_count(image_id) == 0
