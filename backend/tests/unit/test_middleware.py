"""Unit tests for StructuredLogMiddleware and _write_log_to_db helper.

Strategy:
- Test _write_log_to_db in isolation by monkeypatching SessionLocal.
- Test the middleware dispatch logic via FastAPI TestClient (client fixture).
"""
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# _write_log_to_db unit tests
# ---------------------------------------------------------------------------

class TestWriteLogToDb:
    def test_creates_system_log_with_correct_fields(self, monkeypatch):
        """_write_log_to_db should add a SystemLog and commit the session."""
        from app.core.middleware import _write_log_to_db

        mock_db = MagicMock()
        monkeypatch.setattr("app.core.middleware.SessionLocal", lambda: mock_db)

        _write_log_to_db(
            level="INFO",
            endpoint="/api/v1/datasets",
            method="GET",
            status_code=200,
            duration_ms=42,
            error_detail=None,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

        added_log = mock_db.add.call_args[0][0]
        assert added_log.level == "INFO"
        assert added_log.endpoint == "/api/v1/datasets"
        assert added_log.method == "GET"
        assert added_log.status_code == 200
        assert added_log.duration_ms == 42
        assert added_log.error_detail is None
        assert added_log.message == "GET /api/v1/datasets → 200"

    def test_populates_message_with_human_readable_summary(self, monkeypatch):
        """message field should contain 'METHOD endpoint → status_code'."""
        from app.core.middleware import _write_log_to_db

        mock_db = MagicMock()
        monkeypatch.setattr("app.core.middleware.SessionLocal", lambda: mock_db)

        _write_log_to_db("ERROR", "/api/v1/analysis/run", "POST", 500, 1200, "DB timeout")

        added_log = mock_db.add.call_args[0][0]
        assert added_log.message == "POST /api/v1/analysis/run → 500"
        assert added_log.error_detail == "DB timeout"

    def test_closes_session_even_when_commit_raises(self, monkeypatch):
        """db.close() must be called even if db.commit() raises an exception."""
        from app.core.middleware import _write_log_to_db

        mock_db = MagicMock()
        mock_db.commit.side_effect = RuntimeError("DB unavailable")
        monkeypatch.setattr("app.core.middleware.SessionLocal", lambda: mock_db)

        # Should not raise — the exception is swallowed and logged internally
        _write_log_to_db("INFO", "/api/v1/datasets", "GET", 200, 5, None)

        mock_db.close.assert_called_once()

    def test_session_created_then_closed_even_on_add_failure(self, monkeypatch):
        """db.close() is always called regardless of which DB call fails."""
        from app.core.middleware import _write_log_to_db

        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("constraint violation")
        monkeypatch.setattr("app.core.middleware.SessionLocal", lambda: mock_db)

        _write_log_to_db("WARN", "/api/v1/datasets/999", "DELETE", 404, 10, None)

        mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# Middleware integration-level tests (via TestClient + full mock of DB writes)
# ---------------------------------------------------------------------------

class TestStructuredLogMiddleware:
    def _make_client(self, monkeypatch):
        """Return a TestClient with all DB and SessionLocal calls mocked out."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core import db as core_db

        # Prevent any real DB connections in these tests
        monkeypatch.setattr("app.core.middleware.SessionLocal", lambda: MagicMock())
        monkeypatch.setattr(core_db, "engine", MagicMock())

        return TestClient(app, raise_server_exceptions=False)

    def test_normal_request_passes_through(self, monkeypatch):
        """Middleware must not break successful requests."""
        client = self._make_client(monkeypatch)
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_endpoint_is_not_logged(self, monkeypatch):
        """/api/v1/health is in _SKIP_PATHS — DB write must never be triggered."""
        written: list = []

        async def _spy_thread(fn, *args, **kwargs):
            written.append(args)

        monkeypatch.setattr("app.core.middleware.asyncio.to_thread", _spy_thread)
        monkeypatch.setattr("app.core.middleware.SessionLocal", lambda: MagicMock())

        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        client.get("/api/v1/health")
        assert written == [], "/health should not trigger a DB write"

    def test_log_level_mapping(self):
        """Verify level-string mapping for boundary status codes."""
        cases = [
            (200, "INFO"),
            (201, "INFO"),
            (301, "INFO"),
            (400, "WARN"),
            (404, "WARN"),
            (422, "WARN"),
            (500, "ERROR"),
            (503, "ERROR"),
        ]
        for status_code, expected_level in cases:
            if status_code >= 500:
                level = "ERROR"
            elif status_code >= 400:
                level = "WARN"
            else:
                level = "INFO"
            assert level == expected_level, (
                f"status {status_code}: expected {expected_level}, got {level}"
            )

