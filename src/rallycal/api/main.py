"""FastAPI application setup with middleware, CORS, and security headers."""

import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from ..core.logging import get_logger
from ..core.settings import get_settings
from ..database.engine import cleanup_database, init_database
from .routes import router

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting RallyCal application")

    # Initialize database engine
    await init_database()
    logger.info("Database engine initialized")

    yield

    # Shutdown
    logger.info("Shutting down RallyCal application")
    await cleanup_database()
    logger.info("Database engine closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Family sports calendar aggregator that combines multiple iCal/ICS feeds into a single subscribable calendar feed",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

# Rate limiting storage (in production, use Redis or database)
rate_limit_storage = defaultdict(list)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next) -> Response:
    """Basic rate limiting middleware."""
    if not settings.is_production:
        # Skip rate limiting in development
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    # Clean old requests (older than 1 minute)
    rate_limit_storage[client_ip] = [
        req_time
        for req_time in rate_limit_storage[client_ip]
        if current_time - req_time < 60
    ]

    # Check rate limit
    if len(rate_limit_storage[client_ip]) >= settings.security.rate_limit_requests:
        logger.warning(
            "Rate limit exceeded",
            client_ip=client_ip,
            requests_count=len(rate_limit_storage[client_ip]),
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
            headers={"Retry-After": "60"},
        )

    # Record request
    rate_limit_storage[client_ip].append(current_time)

    return await call_next(request)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    if settings.is_production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """Log all requests with timing information."""
    start_time = time.time()

    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    return response


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type", "ETag", "Last-Modified"],
)

# Trusted host middleware (production security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure with actual allowed hosts in production
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        method=request.method,
        url=str(request.url),
    )

    if settings.is_development:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )

    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Include API routes
app.include_router(router, prefix="/api/v1")


# Root endpoint
@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root endpoint with basic application information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "healthy",
    }


# Health check endpoint
@app.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": str(time.time())}
