"""API route handlers for RallyCal."""

import hashlib
import hmac
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from ..config.manager import ConfigManager
from ..core.logging import get_logger
from ..core.settings import Settings, get_settings
from ..database.engine import get_db_session
from ..generators.ical import ICalGenerator

logger = get_logger(__name__)
router = APIRouter()


async def get_config_manager() -> ConfigManager:
    """Get configuration manager dependency."""
    return ConfigManager()


async def get_ical_generator() -> ICalGenerator:
    """Get iCal generator dependency."""
    return ICalGenerator()


@router.get("/calendar.ics", response_class=PlainTextResponse)
async def get_calendar_feed(
    request: Request,
    response: Response,
    config_manager: ConfigManager = Depends(get_config_manager),
    generator: ICalGenerator = Depends(get_ical_generator),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Generate and serve the aggregated calendar feed.

    Returns a standards-compliant iCal feed combining all configured calendar sources.
    """
    try:
        logger.info(
            "Calendar feed requested",
            client_ip=request.client.host if request.client else None,
        )

        # Generate the calendar feed
        calendar_data = await generator.generate_calendar()

        # Set appropriate headers for iCal content
        response.headers["Content-Type"] = "text/calendar; charset=utf-8"
        response.headers["Content-Disposition"] = 'attachment; filename="rallycal.ics"'
        response.headers["Cache-Control"] = (
            f"public, max-age={settings.calendar.cache_ttl}"
        )

        # Generate ETag for caching
        etag = hashlib.md5(calendar_data.encode()).hexdigest()
        response.headers["ETag"] = f'"{etag}"'

        # Check if client has cached version
        if request.headers.get("if-none-match") == f'"{etag}"':
            response.status_code = 304
            return ""

        logger.info(
            "Calendar feed generated successfully", size_bytes=len(calendar_data)
        )
        return calendar_data

    except Exception as exc:
        logger.error("Failed to generate calendar feed", exc_info=exc)
        raise HTTPException(
            status_code=500, detail="Failed to generate calendar feed"
        ) from exc


@router.get("/health")
async def health_check(response: Response) -> dict[str, Any]:
    """
    Comprehensive health check with dependency validation.

    Checks database connectivity, configuration file accessibility,
    and other critical dependencies.
    """
    health_status = {
        "status": "healthy",
        "timestamp": str(time.time()),
        "checks": {},
    }

    try:
        # Check database connectivity
        async with get_db_session() as db:
            await db.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
    except Exception as exc:
        logger.error("Database health check failed", exc_info=exc)
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"

    try:
        # Check configuration file
        config_manager = ConfigManager()
        await config_manager.load_config()
        health_status["checks"]["config"] = "healthy"
    except Exception as exc:
        logger.error("Configuration health check failed", exc_info=exc)
        health_status["checks"]["config"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        response.status_code = 503

    return health_status


@router.get("/health/ready")
async def readiness_check() -> dict[str, str]:
    """
    Kubernetes-style readiness probe.

    Returns 200 if the application is ready to serve traffic.
    """
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Kubernetes-style liveness probe.

    Returns 200 if the application is running and should not be restarted.
    """
    return {"status": "alive"}


@router.post("/webhooks/config")
async def handle_config_webhook(
    request: Request,
    config_manager: ConfigManager = Depends(get_config_manager),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """
    Handle Git webhook for configuration updates.

    Validates webhook signature and triggers configuration reload
    when calendar configuration files are updated.
    """
    # Get request body for signature verification
    body = await request.body()

    # Verify webhook signature if secret is configured
    if settings.security.webhook_secret:
        signature = request.headers.get("x-hub-signature-256")
        if not signature:
            logger.warning("Webhook request missing signature")
            raise HTTPException(status_code=401, detail="Missing webhook signature")

        # Verify HMAC signature
        expected_signature = hmac.new(
            settings.security.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, f"sha256={expected_signature}"):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        # Parse webhook payload
        payload = await request.json()

        # Check if this is a relevant push event
        if payload.get("ref") == "refs/heads/main":
            # Check if calendar config files were modified
            commits = payload.get("commits", [])
            config_modified = any(
                "config/calendars.yaml" in commit.get("modified", [])
                or "config/calendars.yaml" in commit.get("added", [])
                for commit in commits
            )

            if config_modified:
                logger.info("Configuration file updated via webhook, reloading")
                await config_manager.reload_config()
                return {"status": "configuration reloaded"}

        return {"status": "no action needed"}

    except Exception as exc:
        logger.error("Webhook processing failed", exc_info=exc)
        raise HTTPException(
            status_code=500, detail="Webhook processing failed"
        ) from exc


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """
    Basic metrics endpoint for monitoring.

    Returns application metrics in a simple JSON format.
    Future: Can be extended to support Prometheus format.
    """
    # TODO: Implement comprehensive metrics collection
    return {
        "app_info": {
            "name": "rallycal",
            "version": "0.1.0",
        },
        "http_requests_total": 0,  # Placeholder for request counter
        "calendar_generation_duration_seconds": 0,  # Placeholder for timing
        "active_calendar_sources": 0,  # Placeholder for source count
    }
