from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta, time
from threading import Event, Thread
from zoneinfo import ZoneInfo

from sqlalchemy.orm import selectinload
from sqlmodel import select

from .database import session_scope
from . import models
from .pipeline_runner import pipeline_manager
from .config import get_settings


logger = logging.getLogger(__name__)


class ScheduleRunner:
    """Background worker that checks schedules and triggers pipeline runs."""

    def __init__(self, interval_seconds: int = 60) -> None:
        self._interval = interval_seconds
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        logger.info("Starting schedule runner (interval=%ss)", self._interval)
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._thread:
            return
        logger.info("Stopping schedule runner")
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Schedule runner tick failed: %s", exc)
            self._stop_event.wait(self._interval)

    def _tick(self) -> None:
        now_utc = datetime.now(UTC)
        with session_scope() as session:
            schedules = session.exec(
                select(models.Schedule)
                .where(models.Schedule.is_active == True)  # noqa: E712
                .options(selectinload(models.Schedule.playlist))
            ).all()
            for schedule in schedules:
                if not schedule.days_of_week:
                    continue
                playlist = schedule.playlist
                if playlist is None:
                    playlist = session.get(models.Playlist, schedule.playlist_id)
                if playlist is None:
                    logger.warning("Schedule %s references missing playlist %s", schedule.id, schedule.playlist_id)
                    continue
                if not playlist.is_active:
                    logger.info(
                        "Skipping schedule %s because playlist %s is inactive",
                        schedule.id,
                        playlist.id,
                    )
                    continue
                if not self._should_run(schedule, now_utc):
                    continue
                if not self._ensure_job_for_playlist(session, playlist):
                    continue
                triggered = self._trigger_pipeline(schedule)
                if triggered:
                    schedule.last_run_at = datetime.now(UTC)
                    schedule.next_run_at = self._compute_next_run(schedule)
                    session.add(schedule)
            session.commit()

    def _ensure_job_for_playlist(self, session, playlist: models.Playlist) -> bool:
        pending_status = {"queued", "cancelling", "in_progress"}
        existing = session.exec(
            select(models.Job).where(
                (models.Job.playlist_id == playlist.id)
                & (models.Job.status.in_(pending_status))
            )
        ).first()
        if existing:
            return True
        job = models.Job(
            playlist_id=playlist.id,
            action="sync",
            status="queued",
            castopod_slug=playlist.castopod_slug,
            castopod_playlist_uuid=playlist.castopod_uuid,
            should_castopod_upload=bool(playlist.castopod_slug or playlist.castopod_uuid),
            note="스케줄 자동 실행",
        )
        session.add(job)
        session.flush()
        logger.info("Enqueued job %s for playlist %s via schedule", job.id, playlist.id)
        return True

    def _trigger_pipeline(self, schedule: models.Schedule) -> bool:
        try:
            pipeline_manager.trigger()
            logger.info("Triggered pipeline via schedule %s", schedule.id)
            return True
        except RuntimeError as exc:
            logger.warning(
                "Schedule %s skipped because pipeline is busy: %s", schedule.id, exc
            )
        except Exception as exc:  # pragma: no cover - runtime logging
            logger.exception("Failed to trigger pipeline for schedule %s: %s", schedule.id, exc)
        return False

    def _parse_run_time(self, run_time: str) -> time:
        hour, minute = (run_time or "00:00").split(":")
        return time(hour=int(hour), minute=int(minute))

    def _should_run(self, schedule: models.Schedule, now_utc: datetime) -> bool:
        try:
            run_time = self._parse_run_time(schedule.run_time)
        except ValueError:
            logger.warning("Invalid run_time '%s' on schedule %s", schedule.run_time, schedule.id)
            return False
        timezone = schedule.timezone or "UTC"
        try:
            tz = ZoneInfo(timezone)
        except Exception:  # pragma: no cover - fallback for invalid tz
            tz = ZoneInfo("UTC")
        now_local = now_utc.astimezone(tz)
        day_key = now_local.strftime("%a").lower()
        normalized_days = {day.lower() for day in schedule.days_of_week}
        if day_key not in normalized_days:
            return False
        target_local = datetime.combine(now_local.date(), run_time, tzinfo=tz)
        if now_local < target_local:
            return False
        if schedule.last_run_at:
            last_local = schedule.last_run_at.astimezone(tz)
            if last_local.date() == now_local.date() and last_local >= target_local:
                return False
        return True

    def _compute_next_run(self, schedule: models.Schedule) -> datetime | None:
        normalized_days = [day.lower() for day in schedule.days_of_week]
        if not normalized_days:
            return None
        try:
            run_time = self._parse_run_time(schedule.run_time)
        except ValueError:
            return None
        timezone = schedule.timezone or "UTC"
        try:
            tz = ZoneInfo(timezone)
        except Exception:  # pragma: no cover - fallback for invalid tz
            tz = ZoneInfo("UTC")
        now_local = datetime.now(tz)
        for offset in range(1, 15):
            candidate = now_local + timedelta(days=offset)
            day_key = candidate.strftime("%a").lower()
            if day_key not in normalized_days:
                continue
            run_dt = datetime.combine(candidate.date(), run_time, tzinfo=tz)
            return run_dt.astimezone(UTC)
        return None


_settings = get_settings()
schedule_runner = ScheduleRunner(interval_seconds=_settings.scheduler_interval_seconds)
