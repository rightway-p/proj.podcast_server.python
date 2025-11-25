from datetime import datetime

from pydantic import BaseModel, field_validator


class ChannelCreate(BaseModel):
    slug: str
    title: str
    description: str | None = None


class ChannelUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ChannelRead(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PlaylistCreate(BaseModel):
    youtube_playlist_id: str
    title: str | None = None
    channel_id: int
    is_active: bool = True
    castopod_slug: str | None = None
    castopod_uuid: str | None = None

    @field_validator("youtube_playlist_id")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        if not value:
            msg = "playlist id cannot be empty"
            raise ValueError(msg)
        return value


class PlaylistUpdate(BaseModel):
    title: str | None = None
    channel_id: int | None = None
    is_active: bool | None = None
    castopod_slug: str | None = None
    castopod_uuid: str | None = None


class PlaylistRead(BaseModel):
    id: int
    youtube_playlist_id: str
    title: str | None
    channel_id: int
    is_active: bool
    castopod_slug: str | None
    castopod_uuid: str | None
    created_at: datetime
    updated_at: datetime


def _normalize_days(values: list[str]) -> list[str]:
    if not values:
        msg = "at least one day must be selected"
        raise ValueError(msg)
    normalized: list[str] = []
    allowed = {
        "mon": "mon",
        "monday": "mon",
        "tue": "tue",
        "tuesday": "tue",
        "wed": "wed",
        "wednesday": "wed",
        "thu": "thu",
        "thursday": "thu",
        "fri": "fri",
        "friday": "fri",
        "sat": "sat",
        "saturday": "sat",
        "sun": "sun",
        "sunday": "sun",
    }
    for raw in values:
        key = (raw or "").strip().lower()
        value = allowed.get(key)
        if value is None:
            short = key[:3]
            value = allowed.get(short)
        if value is None:
            msg = f"invalid day value '{raw}'"
            raise ValueError(msg)
        if value not in normalized:
            normalized.append(value)
    return normalized


def _validate_time(value: str) -> str:
    parts = value.split(":")
    if len(parts) != 2:
        msg = "run_time must be in HH:MM format"
        raise ValueError(msg)
    hour, minute = parts
    if not hour.isdigit() or not minute.isdigit():
        msg = "run_time must contain digits only"
        raise ValueError(msg)
    h, m = int(hour), int(minute)
    if not (0 <= h <= 23 and 0 <= m <= 59):
        msg = "run_time must be a valid 24h time"
        raise ValueError(msg)
    return f"{h:02d}:{m:02d}"


class ScheduleCreate(BaseModel):
    playlist_id: int
    days_of_week: list[str]
    run_time: str = "07:00"
    timezone: str = "Asia/Seoul"
    is_active: bool = True

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, value: list[str]) -> list[str]:
        return _normalize_days(value)

    @field_validator("run_time")
    @classmethod
    def validate_run_time(cls, value: str) -> str:
        return _validate_time(value)


class ScheduleUpdate(BaseModel):
    days_of_week: list[str] | None = None
    run_time: str | None = None
    timezone: str | None = None
    is_active: bool | None = None
    next_run_at: datetime | None = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _normalize_days(value)

    @field_validator("run_time")
    @classmethod
    def validate_run_time(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_time(value)


class ScheduleRead(BaseModel):
    id: int
    playlist_id: int
    days_of_week: list[str]
    run_time: str
    timezone: str
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RunCreate(BaseModel):
    playlist_id: int
    status: str = "pending"
    message: str | None = None
    progress_total: int | None = 0
    progress_completed: int | None = 0
    current_task: str | None = None
    progress_message: str | None = None


class RunUpdate(BaseModel):
    status: str | None = None
    finished_at: datetime | None = None
    message: str | None = None
    progress_total: int | None = None
    progress_completed: int | None = None
    current_task: str | None = None
    progress_message: str | None = None


class RunRead(BaseModel):
    id: int
    playlist_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    message: str | None
    progress_total: int
    progress_completed: int
    current_task: str | None
    progress_message: str | None


class HealthRead(BaseModel):
    status: str
    timestamp: datetime


class JobCreate(BaseModel):
    playlist_id: int
    action: str = "sync"
    status: str = "queued"
    castopod_slug: str | None = None
    castopod_playlist_uuid: str | None = None
    note: str | None = None
    should_castopod_upload: bool | None = False
    progress_total: int | None = 0
    progress_completed: int | None = 0
    current_task: str | None = None
    progress_message: str | None = None


class JobUpdate(BaseModel):
    action: str | None = None
    status: str | None = None
    castopod_slug: str | None = None
    castopod_playlist_uuid: str | None = None
    note: str | None = None
    should_castopod_upload: bool | None = None
    progress_total: int | None = None
    progress_completed: int | None = None
    current_task: str | None = None
    progress_message: str | None = None


class JobRead(BaseModel):
    id: int
    playlist_id: int
    action: str
    status: str
    castopod_slug: str | None
    castopod_playlist_uuid: str | None
    note: str | None
    should_castopod_upload: bool
    progress_total: int
    progress_completed: int
    current_task: str | None
    progress_message: str | None
    created_at: datetime
    updated_at: datetime


class CastopodPodcastRead(BaseModel):
    id: int
    uuid: str
    title: str
    slug: str


class PipelineStatus(BaseModel):
    running: bool
    pid: int | None = None
    command: str
    started_at: datetime | None = None
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_exit_code: int | None = None
    log_path: str | None = None


class JobQuickCreateRequest(BaseModel):
    job_name: str
    youtube_playlist: str
    castopod_slug: str | None = None
    castopod_uuid: str | None = None
    should_castopod_upload: bool = True
    note: str | None = None
    channel_description: str | None = None


class JobQuickCreateResponse(BaseModel):
    channel: ChannelRead
    playlist: PlaylistRead
    job: JobRead
    created_channel: bool
    created_playlist: bool
