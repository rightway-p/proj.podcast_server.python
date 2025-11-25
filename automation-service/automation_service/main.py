from contextlib import asynccontextmanager
from datetime import UTC, datetime

import os
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

from .api.routes import castopod, channels, playlists, runs, schedules, jobs, pipeline
from .config import get_settings
from .database import init_db
from .scheduler import schedule_runner
from .queue_runner import queue_runner
from .schemas import HealthRead


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.scheduler_enabled:
        schedule_runner.start()
    if settings.queue_runner_enabled:
        queue_runner.start()
    try:
        yield
    finally:
        if settings.scheduler_enabled:
            schedule_runner.stop()
        if settings.queue_runner_enabled:
            queue_runner.stop()
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

download_root = Path(settings.download_root).expanduser().resolve()
download_root.mkdir(parents=True, exist_ok=True)
app.mount("/downloads", StaticFiles(directory=str(download_root), check_dir=False), name="downloads")


@app.get("/downloads-browser", response_class=HTMLResponse)
def downloads_browser(path: str = Query(default="")) -> HTMLResponse:
    target = (download_root / path).resolve()
    if download_root not in target.parents and target != download_root:
        raise HTTPException(status_code=404, detail="Not Found")
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not Found")
    if target.is_file():
        rel = target.relative_to(download_root).as_posix()
        return RedirectResponse(url=f"/downloads/{rel}", status_code=302)
    parent_link = ""
    if target != download_root:
        rel_parent = target.parent.relative_to(download_root).as_posix()
        parent_href = f"/downloads-browser?path={quote(rel_parent)}"
        parent_link = f'<li><a href="{parent_href}">../</a></li>'
    rows = []
    for entry in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        rel = entry.relative_to(download_root).as_posix()
        if entry.is_dir():
            href = f"/downloads-browser?path={quote(rel)}"
            rows.append(f'<li>📁 <a href="{href}">{entry.name}/</a></li>')
        else:
            href = f"/downloads/{quote(rel)}"
            rows.append(f'<li>📄 <a href="{href}" target="_blank">{entry.name}</a></li>')
    html = f"""
    <html>
      <head>
        <meta charset='utf-8'/>
        <title>Downloads</title>
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 1rem; }}
          ul {{ list-style: none; padding-left: 0; }}
          li {{ margin: 0.25rem 0; }}
        </style>
      </head>
      <body>
        <h2>Downloads /{path}</h2>
        <ul>
          {parent_link}
          {''.join(rows) if rows else '<li>비어 있음</li>'}
        </ul>
      </body>
    </html>
    """
    return HTMLResponse(html)
