from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import castopod, channels, playlists, runs, schedules, jobs, pipeline
from .config import get_settings
from .database import init_db
from .schemas import HealthRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()
default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
extra_origins = settings.cors_allow_origins
if extra_origins:
    default_origins.extend(
        [
            origin.strip()
            for origin in extra_origins.split(",")
            if origin.strip()
        ]
    )

app = FastAPI(title="Podcast Automation Service", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthRead)
def healthcheck() -> HealthRead:
    return HealthRead(status="ok", timestamp=datetime.now(UTC))


app.include_router(channels.router)
app.include_router(castopod.router)
app.include_router(playlists.router)
app.include_router(schedules.router)
app.include_router(runs.router)
app.include_router(jobs.router)
app.include_router(pipeline.router)
