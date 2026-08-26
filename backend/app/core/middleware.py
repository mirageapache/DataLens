import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.db import SessionLocal
from app.models.log import SystemLog

logger = logging.getLogger("datalens.access")

# Paths excluded from logging to reduce high-frequency noise in Grafana (Fix #10 edge-case)
_SKIP_PATHS: frozenset[str] = frozenset({"/api/v1/health"})


def _write_log_to_db(
    level: str,
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: int,
    error_detail: str | None,
) -> None:
    """Synchronous DB write.

    Extracted as a top-level function so it can be executed in a
    thread-pool executor (via asyncio.to_thread) without blocking the
    async event loop. (Fix #5)
    """
    # Fix #6: use explicit None initialisation instead of `'db' in locals()`
    db = None
    try:
        db = SessionLocal()
        system_log = SystemLog(
            level=level,
            # Fix #9: populate message with a human-readable summary
            message=f"{method} {endpoint} → {status_code}",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            error_detail=error_detail,
        )
        db.add(system_log)
        db.commit()
    except Exception as db_exc:
        logger.error("Failed to save system log to database: %s", db_exc)
    finally:
        if db is not None:  # Fix #6
            db.close()


class StructuredLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip noisy utility endpoints (Fix #10 — avoid polluting log with health-checks)
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        # Fix #1: initialise response to None so type-checker and runtime agree
        status_code: int = 500
        error_detail: str | None = None
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            error_detail = str(exc)
            raise  # re-raise so FastAPI's exception handlers still work
        finally:
            duration_ms = int((time.time() - start_time) * 1000)

            if status_code >= 500:
                level = "ERROR"
            elif status_code >= 400:
                level = "WARN"
            else:
                level = "INFO"

            log_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "error_detail": error_detail,
            }

            # Fix #8: emit at the correct Python log level, not always INFO
            _log_fn = {
                "ERROR": logger.error,
                "WARN": logger.warning,
            }.get(level, logger.info)
            _log_fn(json.dumps(log_data))

            # Fix #5: run sync DB write in a thread pool — never blocks the event loop
            await asyncio.to_thread(
                _write_log_to_db,
                level,
                endpoint,
                method,
                status_code,
                duration_ms,
                error_detail,
            )

        # Fix #1: only reached when no exception propagated (response is guaranteed set)
        return response  # type: ignore[return-value]
