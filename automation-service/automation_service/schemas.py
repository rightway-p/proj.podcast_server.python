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


class ScheduleCreate(BaseModel):
    playlist_id: int
    cron_expression: str
    timezone: str = "Asia/Seoul"
    is_active: bool = True


class ScheduleUpdate(BaseModel):
    cron_expression: str | None = None
    timezone: str | None = None
    is_active: bool | None = None
    next_run_at: datetime | None = None


class ScheduleRead(BaseModel):
    id: int
    playlist_id: int
    cron_expression: str
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
