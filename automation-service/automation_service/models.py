from datetime import UTC, datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin(SQLModel, table=False):
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)


class ChannelBase(SQLModel):
    slug: str = Field(
        min_length=1,
        max_length=100,
        index=True,
        sa_column_kwargs={"unique": True},
    )
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)


class Channel(ChannelBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlists: List["Playlist"] = Relationship(
        back_populates="channel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class PlaylistBase(SQLModel):
    youtube_playlist_id: str = Field(
        min_length=3,
        max_length=64,
        index=True,
        sa_column_kwargs={"unique": True},
    )
    title: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    castopod_slug: Optional[str] = Field(default=None, max_length=255)
    castopod_uuid: Optional[str] = Field(default=None, max_length=64)


class Playlist(PlaylistBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channel.id")

    channel: Optional[Channel] = Relationship(back_populates="playlists")
    schedules: List["Schedule"] = Relationship(
        back_populates="playlist",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    runs: List["Run"] = Relationship(
        back_populates="playlist",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    jobs: List["Job"] = Relationship(
        back_populates="playlist",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class ScheduleBase(SQLModel):
    cron_expression: str = Field(min_length=5, max_length=120)
    timezone: str = Field(default="Asia/Seoul", max_length=64)
    is_active: bool = Field(default=True)
    last_run_at: Optional[datetime] = Field(default=None)
    next_run_at: Optional[datetime] = Field(default=None)


class Schedule(ScheduleBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlist.id")

    playlist: Optional[Playlist] = Relationship(back_populates="schedules")


class RunBase(SQLModel):
    status: str = Field(default="pending", max_length=32)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: Optional[datetime] = Field(default=None)
    message: Optional[str] = Field(default=None, max_length=4000)
    progress_total: int = Field(default=0)
    progress_completed: int = Field(default=0)
    current_task: Optional[str] = Field(default=None, max_length=255)
    progress_message: Optional[str] = Field(default=None, max_length=2000)


class Run(RunBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlist.id")

    playlist: Optional[Playlist] = Relationship(back_populates="runs")


class JobBase(SQLModel):
    action: str = Field(default="sync", max_length=32)
    status: str = Field(default="queued", max_length=32)
    castopod_slug: Optional[str] = Field(default=None, max_length=255)
    castopod_playlist_uuid: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = Field(default=None, max_length=2000)
    should_castopod_upload: bool = Field(default=False)
    progress_total: int = Field(default=0)
    progress_completed: int = Field(default=0)
    current_task: Optional[str] = Field(default=None, max_length=255)
    progress_message: Optional[str] = Field(default=None, max_length=2000)


class Job(JobBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlist.id")

    playlist: Optional[Playlist] = Relationship(back_populates="jobs")
