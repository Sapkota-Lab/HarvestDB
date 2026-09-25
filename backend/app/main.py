from fastapi import FastAPI
from starlette.responses import RedirectResponse

from app.api.v1.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app

#This will redirct to the swagger docs page for faster testing in development
app = create_app()

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url = "/docs")
