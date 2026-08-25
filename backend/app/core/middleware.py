import time
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.db import SessionLocal
from app.models.log import SystemLog

# Optional: also output to stdout/Loki via structlog or python logging
logger = logging.getLogger("datalens.access")

class StructuredLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # Extract basic request info
        method = request.method
        endpoint = request.url.path
        
        # Default values for errors
        status_code = 500
        error_detail = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_detail = str(e)
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Determine log level
            if status_code >= 500:
                level = "ERROR"
            elif status_code >= 400:
                level = "WARN"
            else:
                level = "INFO"
                
            # Create structured log dict
            log_data = {
                "level": level,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "error_detail": error_detail,
            }
            
            # Log to stdout (Loki will pick this up from Docker logs)
            logger.info(json.dumps(log_data))
            
            # Write to database for PostgreSQL data source in Grafana
            try:
                db = SessionLocal()
                system_log = SystemLog(
                    level=level,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    error_detail=error_detail,
                )
                db.add(system_log)
                db.commit()
            except Exception as db_e:
                # Fallback if DB insert fails so it doesn't crash the request
                logger.error(f"Failed to save system log to database: {db_e}")
            finally:
                if 'db' in locals():
                    db.close()
                    
        return response
