import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth, submissions, surveys, sync, users

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for KBS Toolbox — an offline-first survey & data collection platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Minimal in-process rate limiting (per client IP, sliding 60s window) ---
# For multi-instance production deployments, replace this with a shared store
# (e.g. Redis) behind the same interface; this in-memory version is sufficient
# for a single-instance deployment or local/dev use.
_request_log: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
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


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(surveys.router)
app.include_router(submissions.router)
app.include_router(sync.router)


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
