from datetime import date
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.field import Field
from app.models.harvest_event import HarvestEvent
from app.models.harvest_record import HarvestRecord


@compiles(JSONB, "sqlite")
def sqlite_jsonb(_type, _compiler, **_kwargs):
    return "JSON"


@pytest.fixture()
def database():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Field(id=1, name="Lexington"))
        db.flush()
        db.add(HarvestEvent(id=1, field_id=1, harvest_date=date(2026, 10, 23)))
        db.commit()
        yield db
    engine.dispose()


@pytest.fixture()
def client(database):
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: database
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides = previous


def _upload(client, content, filename="records.csv", event_id=1):
    return client.post(
        "/api/v1/harvest-records/upload",
        params={"harvest_event_id": event_id},
        files={"file": (filename, content, "application/octet-stream")},
    )


def test_upload_parses_valid_rows(client, database) -> None:
    csv_text = (
        "plot_number,dynamic_data\n"
        'A-1,"{""genotype"": ""G1"", ""count"": 10}"\n'
        "A-2,\n"
    )

    response = _upload(client, csv_text)

    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 2
    assert records[0]["plot_number"] == "A-1"
    assert records[0]["harvest_event_id"] == 1
    assert records[0]["dynamic_data"] == {"genotype": "G1", "count": 10}
    assert records[1]["dynamic_data"] == {}
    assert response.json()["imported_sheets"] == []
    assert response.json()["skipped_sheets"] == []
    assert database.scalar(select(func.count()).select_from(HarvestRecord)) == 2


@pytest.mark.parametrize("filename", ["records.txt", "records.xls", "records.xlsx.exe"])
def test_upload_rejects_unsupported_file(client, filename) -> None:
    response = client.post(
        "/api/v1/harvest-records/upload",
        params={"harvest_event_id": 1},
        files={"file": (filename, "genotype\nA\n", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_rejects_missing_required_column(client) -> None:
    csv_text = "dynamic_data\n{}\n"

    response = _upload(client, csv_text)

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing required column: plot_number"


def test_upload_rejects_invalid_dynamic_data(client) -> None:
    response = _upload(client, "plot_number,dynamic_data\nA-1,not-json\n")

    assert response.status_code == 400
    assert response.json()["detail"] == "Row 2: dynamic_data must be valid JSON"


def make_xlsx(rows, second_sheet=None):
    workbook = Workbook()
    workbook.active.title = "First harvest"
    for row in rows:
        workbook.active.append(row)
    if second_sheet:
        sheet = workbook.create_sheet("Other harvest")
        for row in second_sheet:
            sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_xlsx_upload_saves_numeric_and_text_plot_numbers(client, database):
    workbook = make_xlsx([
        ["plot_number", "dynamic_data"],
        [0, '{"weight": 12.5, "count": 0}'],
        [12, None],
        ["0013", "{}"],
    ])
    response = _upload(client, workbook, "records.XLSX")
    assert response.status_code == 200
    records = response.json()["records"]
    assert [record["plot_number"] for record in records] == ["0", "12", "0013"]
    assert records[0]["dynamic_data"] == {"weight": 12.5, "count": 0}
    assert records[1]["dynamic_data"] == {}
    assert all(record["harvest_event_id"] == 1 for record in records)
    assert response.json()["imported_sheets"] == [{"name": "First harvest", "record_count": 3}]
    assert response.json()["skipped_sheets"] == []
    assert database.scalar(select(func.count()).select_from(HarvestRecord)) == 3


def test_xlsx_imports_only_the_first_worksheet(client):
    workbook = make_xlsx(
        [["plot_number"], ["A-1"], [], ["A-2"]],
        second_sheet=[["plot_number"], ["B-1"]],
    )
    response = _upload(client, workbook, "records.xlsx")
    assert response.status_code == 200
    assert [record["plot_number"] for record in response.json()["records"]] == ["A-1", "A-2"]
    assert response.json()["imported_sheets"] == [{"name": "First harvest", "record_count": 2}]
    assert response.json()["skipped_sheets"] == ["Other harvest"]


def test_xlsx_summary_reports_zero_records_for_a_header_only_sheet(client):
    response = _upload(client, make_xlsx([["plot_number"]]), "records.xlsx")
    assert response.status_code == 200
    assert response.json() == {
        "records": [],
        "imported_sheets": [{"name": "First harvest", "record_count": 0}],
        "skipped_sheets": [],
    }


@pytest.mark.parametrize("rows, message", [
    ([], "header row"),
    ([["dynamic_data"], ["{}"]], "Missing required column: plot_number"),
    ([["plot_number", "plot_number"], ["A-1", "A-2"]], "must not be repeated"),
    ([["plot_number", "dynamic_data"], ["A-1", "{}"], [], ["A-2", "bad"]], "Row 4"),
    ([["plot_number", "dynamic_data"], ["A-1", "[]"]], "Row 2"),
    ([["plot_number", "dynamic_data"], [None, '{"count": 1}']], "Row 2"),
    ([["plot_number", "dynamic_data"], ["A-1", '=CONCAT("{", "}")']], "replace formulas"),
    ([["plot_number", "dynamic_data"], ["A-1", "#DIV/0!"]], "fix Excel cell errors"),
])
def test_xlsx_rejects_invalid_rows_without_saving_partial_data(client, database, rows, message):
    response = _upload(client, make_xlsx(rows), "records.xlsx")
    assert response.status_code == 400
    assert message in response.json()["detail"]
    assert database.scalar(select(func.count()).select_from(HarvestRecord)) == 0


@pytest.mark.parametrize("content", [b"", b"not an Excel workbook", b"PK\x03\x04broken"])
def test_xlsx_rejects_corrupt_files(client, content):
    response = _upload(client, content, "records.xlsx")
    assert response.status_code == 400
    assert "valid, unencrypted" in response.json()["detail"]


def test_csv_still_accepts_a_utf8_bom(client):
    response = _upload(client, "\ufeffplot_number\nA-1\n".encode("utf-8"), "records.CSV")
    assert response.status_code == 200
    assert response.json()["records"][0]["plot_number"] == "A-1"


def test_csv_rejects_invalid_encoding(client):
    response = _upload(client, b"plot_number\n\xff\n")
    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_csv_validation_does_not_save_partial_data(client, database):
    response = _upload(client, "plot_number,dynamic_data\nA-1,{}\nA-2,bad\n")
    assert response.status_code == 400
    assert database.scalar(select(func.count()).select_from(HarvestRecord)) == 0


@pytest.mark.parametrize("filename", ["records.csv", "records.xlsx"])
def test_upload_requires_an_existing_event(client, filename):
    response = _upload(client, b"", filename, event_id=999)
    assert response.status_code == 404
    assert response.json()["detail"] == "Harvest event not found"
