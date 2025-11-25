from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from datetime import datetime
import httpx

from pipeline_client.client import Playlist

@dataclass
class CastopodConfig:
    base_url: str
    username: str
    password: str
    user_id: int
    verify_ssl: bool = False
    publication_method: str = "now"
    client_timezone: str = "UTC"
    episode_type: str = "full"


def load_castopod_config_from_env() -> CastopodConfig | None:
    base_url = os.getenv("CASTOPOD_API_BASE_URL")
    username = os.getenv("CASTOPOD_API_USERNAME")
    password = os.getenv("CASTOPOD_API_PASSWORD")
    user_id = os.getenv("CASTOPOD_API_USER_ID")
    if not all([base_url, username, password, user_id]):
        return None
    verify_raw = os.getenv("CASTOPOD_API_VERIFY_SSL", "false").lower()
    verify_ssl = verify_raw in {"1", "true", "yes"}
    publication_method = os.getenv("CASTOPOD_API_PUBLICATION_METHOD", "now")
    client_timezone = os.getenv("CASTOPOD_API_TIMEZONE", "UTC")
    episode_type = os.getenv("CASTOPOD_API_EPISODE_TYPE", "full")
    return CastopodConfig(
        base_url=base_url.rstrip("/"),
        username=username,
        password=password,
        user_id=int(user_id),
        verify_ssl=verify_ssl,
        publication_method=publication_method,
        client_timezone=client_timezone,
        episode_type=episode_type,
    )


class CastopodClient:
    def __init__(self, config: CastopodConfig) -> None:
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            auth=(config.username, config.password),
            verify=config.verify_ssl,
            timeout=30.0,
        )
        self._podcast_cache: dict[str, dict[str, object]] = {}
        self._episode_cache: dict[int, set[str]] = {}

    def close(self) -> None:
        self._client.close()

    def _fetch_podcasts(self) -> None:
        if self._podcast_cache:
            return
        response = self._client.get("podcasts", params={"limit": 200})
        response.raise_for_status()
        for podcast in response.json():
            guid = podcast.get("guid")
            slug = podcast.get("handle")
            if guid:
                self._podcast_cache[guid] = podcast
            if slug:
                self._podcast_cache.setdefault(slug, podcast)

    def resolve_podcast_id(self, playlist: Playlist) -> int | None:
        self._fetch_podcasts()
        if playlist.castopod_uuid and playlist.castopod_uuid in self._podcast_cache:
            return int(self._podcast_cache[playlist.castopod_uuid]["id"])
        if playlist.castopod_slug and playlist.castopod_slug in self._podcast_cache:
            return int(self._podcast_cache[playlist.castopod_slug]["id"])
        return None

    def _fetch_episode_slugs(self, podcast_id: int) -> set[str]:
        if podcast_id in self._episode_cache:
            return self._episode_cache[podcast_id]
        slugs: set[str] = set()
        offset = 0
        while True:
            response = self._client.get(
                "episodes",
                params={"podcastIds": podcast_id, "limit": 100, "offset": offset},
            )
            response.raise_for_status()
            payload = response.json()
            if not payload:
                break
            for entry in payload:
                slug = entry.get("slug")
                if slug:
                    slugs.add(slug)
            if len(payload) < 100:
                break
            offset += 100
        self._episode_cache[podcast_id] = slugs
        return slugs

    def get_episode_slugs(self, podcast_id: int) -> set[str]:
        """Return a copy of the known episode slugs for the given podcast."""
        return set(self._fetch_episode_slugs(podcast_id))

    def upload_episode(
        self,
        podcast_id: int,
        slug: str,
        title: str,
        description: str | None,
        audio_path: Path,
        cover_path: Path | None,
        publication_datetime: datetime | None = None,
    ) -> dict[str, object] | None:
        existing = self._fetch_episode_slugs(podcast_id)
        if slug in existing:
            return None

        data = {
            "title": title,
            "slug": slug,
            "podcast_id": str(podcast_id),
            "description": description or "",
            "created_by": str(self._config.user_id),
            "updated_by": str(self._config.user_id),
            "type": self._config.episode_type,
        }
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        files.append(("audio_file", (audio_path.name, audio_path.read_bytes(), "audio/mpeg")))
        if cover_path and cover_path.exists():
            files.append(("cover", (cover_path.name, cover_path.read_bytes(), "image/jpeg")))

        response = self._client.post("episodes", data=data, files=files)
        response.raise_for_status()
        episode = response.json()
        self._episode_cache.setdefault(podcast_id, set()).add(slug)
        publish_method = self._config.publication_method
        publish_data = {
            "publication_method": publish_method,
            "created_by": str(self._config.user_id),
            "client_timezone": self._config.client_timezone,
        }
        if publish_method == "scheduled":
            if publication_datetime is not None:
                publish_data["publication_datetime"] = publication_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            else:
                publish_data["publication_method"] = "now"
        self._client.post(
            f"episodes/{episode['id']}/publish",
            data=publish_data,
        ).raise_for_status()
        return episode


def slugify(value: str) -> str:
    allowed = []
    for char in value.lower():
        if char.isalnum() and char.isascii():
            allowed.append(char)
        elif char in {" ", "_"}:
            allowed.append("-")
        elif char == "-":
            allowed.append("-")
    slug = "".join(allowed).strip("-")
    return slug or "episode"
