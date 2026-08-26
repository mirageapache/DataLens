from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Fix #3: all imports at the top of the module (PEP 8)
from app.core.config import settings
from app.core.middleware import StructuredLogMiddleware
from app.routes.datasets import router as datasets_router
from app.routes.analysis import router as analysis_router

app = FastAPI(title=settings.app_name)

# Fix #2: middleware stack is LIFO — register CORS first so it is the
# innermost layer, then StructuredLogMiddleware as the outermost wrapper.
# Execution order at runtime: StructuredLogMiddleware → CORSMiddleware → route handler
app.add_middleware(CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLogMiddleware)

app.include_router(datasets_router)
app.include_router(analysis_router)


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
