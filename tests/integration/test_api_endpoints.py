"""FastAPI integration tests with TestClient and endpoint validation."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.rallycal.api.main import app
from src.rallycal.core.settings import get_settings


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_root_endpoint(self, test_client: AsyncClient):
        """Test root endpoint returns basic app info."""
        response = await test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "environment" in data
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_basic_health_check(self, test_client: AsyncClient):
        """Test basic health check endpoint."""
        response = await test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self, test_client: AsyncClient):
        """Test comprehensive health check with dependencies."""
        with patch("src.rallycal.database.engine.get_database") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session

            with patch(
                "src.rallycal.config.manager.ConfigManager.load_config"
            ) as mock_config:
                mock_config.return_value = True

                response = await test_client.get("/api/v1/health")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert "checks" in data
                assert data["checks"]["database"] == "healthy"
                assert data["checks"]["config"] == "healthy"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check_database_failure(self, test_client: AsyncClient):
        """Test health check when database is unhealthy."""
        with patch("src.rallycal.database.engine.get_database") as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = await test_client.get("/api/v1/health")

            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["database"] == "unhealthy"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_readiness_probe(self, test_client: AsyncClient):
        """Test Kubernetes-style readiness probe."""
        response = await test_client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_liveness_probe(self, test_client: AsyncClient):
        """Test Kubernetes-style liveness probe."""
        response = await test_client.get("/api/v1/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestCalendarEndpoints:
    """Test calendar-related endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_calendar_feed_endpoint(self, test_client: AsyncClient):
        """Test calendar feed generation endpoint."""
        mock_calendar_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//RallyCal//RallyCal//EN
