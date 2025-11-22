from datetime import UTC, datetime
import re
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException, status
from sqlmodel import Session, select

from . import models, schemas


_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    slug = _NON_ALNUM_RE.sub("-", value.lower()).strip("-")
    return slug or "channel"


def _extract_playlist_id(value: str) -> str:
    playlist_input = (value or "").strip()
    if not playlist_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube playlist identifier is required",
        )
    if playlist_input.startswith(("http://", "https://")):
        parsed = urlparse(playlist_input)
        query = parse_qs(parsed.query)
        playlist_id = query.get("list", [None])[0]
        if not playlist_id:
            # fallback: last segment if looks like playlist id
            path_parts = [segment for segment in parsed.path.split("/") if segment]
            for segment in reversed(path_parts):
                if segment.startswith(("PL", "UU", "OL", "LL")):
                    playlist_id = segment
                    break
        if not playlist_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract playlist id from URL",
            )
        return playlist_id
    return playlist_input


def _get_or_create_channel(
    session: Session,
    *,
    job_name: str,
    channel_description: str | None = None,
) -> tuple[models.Channel, bool]:
    slug = _slugify(job_name or "")
    channel = session.exec(
        select(models.Channel).where(models.Channel.slug == slug)
    ).one_or_none()
    created = False
    if channel is None:
        channel = models.Channel(
            slug=slug,
            title=job_name or slug,
            description=channel_description,
        )
        session.add(channel)
        session.commit()
        session.refresh(channel)
        created = True
    return channel, created


def _create_or_update_playlist(
    session: Session,
    *,
    channel: models.Channel,
    playlist_id: str,
    job_name: str,
    castopod_slug: str | None,
    castopod_uuid: str | None,
) -> tuple[models.Playlist, bool]:
    playlist = session.exec(
        select(models.Playlist).where(models.Playlist.youtube_playlist_id == playlist_id)
    ).one_or_none()
    created = False
    if playlist is None:
        playlist = models.Playlist(
            youtube_playlist_id=playlist_id,
            title=job_name or playlist_id,
            channel_id=channel.id,
            is_active=True,
            castopod_slug=castopod_slug,
            castopod_uuid=castopod_uuid,
        )
        session.add(playlist)
        session.commit()
        session.refresh(playlist)
        created = True
    else:
        updated = False
        if playlist.channel_id != channel.id:
            playlist.channel_id = channel.id
            updated = True
        if castopod_slug and playlist.castopod_slug != castopod_slug:
            playlist.castopod_slug = castopod_slug
            updated = True
        if castopod_uuid and playlist.castopod_uuid != castopod_uuid:
            playlist.castopod_uuid = castopod_uuid
            updated = True
        if job_name and not playlist.title:
            playlist.title = job_name
            updated = True
        if updated:
            playlist.updated_at = datetime.now(UTC)
            session.add(playlist)
            session.commit()
            session.refresh(playlist)
    return playlist, created


# ----- Channel -----

def list_channels(session: Session) -> list[models.Channel]:
    return session.exec(select(models.Channel)).all()


def create_channel(session: Session, data: schemas.ChannelCreate) -> models.Channel:
    existing = session.exec(
        select(models.Channel).where(models.Channel.slug == data.slug)
    ).one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel with slug '{data.slug}' already exists",
        )
    channel = models.Channel(**data.model_dump())
    session.add(channel)
    session.commit()
    session.refresh(channel)
    return channel


def get_channel(session: Session, channel_id: int) -> models.Channel:
    channel = session.get(models.Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


def update_channel(session: Session, channel_id: int, data: schemas.ChannelUpdate) -> models.Channel:
    channel = get_channel(session, channel_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)
    channel.updated_at = datetime.now(UTC)
    session.add(channel)
    session.commit()
    session.refresh(channel)
    return channel


def delete_channel(session: Session, channel_id: int) -> None:
    channel = get_channel(session, channel_id)
    session.delete(channel)
    session.commit()


# ----- Playlist -----

def list_playlists(session: Session) -> list[models.Playlist]:
    return session.exec(select(models.Playlist)).all()


def create_playlist(session: Session, data: schemas.PlaylistCreate) -> models.Playlist:
    _ = get_channel(session, data.channel_id)
    existing = session.exec(
        select(models.Playlist).where(
            models.Playlist.youtube_playlist_id == data.youtube_playlist_id
        )
    ).one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Playlist already registered",
        )
    playlist = models.Playlist(**data.model_dump())
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    return playlist


