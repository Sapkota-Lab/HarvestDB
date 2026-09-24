import csv
import io
import json

from fastapi.testclient import TestClient
from app.db.session import get_test_db, get_db
from app.main import app

app.dependency_overrides[get_db] = get_test_db #overide the get_db dependency with the get_test_db dependency for testing
client = TestClient(app)


def _export():
    return client.get("/api/v1/exports/harvest-records.csv")


def test_export_returns_csv() -> None:
    response = _export()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]


def test_export_contains_database_rows() -> None:
    response = _export()

    assert response.status_code == 200

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)

    assert len(rows) > 0

    assert "record_id" in rows[0]
    assert "field_name" in rows[0]
    assert "dynamic_harvest_data" in rows[0]


def test_export_json_data_is_valid() -> None:
    response = _export()

    assert response.status_code == 200

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)

    assert len(rows) > 0
    assert rows[0]["dynamic_harvest_data"] is not None
    
    dynamic_data = json.loads(
        rows[0]["dynamic_harvest_data"]
    )

    assert isinstance(dynamic_data, dict)