BEGIN:VEVENT
UID:test@example.com
DTSTART:20240120T100000Z
DTEND:20240120T110000Z
SUMMARY:Test Event
END:VEVENT
END:VCALENDAR"""

        with patch(
            "src.rallycal.generators.ical.ICalGenerator.generate_calendar"
        ) as mock_generate:
            mock_generate.return_value = mock_calendar_data

            response = await test_client.get("/api/v1/calendar.ics")

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/calendar; charset=utf-8"
            assert "attachment" in response.headers["content-disposition"]
            assert "rallycal.ics" in response.headers["content-disposition"]
            assert "cache-control" in response.headers
            assert "etag" in response.headers

            # Verify calendar content
            content = response.text
            assert "BEGIN:VCALENDAR" in content
            assert "Test Event" in content

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_calendar_feed_etag_caching(self, test_client: AsyncClient):
        """Test ETag caching for calendar feed."""
        mock_calendar_data = "BEGIN:VCALENDAR\nEND:VCALENDAR"

        with patch(
            "src.rallycal.generators.ical.ICalGenerator.generate_calendar"
        ) as mock_generate:
            mock_generate.return_value = mock_calendar_data

            # First request
            response1 = await test_client.get("/api/v1/calendar.ics")
            assert response1.status_code == 200
            etag = response1.headers["etag"]

            # Second request with If-None-Match header
            response2 = await test_client.get(
                "/api/v1/calendar.ics", headers={"if-none-match": etag}
            )

            assert response2.status_code == 304
            assert response2.text == ""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_calendar_feed_generation_error(self, test_client: AsyncClient):
        """Test calendar feed endpoint when generation fails."""
        with patch(
            "src.rallycal.generators.ical.ICalGenerator.generate_calendar"
        ) as mock_generate:
            mock_generate.side_effect = Exception("Calendar generation failed")

            response = await test_client.get("/api/v1/calendar.ics")

            assert response.status_code == 500
            data = response.json()
            assert "Failed to generate calendar feed" in data["detail"]


class TestWebhookEndpoints:
    """Test webhook endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_config_webhook_valid_signature(self, test_client: AsyncClient):
        """Test config webhook with valid signature."""
        import hashlib
        import hmac

        webhook_payload = {
            "ref": "refs/heads/main",
            "commits": [
                {
                    "modified": ["config/calendars.yaml"],
                    "message": "Update calendar configuration",
                }
            ],
        }

        payload_bytes = json.dumps(webhook_payload).encode()

        # Mock settings with webhook secret
        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = get_settings()
            settings.security.webhook_secret = "test-secret"
            mock_settings.return_value = settings

            # Generate valid signature
            signature = hmac.new(
                b"test-secret", payload_bytes, hashlib.sha256
            ).hexdigest()

            with patch(
                "src.rallycal.config.manager.ConfigManager.reload_config"
            ) as mock_reload:
                mock_reload.return_value = True

                response = await test_client.post(
                    "/api/v1/webhooks/config",
                    json=webhook_payload,
                    headers={"x-hub-signature-256": f"sha256={signature}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "configuration reloaded"
                mock_reload.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_config_webhook_invalid_signature(self, test_client: AsyncClient):
        """Test config webhook with invalid signature."""
        webhook_payload = {
            "ref": "refs/heads/main",
            "commits": [{"modified": ["config/calendars.yaml"]}],
        }

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = get_settings()
            settings.security.webhook_secret = "test-secret"
            mock_settings.return_value = settings

            response = await test_client.post(
                "/api/v1/webhooks/config",
                json=webhook_payload,
                headers={"x-hub-signature-256": "sha256=invalid-signature"},
            )

            assert response.status_code == 401
            data = response.json()
            assert "Invalid webhook signature" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_config_webhook_missing_signature(self, test_client: AsyncClient):
        """Test config webhook with missing signature."""
        webhook_payload = {
            "ref": "refs/heads/main",
            "commits": [{"modified": ["config/calendars.yaml"]}],
        }

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = get_settings()
            settings.security.webhook_secret = "test-secret"
            mock_settings.return_value = settings

            response = await test_client.post(
                "/api/v1/webhooks/config", json=webhook_payload
            )

            assert response.status_code == 401
            data = response.json()
            assert "Missing webhook signature" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_config_webhook_no_changes(self, test_client: AsyncClient):
        """Test config webhook when no config changes are made."""
        webhook_payload = {
            "ref": "refs/heads/main",
            "commits": [
                {
                    "modified": ["README.md"],  # No config files
                    "message": "Update documentation",
                }
            ],
        }

        response = await test_client.post(
            "/api/v1/webhooks/config", json=webhook_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no action needed"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_config_webhook_non_main_branch(self, test_client: AsyncClient):
        """Test config webhook for non-main branch."""
        webhook_payload = {
            "ref": "refs/heads/feature-branch",  # Not main branch
            "commits": [{"modified": ["config/calendars.yaml"]}],
        }

        response = await test_client.post(
            "/api/v1/webhooks/config", json=webhook_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no action needed"


class TestMetricsEndpoints:
    """Test metrics endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, test_client: AsyncClient):
        """Test metrics endpoint returns basic metrics."""
        response = await test_client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()

        assert "app_info" in data
        assert "http_requests_total" in data
        assert "calendar_generation_duration_seconds" in data
        assert "active_calendar_sources" in data

        assert data["app_info"]["name"] == "rallycal"


class TestMiddleware:
    """Test middleware functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_headers(self, test_client: AsyncClient):
        """Test that security headers are added to responses."""
        response = await test_client.get("/")

        # Check security headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-xss-protection"] == "1; mode=block"
        assert "referrer-policy" in response.headers
        assert "permissions-policy" in response.headers

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cors_headers(self, test_client: AsyncClient):
        """Test CORS headers for calendar endpoint."""
        response = await test_client.options(
            "/api/v1/calendar.ics", headers={"origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.integration
    def test_rate_limiting_in_production(self):
        """Test rate limiting middleware in production mode."""
        # Use synchronous TestClient for rate limiting test
        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = get_settings()
            settings.environment = "production"
            settings.security.rate_limit_requests = 2
            mock_settings.return_value = settings

            client = TestClient(app)

            # First two requests should succeed
            response1 = client.get("/")
            assert response1.status_code == 200

            response2 = client.get("/")
            assert response2.status_code == 200

            # Third request should be rate limited
            response3 = client.get("/")
            assert response3.status_code == 429
            assert "Rate limit exceeded" in response3.json()["detail"]
            assert "Retry-After" in response3.headers


class TestErrorHandling:
    """Test error handling and exception responses."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_404_error(self, test_client: AsyncClient):
        """Test 404 error for non-existent endpoints."""
        response = await test_client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_method_not_allowed(self, test_client: AsyncClient):
        """Test 405 error for wrong HTTP method."""
        response = await test_client.post("/")

        assert response.status_code == 405

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_internal_server_error_in_development(self, test_client: AsyncClient):
        """Test internal server error handling in development."""
        with patch("src.rallycal.api.routes.get_ical_generator") as mock_generator:
            mock_generator.side_effect = RuntimeError("Unexpected error")

            with patch("src.rallycal.core.settings.get_settings") as mock_settings:
                settings = get_settings()
                settings.debug = True
                settings.environment = "development"
                mock_settings.return_value = settings

                response = await test_client.get("/api/v1/calendar.ics")

                assert response.status_code == 500
                data = response.json()
                assert "error" in data
                assert "detail" in data  # Development mode shows details
                assert "type" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_internal_server_error_in_production(self, test_client: AsyncClient):
        """Test internal server error handling in production."""
        with patch("src.rallycal.api.routes.get_ical_generator") as mock_generator:
            mock_generator.side_effect = RuntimeError("Unexpected error")

            with patch("src.rallycal.core.settings.get_settings") as mock_settings:
                settings = get_settings()
                settings.debug = False
                settings.environment = "production"
                mock_settings.return_value = settings

                response = await test_client.get("/api/v1/calendar.ics")

                assert response.status_code == 500
                data = response.json()
                assert data["error"] == "Internal server error"
                assert "detail" not in data  # Production mode hides details


class TestRequestValidation:
    """Test request validation and input sanitization."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_webhook_invalid_json(self, test_client: AsyncClient):
        """Test webhook endpoint with invalid JSON."""
        response = await test_client.post(
            "/api/v1/webhooks/config",
            content="invalid json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_webhook_missing_content_type(self, test_client: AsyncClient):
        """Test webhook endpoint with missing content type."""
        response = await test_client.post(
            "/api/v1/webhooks/config", content='{"test": "data"}'
        )

        # Should still process if content is valid JSON
        assert response.status_code in [200, 422]
