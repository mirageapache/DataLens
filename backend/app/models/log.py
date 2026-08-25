import datetime as dt
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str]
    message: Mapped[str | None] = mapped_column(default=None)
    endpoint: Mapped[str]
    method: Mapped[str]
    status_code: Mapped[int]
    duration_ms: Mapped[int]
    error_detail: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
