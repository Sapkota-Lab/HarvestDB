from fastapi import APIRouter

from app.api.v1.endpoints import auth, crops, exports, fields, health, harvests, record_images

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(fields.router, prefix="/fields", tags=["fields"])
api_router.include_router(harvests.router, prefix="/harvests", tags=["harvests"])
api_router.include_router(crops.router, prefix="/harvest-records", tags=["harvest-records"])
api_router.include_router(record_images.router, prefix="/harvest-records", tags=["record-images"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
