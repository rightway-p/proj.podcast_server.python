from __future__ import annotations

import logging
from threading import Event, Thread

from sqlmodel import select

from .config import get_settings
from .database import session_scope
from . import models
from .pipeline_runner import pipeline_manager


logger = logging.getLogger(__name__)


class QueueRunner:
    """Background worker that triggers pipeline-run whenever queued jobs exist."""

    def __init__(self, interval_seconds: int = 30) -> None:
        self._interval = interval_seconds
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        logger.info("Starting queue runner (interval=%ss)", self._interval)
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._thread:
            return
        logger.info("Stopping queue runner")
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Queue runner tick failed: %s", exc)
            self._stop_event.wait(self._interval)

    def _tick(self) -> None:
        status = pipeline_manager.status()
        if status.get("running"):
            return
        with session_scope() as session:
            job = session.exec(
                select(models.Job)
                .where(models.Job.status == "queued")
                .order_by(models.Job.created_at.asc())
            ).first()
        if job is None:
            return
        try:
            pipeline_manager.trigger()
            logger.info("Triggered pipeline for queued job %s", job.id)
        except RuntimeError as exc:
            logger.debug("Queue trigger skipped: %s", exc)
        except Exception as exc:  # pragma: no cover
            logger.exception("Queue trigger failed: %s", exc)


_settings = get_settings()
queue_runner = QueueRunner(interval_seconds=_settings.queue_runner_interval_seconds)
