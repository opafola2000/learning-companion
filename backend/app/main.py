import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.config import get_settings
from app.database import engine, Base
from app.database_migrate import run_migrations
from app.models import *  # noqa: F401, F403 — ensures all models are registered
from app.routers import auth, curriculum, resources, quiz, progress, feedback
from app.middleware.security import SecurityHeadersMiddleware
from app.limiter import limiter


logger = logging.getLogger(__name__)


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)


def _safe_init_database() -> None:
    try:
        init_database()
    except Exception:
        logger.exception("Database initialization failed; API will start but DB features may be unavailable")


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, _safe_init_database)
    yield


app = FastAPI(
    title="Learning Companion Agent",
    description="AI-powered learning companion for professional certification exam preparation",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(curriculum.router)
app.include_router(resources.router)
app.include_router(quiz.router)
app.include_router(progress.router)
app.include_router(feedback.router)


@app.get("/api/health")
def health_check():
    # Keep this fast — App Runner health checks often time out at ~5s.
    # Do not probe the database here.
    return {"status": "healthy", "service": "learning-companion", "version": "2.0.0"}


@app.get("/api/trust")
def trust_info():
    return {
        "disclaimer": (
            "Curriculum and quizzes are AI-generated from official exam objectives and "
            "documentation with source citations. Always verify against the latest official "
            "exam guide before your test date."
        ),
        "features": [
            "Source-grounded curriculum generation",
            "Automated content validation",
            "Exam blueprint versioning",
            "Spaced repetition recommendations",
            "Audit logging and rate limiting",
        ],
    }


# Serve React static files in production (must be after API routes)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
