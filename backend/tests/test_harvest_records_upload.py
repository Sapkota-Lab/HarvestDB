from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _upload(csv_text: str, filename: str = "records.csv"):
    return client.post(
        "/api/v1/harvest-records/upload",
        params={"harvest_event_id": 1},
        files={"file": (filename, csv_text, "text/csv")},
    )


def test_upload_parses_valid_rows() -> None:
    csv_text = (
        "serial_number,genotype,location,harvest,grade_1_marketable_weight,grade_1_marketable_count\n"
        "SN-1,Genotype A,Row 1,H1,12.5,10\n"
        "SN-2,Genotype B,Row 2,H1,,\n"
    )

    response = _upload(csv_text)

    assert response.status_code == 200
    records = response.json()
    assert len(records) == 2
    assert records[0]["serial_number"] == "SN-1"
    assert records[0]["harvest_event_id"] == 1
    assert records[1]["grade_1_marketable_weight"] is None


def test_upload_rejects_non_csv_file() -> None:
    response = client.post(
        "/api/v1/harvest-records/upload",
        params={"harvest_event_id": 1},
        files={"file": ("records.txt", "genotype\nA\n", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_rejects_row_missing_required_field() -> None:
    csv_text = "serial_number,genotype\nSN-1,\n"

    response = _upload(csv_text)

    assert response.status_code == 400
    assert "Row 2" in response.json()["detail"]
