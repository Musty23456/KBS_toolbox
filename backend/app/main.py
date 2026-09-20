import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.routers import analytics, audit, auth, devices, exports, locations, map as map_router, media, reviews, submissions, surveys, sync, translations, users

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for KBS Toolbox — an offline-first survey & data collection platform.",
    version="1.0.0",
)

# --- Minimal in-process rate limiting (per client IP, sliding 60s window) ---
# For multi-instance production deployments, replace this with a shared store
# (e.g. Redis) behind the same interface; this in-memory version is sufficient
# for a single-instance deployment or local/dev use.
_request_log: dict[str, deque] = defaultdict(deque)


async def rate_limit_middleware(request: Request, call_next):
    # Never rate-limit CORS preflight requests — browsers send these
    # automatically and blocking them breaks cross-origin requests entirely.
    if request.method == "OPTIONS":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = _request_log[client_ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."},
        )
    window.append(now)
    return await call_next(request)


# Order matters: middleware added last runs first (outermost). We add the
# rate limiter first and CORS last, so CORS ends up outermost and its
# headers are attached even to responses the rate limiter short-circuits
# (like a 429) — otherwise the browser reports those as generic network
# errors instead of showing the real status.
from starlette.middleware.base import BaseHTTPMiddleware

app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# translations.router must be included BEFORE surveys.router: both define
# routes under /api/surveys/..., and FastAPI matches routes in registration
# order. translations.router's static GET /api/surveys/languages would
# otherwise be shadowed by surveys.router's GET /api/surveys/{survey_id},
# which greedily matches "languages" as a survey id and 404s.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(translations.router)
app.include_router(surveys.router)
app.include_router(submissions.router)
app.include_router(reviews.router)
app.include_router(sync.router)
app.include_router(media.router)
app.include_router(devices.router)
app.include_router(locations.router)
app.include_router(map_router.router)
app.include_router(exports.router)
app.include_router(analytics.router)
app.include_router(audit.router)


@app.on_event("startup")
def on_startup():
    # In production, schema changes should go through Alembic migrations
    # (see alembic/). create_all is safe here because it only creates
    # missing tables — it never alters or drops existing ones — which keeps
    # first-run/local/dev/test setup simple.
    Base.metadata.create_all(bind=engine)

    # SEED_DEMO_DATA=true creates the demo admin/supervisor/enumerator
    # accounts and three example published surveys, so a fresh deployment
    # has something to sign in with and test against immediately. Seeding
    # is idempotent (it skips any user/survey that already exists by
    # email/title), so it's safe to leave this flag on.
    if settings.SEED_DEMO_DATA:
        from app.seed import run as run_seed

        run_seed()


@app.get("/", tags=["health"])
def root():
    return {"service": settings.APP_NAME, "status": "ok"}


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "healthy", "environment": settings.APP_ENV}
