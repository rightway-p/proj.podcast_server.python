from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from pipeline_client.client import Channel, PipelineChannel, PipelinePlaylist, Playlist
from pipeline_runner.artwork import create_square_artwork, gather_thumbnail_urls
from pipeline_runner.main import DownloadResult, EpisodeRecord, write_playlist_metadata


def _create_rect_image(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", size, color)
    try:
        image.save(path, format="JPEG")
    finally:
        image.close()


def test_create_square_artwork_local_source(tmp_path: Path) -> None:
    src = tmp_path / "src.jpg"
    _create_rect_image(src, (300, 120), (255, 0, 0))

    dest = tmp_path / "square.jpg"
    result = create_square_artwork(dest, local_source=src)

    assert result == dest
    assert dest.exists()

    with Image.open(dest) as image:
        assert image.size == (300, 300)
        assert image.getpixel((150, 10)) == (0, 0, 0)  # top padding
        center_pixel = image.getpixel((150, 150))
        assert center_pixel[0] >= 250 and center_pixel[1:] == (0, 0)  # original content within JPEG tolerance
        assert image.getpixel((150, 290)) == (0, 0, 0)  # bottom padding


def test_gather_thumbnail_urls_orders_by_resolution() -> None:
    thumbnails: list[dict[str, Any]] = [
        {"url": "small", "width": 120, "height": 90},
        {"url": "medium", "width": 640, "height": 480},
        {"url": "large", "width": 1920, "height": 1080},
    ]

    ordered = gather_thumbnail_urls("fallback", thumbnails)

    assert ordered[:3] == ["large", "medium", "small"]
    assert ordered[-1] == "fallback"


def test_write_playlist_metadata_with_artwork(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    playlist_dir = tmp_path / "playlist"
    audio_dir = playlist_dir
    audio_dir.mkdir(parents=True)

    episode_audio = audio_dir / "episode.mp3"
    episode_audio.write_bytes(b"fake-audio")

    episode_thumbnail = playlist_dir / "episode_src.jpg"
    _create_rect_image(episode_thumbnail, (400, 200), (0, 255, 0))

    def fake_httpx_get(url: str, *args: Any, **kwargs: Any):
        class _Resp:
            def __init__(self, content: bytes) -> None:
                self.content = content

            def raise_for_status(self) -> None:  # pragma: no cover - no error expected
                return None

        return _Resp(episode_thumbnail.read_bytes())

    monkeypatch.setattr("pipeline_runner.artwork.httpx.get", fake_httpx_get)

    episode = EpisodeRecord(
        video_id="video123",
        title="Episode",
        description="",
        webpage_url="https://example.com",
        upload_date="20240101",
        duration=120,
        audio_path=episode_audio,
        info_path=None,
        thumbnail_path=episode_thumbnail,
        thumbnail_url=None,
        thumbnails=None,
    )

    download_result = DownloadResult(
        playlist_url="https://youtube.com/playlist?list=123",
        downloaded=1,
        dry_run=False,
        episodes=[episode],
        playlist_info={
            "thumbnail": None,
            "thumbnails": [
                {"url": "https://example.com/cover", "width": 1280, "height": 720},
            ],
        },
    )

    channel_entry = PipelineChannel(
        channel=Channel(id=1, slug="test", title="Test Channel", description="Desc"),
        playlists=[
            PipelinePlaylist(
                playlist=Playlist(
                    id=1,
                    youtube_playlist_id="PL123",
                    title="Playlist",
                    channel_id=1,
                ),
                schedules=[],
            )
        ],
    )
    playlist_entry = channel_entry.playlists[0]

    write_playlist_metadata(playlist_dir, channel_entry, playlist_entry, download_result)

    metadata_path = playlist_dir / "metadata" / "playlist.json"
    assert metadata_path.exists()

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))

    playlist_cover = payload["playlist"]["square_cover"]
    assert playlist_cover is not None
    assert (playlist_dir / playlist_cover).exists()

    episode_meta = payload["episodes"][0]
    assert episode_meta["thumbnail_square"] is not None
    assert (playlist_dir / episode_meta["thumbnail_square"]).exists()
