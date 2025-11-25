from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from automation_service import database
from automation_service.main import app

from pipeline_client.client import AutomationServiceClient


@pytest.fixture()
async def http_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    original_engine = database._engine
    original_init_db = database.init_db

    database._engine = engine

    def override_init_db() -> None:
        SQLModel.metadata.create_all(engine)

    database.init_db = override_init_db
    override_init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client

    SQLModel.metadata.drop_all(engine)
    database._engine = original_engine
    database.init_db = original_init_db


@pytest.mark.asyncio
async def test_fetch_configuration_returns_nested_structure(http_client: AsyncClient) -> None:
    channel_payload = {"slug": "rw", "title": "RW", "description": "channel"}
    resp = await http_client.post("/channels/", json=channel_payload)
    assert resp.status_code == 201
    channel_id = resp.json()["id"]

    playlist_payload = {
        "youtube_playlist_id": "PL123",
        "title": "Playlist",
        "channel_id": channel_id,
    }
    playlist_resp = await http_client.post("/playlists/", json=playlist_payload)
    assert playlist_resp.status_code == 201
    playlist_id = playlist_resp.json()["id"]

    inactive_playlist_payload = {
        "youtube_playlist_id": "PL999",
        "title": "Inactive",
        "channel_id": channel_id,
        "is_active": False,
    }
    inactive_resp = await http_client.post("/playlists/", json=inactive_playlist_payload)
    assert inactive_resp.status_code == 201

    schedule_payload = {
        "playlist_id": playlist_id,
        "days_of_week": ["mon", "wed"],
        "run_time": "07:00",
        "timezone": "Asia/Seoul",
        "next_run_at": datetime.now(UTC).isoformat(),
    }
    schedule_resp = await http_client.post("/schedules/", json=schedule_payload)
    assert schedule_resp.status_code == 201

    async with AutomationServiceClient(
        base_url="http://testserver",
        transport=ASGITransport(app=app),
    ) as client:
        config = await client.fetch_configuration()

    assert len(config.channels) == 1
    channel_entry = config.channels[0]
    assert channel_entry.channel.slug == "rw"
    assert len(channel_entry.playlists) == 1  # inactive playlist excluded
    playlist_entry = channel_entry.playlists[0]
    assert playlist_entry.playlist.youtube_playlist_id == "PL123"
    assert len(playlist_entry.schedules) == 1
    assert playlist_entry.schedules[0].days_of_week == ["mon", "wed"]


@pytest.mark.asyncio
async def test_fetch_configuration_includes_empty_channels(http_client: AsyncClient) -> None:
    channel_payload = {"slug": "empty", "title": "Empty"}
    resp = await http_client.post("/channels/", json=channel_payload)
    assert resp.status_code == 201

    async with AutomationServiceClient(
        base_url="http://testserver",
        transport=ASGITransport(app=app),
    ) as client:
        config = await client.fetch_configuration()

    assert len(config.channels) == 1
    channel_entry = config.channels[0]
    assert channel_entry.channel.slug == "empty"
    assert channel_entry.playlists == []


@pytest.mark.asyncio
async def test_crud_helpers_modify_resources(http_client: AsyncClient) -> None:
    async with AutomationServiceClient(
        base_url="http://testserver",
        transport=ASGITransport(app=app),
    ) as client:
        channel = await client.create_channel("crud", "CRUD Channel", "desc")
        assert channel.slug == "crud"

        updated_channel = await client.update_channel(channel.id, title="Updated")
        assert updated_channel.title == "Updated"

        playlist = await client.create_playlist(
            channel_id=channel.id,
            youtube_playlist_id="PLCRUD",
            title="CRUD Playlist",
        )
        assert playlist.channel_id == channel.id

        await client.update_playlist(playlist.id, is_active=False)

        schedule = await client.create_schedule(
            playlist_id=playlist.id,
            days_of_week=["mon"],
            run_time="12:00",
            timezone="Asia/Tokyo",
        )
        assert schedule.timezone == "Asia/Tokyo"

        await client.update_schedule(schedule.id, days_of_week=["fri"], run_time="06:00")

        # delete operations should not raise
        await client.delete_schedule(schedule.id)
        await client.delete_playlist(playlist.id)
        await client.delete_channel(channel.id)


@pytest.mark.asyncio
async def test_run_crud_via_client(http_client: AsyncClient) -> None:
    channel_payload = {"slug": "run-test", "title": "Run Test"}
    resp = await http_client.post("/channels/", json=channel_payload)
    channel_id = resp.json()["id"]
    playlist_payload = {
        "youtube_playlist_id": "PLRUN",
        "title": "Run Playlist",
        "channel_id": channel_id,
    }
    playlist_resp = await http_client.post("/playlists/", json=playlist_payload)
    playlist_id = playlist_resp.json()["id"]

    async with AutomationServiceClient(
        base_url="http://testserver",
        transport=ASGITransport(app=app),
    ) as client:
        run = await client.create_run(playlist_id=playlist_id, message="start")
        assert run.status == "pending"
        assert run.message == "start"

        updated = await client.update_run(
            run.id,
            status="finished",
            message="done",
        )
        assert updated.status == "finished"
        assert updated.message == "done"
