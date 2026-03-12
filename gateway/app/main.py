"""
 API Gateway — Agent Chiguru AI Platform
==========================================
Central entry point for all client requests.
Handles authentication, rate limiting, and proxying to microservices.
"""

import logging
import sys

# 12-factor: logs as event stream to stdout (no file)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
    force=True,
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx

from app.routes import disease, advisory, irrigation, market, notification
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.config import get_gateway_settings
from app.users import fastapi_users, auth_backend, UserRead, UserCreate, UserUpdate

logger = logging.getLogger(__name__)
settings = get_gateway_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — initialize HTTP client pool."""
    logger.info("Gateway starting — initializing HTTP client pool")
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    yield
    logger.info("Gateway shutting down — closing HTTP client")
    await app.state.http_client.aclose()


app = FastAPI(
    title="Agent Chiguru AI Platform",
    description="API Gateway for the Agent Chiguru AI microservices platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #Allows requests from any domain for development purposes
    allow_credentials=True, #Allows cookies, authorization headers, etc.
    allow_methods=["*"], #Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], #Allows all headers (Authorization, Content-Type, etc.)
)

# ── Rate Limiter ──
app.add_middleware(RateLimiterMiddleware)

# ── FastAPI Users auth routes ──
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/v1/auth/jwt",
    tags=["Authentication"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/v1/auth",
    tags=["Authentication"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/v1/users",
    tags=["Users"],
)

# ── Business routes ──
app.include_router(disease.router, prefix="/api/v1", tags=["Disease Detection"])
app.include_router(advisory.router, prefix="/api/v1", tags=["AI Advisory"])
app.include_router(irrigation.router, prefix="/api/v1", tags=["Irrigation"])
app.include_router(market.router, prefix="/api/v1", tags=["Market Prices"])
app.include_router(notification.router, prefix="/api/v1", tags=["Notifications"])


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Aggregate health status from all downstream services."""
    client: httpx.AsyncClient = app.state.http_client
    services = {
        "disease_detection": settings.DISEASE_DETECTION_URL,
        "ai_advisory": settings.AI_ADVISORY_URL,
        "irrigation": settings.IRRIGATION_URL,
        "market_price": settings.MARKET_PRICE_URL,
        "notification": settings.NOTIFICATION_URL,
    }
    status = {}
    for name, url in services.items():
        try:
            resp = await client.get(f"{url}/health", timeout=5.0)
            status[name] = "healthy" if resp.status_code == 200 else "unhealthy"
        except Exception as e:
            status[name] = "unreachable"
            logger.warning("Health check: %s unreachable — %s", name, e)

    overall = "healthy" if all(s == "healthy" for s in status.values()) else "degraded"
    logger.info("Health check completed — overall=%s, services=%s", overall, status)
    return {"status": overall, "services": status}


@app.get("/", tags=["Root"])
async def root():
    logger.info("Root endpoint requested")
    return {
        "service": "Agent Chiguru AI — API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
    }
