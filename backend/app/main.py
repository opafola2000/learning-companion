from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.database import engine, Base
from app.models import *  # noqa: F401, F403 — ensures all models are registered
from app.routers import auth, curriculum, resources, quiz, progress


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Learning Companion Agent",
    description="AI-powered learning companion for professional certification exam preparation",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",")]
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

# Serve React static files in production
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "learning-companion"}
