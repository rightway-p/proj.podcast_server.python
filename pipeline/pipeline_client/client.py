from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Iterable, List, Optional

import httpx
from pydantic import BaseModel


class Channel(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str] = None


class Playlist(BaseModel):
    id: int
    youtube_playlist_id: str
    title: Optional[str] = None
    channel_id: int
    is_active: bool = True
    castopod_slug: Optional[str] = None
    castopod_uuid: Optional[str] = None


class Schedule(BaseModel):
    id: int
    playlist_id: int
    cron_expression: str
    timezone: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None


class PipelinePlaylist(BaseModel):
    playlist: Playlist
    schedules: List[Schedule]


class PipelineChannel(BaseModel):
    channel: Channel
    playlists: List[PipelinePlaylist]


class PipelineConfiguration(BaseModel):
    fetched_at: datetime
    channels: List[PipelineChannel]


class Run(BaseModel):
    id: int
    playlist_id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    message: Optional[str] = None
    progress_total: int = 0
    progress_completed: int = 0
    current_task: Optional[str] = None
    progress_message: Optional[str] = None


class Job(BaseModel):
    id: int
    playlist_id: int
    action: str
    status: str
    castopod_slug: Optional[str] = None
    castopod_playlist_uuid: Optional[str] = None
    note: Optional[str] = None
    should_castopod_upload: bool = False
    progress_total: int = 0
    progress_completed: int = 0
    current_task: Optional[str] = None
    progress_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AutomationServiceClient:
    """HTTP client wrapper around the automation service REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if base_url is None:
            base_url = os.getenv("AUTOMATION_API_BASE_URL", "http://localhost:8000")
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport)

    async def __aenter__(self) -> "AutomationServiceClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_channels(self) -> List[Channel]:
        response = await self._client.get("/channels/")
        response.raise_for_status()
        return [Channel.model_validate(item) for item in response.json()]

    async def fetch_playlists(self) -> List[Playlist]:
        response = await self._client.get("/playlists/")
        response.raise_for_status()
        return [Playlist.model_validate(item) for item in response.json()]

    async def fetch_schedules(self) -> List[Schedule]:
        response = await self._client.get("/schedules/")
        response.raise_for_status()
        return [Schedule.model_validate(item) for item in response.json()]

    async def fetch_configuration(self) -> PipelineConfiguration:
        channels = await self.fetch_channels()
        playlists = await self.fetch_playlists()
        schedules = await self.fetch_schedules()

        schedule_map = _group_schedules_by_playlist(schedules)
        channel_map = {channel.id: channel for channel in channels}

        channel_entries: list[PipelineChannel] = []
        for channel_id, channel in channel_map.items():
            channel_playlists = [
                PipelinePlaylist(
                    playlist=playlist,
                    schedules=schedule_map.get(playlist.id, []),
                )
                for playlist in playlists
                if playlist.channel_id == channel_id and playlist.is_active
            ]
            channel_entries.append(PipelineChannel(channel=channel, playlists=channel_playlists))

        fetched_at = datetime.now(UTC)
        return PipelineConfiguration(fetched_at=fetched_at, channels=channel_entries)

    async def create_channel(self, slug: str, title: str, description: Optional[str] = None) -> Channel:
        payload = {"slug": slug, "title": title, "description": description}
        response = await self._client.post("/channels/", json=payload)
        response.raise_for_status()
        return Channel.model_validate(response.json())

    async def update_channel(self, channel_id: int, *, title: Optional[str] = None,
                             description: Optional[str] = None) -> Channel:
        payload: dict[str, str | None] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        response = await self._client.patch(f"/channels/{channel_id}", json=payload)
        response.raise_for_status()
        return Channel.model_validate(response.json())

    async def delete_channel(self, channel_id: int) -> None:
        response = await self._client.delete(f"/channels/{channel_id}")
        response.raise_for_status()

    async def create_playlist(
        self,
        channel_id: int,
        youtube_playlist_id: str,
        *,
        title: Optional[str] = None,
        is_active: bool = True,
    ) -> Playlist:
        payload = {
            "channel_id": channel_id,
            "youtube_playlist_id": youtube_playlist_id,
            "title": title,
            "is_active": is_active,
        }
        response = await self._client.post("/playlists/", json=payload)
        response.raise_for_status()
        return Playlist.model_validate(response.json())

    async def update_playlist(
        self,
        playlist_id: int,
        *,
        title: Optional[str] = None,
        channel_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Playlist:
        payload: dict[str, object] = {}
        if title is not None:
            payload["title"] = title
        if channel_id is not None:
            payload["channel_id"] = channel_id
        if is_active is not None:
            payload["is_active"] = is_active
        response = await self._client.patch(f"/playlists/{playlist_id}", json=payload)
        response.raise_for_status()
        return Playlist.model_validate(response.json())

    async def delete_playlist(self, playlist_id: int) -> None:
        response = await self._client.delete(f"/playlists/{playlist_id}")
        response.raise_for_status()

    async def create_schedule(
        self,
        playlist_id: int,
        cron_expression: str,
        *,
        timezone: str = "Asia/Seoul",
        is_active: bool = True,
        next_run_at: Optional[str] = None,
    ) -> Schedule:
        payload = {
            "playlist_id": playlist_id,
            "cron_expression": cron_expression,
            "timezone": timezone,
            "is_active": is_active,
        }
        if next_run_at is not None:
            payload["next_run_at"] = next_run_at
        response = await self._client.post("/schedules/", json=payload)
        response.raise_for_status()
        return Schedule.model_validate(response.json())

    async def update_schedule(
        self,
        schedule_id: int,
        *,
        cron_expression: Optional[str] = None,
        timezone: Optional[str] = None,
        is_active: Optional[bool] = None,
        next_run_at: Optional[str] = None,
    ) -> Schedule:
        payload: dict[str, object] = {}
        if cron_expression is not None:
            payload["cron_expression"] = cron_expression
        if timezone is not None:
            payload["timezone"] = timezone
        if is_active is not None:
            payload["is_active"] = is_active
        if next_run_at is not None:
            payload["next_run_at"] = next_run_at
        response = await self._client.patch(f"/schedules/{schedule_id}", json=payload)
        response.raise_for_status()
        return Schedule.model_validate(response.json())

    async def delete_schedule(self, schedule_id: int) -> None:
        response = await self._client.delete(f"/schedules/{schedule_id}")
        response.raise_for_status()

    async def create_run(
        self,
        playlist_id: int,
        *,
        status: str = "pending",
        message: Optional[str] = None,
    ) -> Run:
        payload = {
            "playlist_id": playlist_id,
            "status": status,
            "message": message,
        }
        response = await self._client.post("/runs/", json=payload)
        response.raise_for_status()
        return Run.model_validate(response.json())

    async def update_run(
        self,
        run_id: int,
        *,
        status: Optional[str] = None,
        message: Optional[str] = None,
        finished_at: Optional[datetime] = None,
        progress_total: Optional[int] = None,
        progress_completed: Optional[int] = None,
        current_task: Optional[str] = None,
        progress_message: Optional[str] = None,
    ) -> Run:
        payload: dict[str, object] = {}
        if status is not None:
            payload["status"] = status
        if message is not None:
            payload["message"] = message
        if finished_at is not None:
            payload["finished_at"] = finished_at.isoformat()
        if progress_total is not None:
            payload["progress_total"] = progress_total
        if progress_completed is not None:
            payload["progress_completed"] = progress_completed
        if current_task is not None:
            payload["current_task"] = current_task
        if progress_message is not None:
            payload["progress_message"] = progress_message
        response = await self._client.patch(f"/runs/{run_id}", json=payload)
        response.raise_for_status()
        return Run.model_validate(response.json())

    async def fetch_jobs(self) -> List[Job]:
        response = await self._client.get("/jobs/")
        response.raise_for_status()
        return [Job.model_validate(item) for item in response.json()]

    async def fetch_job(self, job_id: int) -> Job:
        response = await self._client.get(f"/jobs/{job_id}")
        response.raise_for_status()
        return Job.model_validate(response.json())

    async def update_job(
        self,
        job_id: int,
        *,
        status: Optional[str] = None,
        note: Optional[str] = None,
        progress_total: Optional[int] = None,
        progress_completed: Optional[int] = None,
        current_task: Optional[str] = None,
        progress_message: Optional[str] = None,
        should_castopod_upload: Optional[bool] = None,
    ) -> Job:
        payload: dict[str, object] = {}
        if status is not None:
            payload["status"] = status
        if note is not None:
            payload["note"] = note
        if progress_total is not None:
            payload["progress_total"] = progress_total
        if progress_completed is not None:
            payload["progress_completed"] = progress_completed
        if current_task is not None:
            payload["current_task"] = current_task
        if progress_message is not None:
            payload["progress_message"] = progress_message
        if should_castopod_upload is not None:
            payload["should_castopod_upload"] = should_castopod_upload
        response = await self._client.patch(f"/jobs/{job_id}", json=payload)
        response.raise_for_status()
        return Job.model_validate(response.json())


def _group_schedules_by_playlist(schedules: Iterable[Schedule]) -> dict[int, List[Schedule]]:
    grouped: dict[int, List[Schedule]] = {}
    for schedule in schedules:
        grouped.setdefault(schedule.playlist_id, []).append(schedule)
    return grouped
