from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db, get_test_db, verify_test_db_connection
from app.services.export_service import ExportService

router = APIRouter()

export_service = ExportService()

def require_testing_db_connection():
    if not verify_test_db_connection():
        raise HTTPException(
            status_code=503,
            detail="Testing database is not available... Please run TEST_DB_SETUP.sh First",
        )
    
@router.get("/harvest-records.csv")
def export_harvest_records_csv(
    db: Session = Depends(get_db), #SQlAlchemy Session
) -> Response:
    csv_data = export_service.harvest_records_as_csv(db)

    return Response(
        content=csv_data,
        media_type="text/csv",
        detail={
            "Content-Disposition": 'attachment; filename="harvest_records.csv"'
        },
    )

@router.get("/test-harvest-records.csv")
def export_test_harvest_records_csv(
    _: None = Depends(require_testing_db_connection), #require the testing database connection to be available before proceeding
    db: Session = Depends(get_test_db),
) -> Response:
    csv_data = export_service.harvest_records_as_csv(db)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="test_harvest_records.csv"'
        },
    )