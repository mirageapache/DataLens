from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name)


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
