from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def test_channel_crud(client: TestClient) -> None:
    payload = {"slug": "rw-test", "title": "RW Test", "description": "Demo channel"}
    response = client.post("/channels/", json=payload)
    assert response.status_code == 201
    channel_id = response.json()["id"]

    response = client.get("/channels/")
    assert response.status_code == 200
    channels = response.json()
    assert len(channels) == 1
    assert channels[0]["slug"] == "rw-test"

    update_response = client.patch(f"/channels/{channel_id}", json={"title": "New Title"})
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "New Title"

    duplicate_response = client.post("/channels/", json=payload)
    assert duplicate_response.status_code == 409

    delete_response = client.delete(f"/channels/{channel_id}")
    assert delete_response.status_code == 204
    remaining = client.get("/channels/").json()
    assert remaining == []


@pytest.fixture()
def channel_id(client: TestClient) -> int:
    payload = {"slug": "rw-test", "title": "RW Test"}
    response = client.post("/channels/", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture()
def playlist_id(client: TestClient, channel_id: int) -> int:
    payload = {
        "youtube_playlist_id": "PL1234567890",
        "title": "Playlist",
        "channel_id": channel_id,
    }
    response = client.post("/playlists/", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


def test_playlist_crud(client: TestClient, channel_id: int) -> None:
    payload = {
        "youtube_playlist_id": "PLtest123",
        "title": "Playlist",
        "channel_id": channel_id,
        "castopod_slug": "rw-test",
        "castopod_uuid": "uuid-123",
    }
    response = client.post("/playlists/", json=payload)
    assert response.status_code == 201
    playlist = response.json()
    playlist_id = playlist["id"]
    assert playlist["castopod_slug"] == "rw-test"

    list_response = client.get("/playlists/")
    assert list_response.status_code == 200
    assert any(item["id"] == playlist_id for item in list_response.json())

    update_response = client.patch(
        f"/playlists/{playlist_id}",
        json={"title": "Updated", "is_active": False, "castopod_uuid": "uuid-456"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Updated"
    assert updated["is_active"] is False
    assert updated["castopod_uuid"] == "uuid-456"

    duplicate_response = client.post("/playlists/", json=payload)
    assert duplicate_response.status_code == 409

    delete_response = client.delete(f"/playlists/{playlist_id}")
    assert delete_response.status_code == 204


def test_schedule_crud(client: TestClient, playlist_id: int) -> None:
    create_response = client.post(
        "/schedules/",
        json={
            "playlist_id": playlist_id,
            "cron_expression": "0 7 * * *",
            "timezone": "Asia/Seoul",
        },
    )
    assert create_response.status_code == 201
    schedule = create_response.json()
    schedule_id = schedule["id"]

    list_response = client.get("/schedules/")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == schedule_id

    update_payload = {
        "cron_expression": "30 19 * * *",
        "timezone": "Asia/Tokyo",
        "next_run_at": datetime.now(UTC).isoformat(),
    }
    update_response = client.patch(f"/schedules/{schedule_id}", json=update_payload)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["cron_expression"] == "30 19 * * *"
    assert updated["timezone"] == "Asia/Tokyo"

    delete_response = client.delete(f"/schedules/{schedule_id}")
    assert delete_response.status_code == 204


def test_run_crud(client: TestClient, playlist_id: int) -> None:
    create_response = client.post(
        "/runs/",
        json={
            "playlist_id": playlist_id,
            "status": "pending",
            "message": "queued",
        },
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["id"]

    list_response = client.get("/runs/")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == run_id

    update_response = client.patch(
        f"/runs/{run_id}", json={"status": "finished", "message": "done"}
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "finished"
    assert updated["message"] == "done"

    delete_response = client.delete(f"/runs/{run_id}")
    assert delete_response.status_code == 204


def test_job_queue(client: TestClient, playlist_id: int) -> None:
    create_response = client.post(
        "/jobs/",
        json={
            "playlist_id": playlist_id,
            "action": "sync",
            "castopod_slug": "cast-channel",
            "note": "initial import",
            "should_castopod_upload": True,
        },
    )
    assert create_response.status_code == 201
    job = create_response.json()
    job_id = job["id"]
    assert job["should_castopod_upload"] is True
    assert job["progress_total"] == 0
    assert job["progress_completed"] == 0
    assert job["current_task"] is None

    list_response = client.get("/jobs/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/jobs/{job_id}")
    assert get_response.status_code == 200

    update_response = client.patch(
        f"/jobs/{job_id}",
        json={
            "status": "running",
            "should_castopod_upload": False,
            "progress_total": 10,
            "progress_completed": 3,
            "current_task": "download",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "running"
    assert updated["should_castopod_upload"] is False
    assert updated["progress_total"] == 10
    assert updated["progress_completed"] == 3
    assert updated["current_task"] == "download"

    delete_response = client.delete(f"/jobs/{job_id}")
    assert delete_response.status_code == 204


def test_job_quick_create(client: TestClient) -> None:
    payload = {
        "job_name": "RW Playlist",
        "youtube_playlist": "https://www.youtube.com/playlist?list=PLquick123",
        "castopod_slug": "rw-channel",
        "castopod_uuid": "uuid-quick",
        "should_castopod_upload": True,
        "note": "initial",
    }
    response = client.post("/jobs/quick-create", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["created_channel"] is True
    assert body["created_playlist"] is True
    assert body["channel"]["slug"] == "rw-playlist"
    assert body["playlist"]["youtube_playlist_id"] == "PLquick123"
    assert body["job"]["should_castopod_upload"] is True

    # second call reuses channel/playlist but enqueues new job
    repeat = client.post("/jobs/quick-create", json=payload)
    assert repeat.status_code == 201
    repeat_body = repeat.json()
    assert repeat_body["created_channel"] is False
    assert repeat_body["created_playlist"] is False

    channels = client.get("/channels/").json()
    playlists = client.get("/playlists/").json()
    jobs = client.get("/jobs/").json()
    assert len(channels) == 1
    assert len(playlists) == 1
    assert len(jobs) == 2


def test_delete_channel_cascade(client: TestClient) -> None:
    channel = client.post("/channels/", json={"slug": "cascade", "title": "Cascade"}).json()
    playlist = client.post(
        "/playlists/",
        json={
            "youtube_playlist_id": "PLCascade",
            "title": "Cascade Playlist",
            "channel_id": channel["id"],
        },
    ).json()
    client.post(
        "/schedules/",
        json={
            "playlist_id": playlist["id"],
            "cron_expression": "0 7 * * *",
            "timezone": "Asia/Seoul",
        },
    )
    client.post("/runs/", json={"playlist_id": playlist["id"]})
    client.post("/jobs/", json={"playlist_id": playlist["id"]})

    response = client.delete(f"/channels/{channel['id']}")
    assert response.status_code == 204
    assert client.get("/channels/").json() == []
    assert client.get("/playlists/").json() == []
