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
        "plot_number,dynamic_data\n"
        'A-1,"{""genotype"": ""G1"", ""count"": 10}"\n'
        "A-2,\n"
    )

    response = _upload(csv_text)

    assert response.status_code == 200
    records = response.json()
    assert len(records) == 2
    assert records[0]["plot_number"] == "A-1"
    assert records[0]["harvest_event_id"] == 1
    assert records[0]["dynamic_data"] == {"genotype": "G1", "count": 10}
    assert records[1]["dynamic_data"] == {}


def test_upload_rejects_non_csv_file() -> None:
    response = client.post(
        "/api/v1/harvest-records/upload",
        params={"harvest_event_id": 1},
        files={"file": ("records.txt", "genotype\nA\n", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_rejects_missing_required_column() -> None:
    csv_text = "dynamic_data\n{}\n"

    response = _upload(csv_text)

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing required column: plot_number"


def test_upload_rejects_invalid_dynamic_data() -> None:
    response = _upload("plot_number,dynamic_data\nA-1,not-json\n")

    assert response.status_code == 400
    assert response.json()["detail"] == "Row 2: dynamic_data must be valid JSON"
