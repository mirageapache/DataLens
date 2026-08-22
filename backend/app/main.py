from fastapi import FastAPI

from app.core.config import settings
from app.routes.datasets import router as datasets_router
from app.routes.analysis import router as analysis_router

app = FastAPI(title=settings.app_name)
app.include_router(datasets_router)
app.include_router(analysis_router)


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
