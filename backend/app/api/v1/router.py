from fastapi import APIRouter, Depends
from app.api.v1.endpoints import auth, crops, exports, fields, health, harvests, record_images, seed_inventory
from app.core.security import get_current_user

api_router = APIRouter()
protected = [Depends(get_current_user)]
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(health.router, tags=["health"], dependencies=protected)
api_router.include_router(fields.router, prefix="/fields", tags=["fields"], dependencies=protected)
api_router.include_router(harvests.router, prefix="/harvests", tags=["harvests"],dependencies=protected)
api_router.include_router(crops.router, prefix="/harvest-records", tags=["harvest-records"],dependencies=protected)
api_router.include_router(record_images.router, prefix="/harvest-records", tags=["record-images"], dependencies=protected)
api_router.include_router(exports.router, prefix="/exports", tags=["exports"],dependencies=protected)
api_router.include_router(seed_inventory.router, prefix="/seeds", tags=["seed-inventory"],dependencies=protected)