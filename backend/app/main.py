from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Fix #3: all imports at the top of the module (PEP 8)
from app.core.config import settings
from app.core.db import Base, engine
from app.core.middleware import StructuredLogMiddleware
import app.models  # noqa: F401
from app.routes.datasets import router as datasets_router
from app.routes.analysis import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# In Starlette/FastAPI, add_middleware wraps in reverse order (LIFO).
# We register StructuredLogMiddleware first so that CORSMiddleware becomes the
# outermost middleware. This ensures CORS headers are attached to all responses,
# and OPTIONS preflight requests are handled directly.
app.add_middleware(StructuredLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets_router)
app.include_router(analysis_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