def get_playlist(session: Session, playlist_id: int) -> models.Playlist:
    playlist = session.get(models.Playlist, playlist_id)
    if playlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    return playlist


def update_playlist(session: Session, playlist_id: int, data: schemas.PlaylistUpdate) -> models.Playlist:
    playlist = get_playlist(session, playlist_id)
    update_data = data.model_dump(exclude_unset=True)
    if "channel_id" in update_data:
        _ = get_channel(session, update_data["channel_id"])
    for key, value in update_data.items():
        setattr(playlist, key, value)
    playlist.updated_at = datetime.now(UTC)
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    return playlist


def delete_playlist(session: Session, playlist_id: int) -> None:
    playlist = get_playlist(session, playlist_id)
    session.delete(playlist)
    session.commit()


# ----- Schedule -----

def list_schedules(session: Session) -> list[models.Schedule]:
    return session.exec(select(models.Schedule)).all()


def create_schedule(session: Session, data: schemas.ScheduleCreate) -> models.Schedule:
    _ = get_playlist(session, data.playlist_id)
    schedule = models.Schedule(**data.model_dump())
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def get_schedule(session: Session, schedule_id: int) -> models.Schedule:
    schedule = session.get(models.Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return schedule


def update_schedule(session: Session, schedule_id: int, data: schemas.ScheduleUpdate) -> models.Schedule:
    schedule = get_schedule(session, schedule_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)
    schedule.updated_at = datetime.now(UTC)
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def delete_schedule(session: Session, schedule_id: int) -> None:
    schedule = get_schedule(session, schedule_id)
    session.delete(schedule)
    session.commit()


# ----- Run -----

def list_runs(session: Session) -> list[models.Run]:
    return session.exec(select(models.Run).order_by(models.Run.started_at.desc())).all()


def create_run(session: Session, data: schemas.RunCreate) -> models.Run:
    _ = get_playlist(session, data.playlist_id)
    run = models.Run(**data.model_dump())
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: int) -> models.Run:
    run = session.get(models.Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


def update_run(session: Session, run_id: int, data: schemas.RunUpdate) -> models.Run:
    run = get_run(session, run_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(run, key, value)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def delete_run(session: Session, run_id: int) -> None:
    run = get_run(session, run_id)
    session.delete(run)
    session.commit()


# ----- Jobs -----

def list_jobs(session: Session) -> list[models.Job]:
    return session.exec(select(models.Job).order_by(models.Job.created_at.asc())).all()


def create_job(session: Session, data: schemas.JobCreate) -> models.Job:
    _ = get_playlist(session, data.playlist_id)
    job = models.Job(**data.model_dump())
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job(session: Session, job_id: int) -> models.Job:
    job = session.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


def update_job(session: Session, job_id: int, data: schemas.JobUpdate) -> models.Job:
    job = get_job(session, job_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job, key, value)
    job.updated_at = datetime.now(UTC)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def delete_job(session: Session, job_id: int) -> None:
    job = get_job(session, job_id)
    session.delete(job)
    session.commit()


def quick_create_job(
    session: Session,
    data: schemas.JobQuickCreateRequest,
) -> schemas.JobQuickCreateResponse:
    playlist_id = _extract_playlist_id(data.youtube_playlist)
    channel, created_channel = _get_or_create_channel(
        session,
        job_name=data.job_name,
        channel_description=data.channel_description,
    )
    playlist, created_playlist = _create_or_update_playlist(
        session,
        channel=channel,
        playlist_id=playlist_id,
        job_name=data.job_name,
        castopod_slug=data.castopod_slug,
        castopod_uuid=data.castopod_uuid,
    )
    job = models.Job(
        playlist_id=playlist.id,
        action="sync",
        status="queued",
        castopod_slug=data.castopod_slug or playlist.castopod_slug,
        castopod_playlist_uuid=data.castopod_uuid or playlist.castopod_uuid,
        note=data.note,
        should_castopod_upload=data.should_castopod_upload,
        progress_total=0,
        progress_completed=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return schemas.JobQuickCreateResponse(
        channel=channel,
        playlist=playlist,
        job=job,
        created_channel=created_channel,
        created_playlist=created_playlist,
    )
