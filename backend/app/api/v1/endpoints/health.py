from fastapi import APIRouter, HTTPException
from app.db.session import verify_test_db_connection

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@router.get("/test-db")
def check_test_db_connection():
    if not verify_test_db_connection():
        raise HTTPException(
            status_code=503,
            detail="Testing database is not available",
        )

    return {
        "status": "ok",
        "database": "testing_db",
    }