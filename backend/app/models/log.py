from datetime import datetime, timezone

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(10))  # "INFO" | "WARN" | "ERROR"
    # Human-readable summary, e.g. "GET /api/v1/datasets → 200"
    message: Mapped[str | None] = mapped_column(String(255), default=None)
    endpoint: Mapped[str]
    method: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int]
    duration_ms: Mapped[int]
    error_detail: Mapped[str | None] = mapped_column(Text, default=None)
    # Use timezone-aware UTC timestamp (datetime.utcnow is deprecated since Python 3.12)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Composite indexes to support Grafana queries (created_at range scans, status filters)
    __table_args__ = (
        Index("ix_system_logs_created_at", "created_at"),
        Index("ix_system_logs_status_code", "status_code"),
        Index("ix_system_logs_level", "level"),
    )
