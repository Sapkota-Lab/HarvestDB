from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.export_service import ExportService

router = APIRouter()

export_service = ExportService()


@router.get("/harvest-records.csv")
def export_harvest_records_csv(
    db: Session = Depends(get_db), #SQlAlchemy Session
) -> Response:
    csv_data = export_service.harvest_records_as_csv(db)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="harvest_records.csv"'
        },
    )