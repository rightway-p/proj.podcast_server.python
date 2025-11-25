from __future__ import annotations

import argparse
import asyncio
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, time
from pathlib import Path
from threading import Event
from typing import Any, Iterable

from rich.console import Console
from rich.table import Table
import json

try:
    from yt_dlp import YoutubeDL
except ImportError:  # pragma: no cover - handled in runtime
    YoutubeDL = None  # type: ignore

from pipeline_client.client import (
    AutomationServiceClient,
    Job,
    PipelineChannel,
    PipelineConfiguration,
    PipelinePlaylist,
)

from .castopod import CastopodClient, load_castopod_config_from_env, slugify

from .artwork import create_square_artwork, gather_thumbnail_urls

console = Console()


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass
class EpisodeRecord:
    video_id: str
    title: str
    description: str | None
    webpage_url: str | None
    upload_date: str | None
    duration: int | None
    audio_path: Path
    info_path: Path | None
    thumbnail_path: Path | None
    thumbnail_url: str | None
    thumbnails: list[dict[str, Any]] | None
    square_cover_path: Path | None = None


def _episode_sort_key(episode: EpisodeRecord) -> tuple[datetime, str]:
    upload_date = episode.upload_date or ""
    if len(upload_date) == 8 and upload_date.isdigit():
        try:
            parsed = datetime.strptime(upload_date, "%Y%m%d")
        except ValueError:
            parsed = datetime.max
    else:
        parsed = datetime.max
    return parsed, episode.title or episode.audio_path.stem


def _episode_publication_datetime(episode: EpisodeRecord) -> datetime | None:
    if not episode.upload_date:
        return None
    if len(episode.upload_date) != 8 or not episode.upload_date.isdigit():
        return None
    try:
        base_date = datetime.strptime(episode.upload_date, "%Y%m%d")
    except ValueError:
        return None
    return datetime.combine(base_date.date(), time(hour=6))


@dataclass
class DownloadResult:
    playlist_url: str
    downloaded: int
    dry_run: bool
    episodes: list[EpisodeRecord]
    playlist_info: dict[str, Any] | None


class JobCancelledError(Exception):
    """Raised when a queue job is cancelled by the user."""


@dataclass
class JobTracker:
    client: AutomationServiceClient
    job: Job
    _cancel_event: Event = field(default_factory=Event, init=False)
    _watch_task: asyncio.Task | None = field(default=None, init=False)

    async def patch(self, **fields: Any) -> Job:
        self.job = await self.client.update_job(self.job.id, **fields)
        return self.job

    async def refresh(self) -> Job:
        self.job = await self.client.fetch_job(self.job.id)
        return self.job

    async def ensure_active(self) -> None:
        if self._cancel_event.is_set():
            raise JobCancelledError
        current = await self.refresh()
        if current.status == "cancelling":
            self._cancel_event.set()
            raise JobCancelledError

    async def start_watch(self) -> None:
        if self._watch_task is not None:
            return
        loop = asyncio.get_running_loop()
        self._watch_task = loop.create_task(self._poll_cancellation())

    async def stop_watch(self) -> None:
        if self._watch_task is None:
            return
        self._watch_task.cancel()
        try:
            await self._watch_task
        except asyncio.CancelledError:
            pass
        self._watch_task = None

    async def _poll_cancellation(self) -> None:
        try:
            while not self._cancel_event.is_set():
                current = await self.refresh()
                if current.status == "cancelling":
                    self._cancel_event.set()
                    break
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(1.0)

    @property
    def cancel_event(self) -> Event:
        return self._cancel_event


@dataclass
class RunTracker:
    client: AutomationServiceClient
    run_id: int

    async def patch(self, **fields: Any) -> None:
        await self.client.update_run(self.run_id, **fields)


def build_playlist_url(value: str) -> str:
    value = value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://www.youtube.com/playlist?list={value}"


async def download_playlist(
    pipeline_playlist: PipelinePlaylist,
    download_dir: Path,
    audio_format: str,
    dry_run: bool,
    existing_slugs: set[str] | None = None,
    job_tracker: JobTracker | None = None,
) -> DownloadResult:
    if YoutubeDL is None:  # pragma: no cover - fallback for missing dependency
        raise RuntimeError("yt-dlp is not installed in this environment")

    def _check_cancel() -> None:
        if job_tracker and job_tracker.cancel_event.is_set():
            raise JobCancelledError

    playlist_url = build_playlist_url(pipeline_playlist.playlist.youtube_playlist_id)

    download_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "outtmpl": str(download_dir / "%(upload_date)s_%(title)s.%(ext)s"),
        "ignoreerrors": True,
        "format": "bestaudio/best",
        "noplaylist": False,
        "quiet": False,
        "no_warnings": True,
        "writeinfojson": True,
        "writethumbnail": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "0",
            }
        ],
    }
    def _run() -> tuple[int, list[EpisodeRecord], dict[str, Any] | None, int]:
        metadata_opts = dict(ydl_opts)
        metadata_opts["skip_download"] = True
        metadata_opts.pop("postprocessors", None)
        playlist_info: dict[str, Any] | None = None
        filtered_entries: list[dict[str, Any]] = []
        skipped_existing = 0
        with YoutubeDL(metadata_opts) as meta_ydl:
            _check_cancel()
            info = meta_ydl.extract_info(playlist_url, download=False)
            playlist_info = info if isinstance(info, dict) else None
            entries = playlist_info.get("entries") if playlist_info else []
            if entries:
                for entry in entries:
                    _check_cancel()
                    if not entry:
                        continue
                    slug_source = entry.get("id") or entry.get("title") or ""
                    slug = slugify(slug_source)
                    if existing_slugs and slug in existing_slugs:
                        skipped_existing += 1
                        continue
                    filtered_entries.append(entry)

        episodes: list[EpisodeRecord] = []
        if not filtered_entries:
            return 0, episodes, playlist_info, skipped_existing

        download_opts = dict(ydl_opts)
        download_opts.pop("skip_download", None)
        with YoutubeDL(download_opts) as ydl:
            for entry in filtered_entries:
                _check_cancel()
                entry_url = (
                    entry.get("original_url")
                    or entry.get("webpage_url")
                    or entry.get("url")
                )
                info = entry
                if entry_url and not dry_run:
                    info = ydl.extract_info(entry_url, download=True)
                base_filename = Path(ydl.prepare_filename(info))
                audio_path = base_filename.with_suffix(f".{audio_format}")
                info_path = base_filename.with_suffix(".info.json")
                thumbnail_path = None
                for ext in (".jpg", ".webp", ".png"):
                    candidate = base_filename.with_suffix(ext)
                    if candidate.exists():
                        thumbnail_path = candidate
                        break
                thumbnails = info.get("thumbnails")
                episodes.append(
                    EpisodeRecord(
                        video_id=info.get("id", ""),
                        title=info.get("title", ""),
                        description=info.get("description"),
                        webpage_url=info.get("webpage_url"),
                        upload_date=info.get("upload_date"),
                        duration=info.get("duration"),
                        audio_path=audio_path,
                        info_path=info_path if info_path.exists() else None,
                        thumbnail_path=thumbnail_path,
                        thumbnail_url=info.get("thumbnail"),
                        thumbnails=list(thumbnails) if thumbnails else None,
                    )
                )
        episodes.sort(key=_episode_sort_key)
        return len(episodes), episodes, playlist_info, skipped_existing

    downloaded, episodes, playlist_info, skipped_existing = await asyncio.to_thread(_run)
    if skipped_existing:
        console.print(
            f"[yellow]{skipped_existing}개 에피소드는 Castopod에 이미 존재하여 건너뜀[/yellow]"
        )
    return DownloadResult(playlist_url, downloaded, dry_run, episodes, playlist_info)


def write_playlist_metadata(
    playlist_dir: Path,
    channel_entry: PipelineChannel,
    playlist_entry: PipelinePlaylist,
    result: DownloadResult,
) -> None:
    metadata_dir = playlist_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    artwork_dir = metadata_dir / "artwork"
    episodes_artwork_dir = artwork_dir / "episodes"

    playlist_cover_rel: str | None = None
    channel_cover_rel: str | None = None

    playlist_info = result.playlist_info or {}
    playlist_thumbnail_urls = gather_thumbnail_urls(
        playlist_info.get("thumbnail"),
        playlist_info.get("thumbnails"),
    )

    playlist_cover_path = create_square_artwork(
        artwork_dir / "playlist_cover.jpg",
        remote_candidates=playlist_thumbnail_urls,
    )
    if playlist_cover_path is not None:
        playlist_cover_rel = os.path.relpath(playlist_cover_path, playlist_dir)
        channel_cover_rel = playlist_cover_rel
    elif playlist_thumbnail_urls:
        console.log(
            f"[yellow]경고:[/yellow] 플레이리스트 표지 이미지를 생성하지 못했습니다 — {playlist_dir}"
        )

    episode_lookup = {
        (episode.video_id or episode.audio_path.stem): episode for episode in result.episodes
    }

    playlist_meta = []
    for episode in result.episodes:
        episode_thumbnail_urls = gather_thumbnail_urls(
            episode.thumbnail_url,
            episode.thumbnails,
        )
        episode_artwork_path = create_square_artwork(
            episodes_artwork_dir / f"{episode.video_id or episode.audio_path.stem}.jpg",
            local_source=episode.thumbnail_path,
            remote_candidates=episode_thumbnail_urls,
        )
        episode_artwork_rel = (
            os.path.relpath(episode_artwork_path, playlist_dir)
            if episode_artwork_path is not None
            else None
        )
        if episode_artwork_path is not None:
            key = episode.video_id or episode.audio_path.stem
            record = episode_lookup.get(key)
            if record is not None:
                record.square_cover_path = episode_artwork_path
        if episode_artwork_rel is None and (episode.thumbnail_path or episode_thumbnail_urls):
            console.log(
                f"[yellow]경고:[/yellow] 에피소드 썸네일 생성 실패 — {episode.video_id or episode.audio_path.stem}"
            )
        playlist_meta.append(
            {
                "video_id": episode.video_id,
                "title": episode.title,
                "description": episode.description,
                "webpage_url": episode.webpage_url,
                "upload_date": episode.upload_date,
                "duration": episode.duration,
                "audio_file": os.path.relpath(episode.audio_path, playlist_dir)
                if episode.audio_path.exists()
                else str(episode.audio_path),
                "info_json": os.path.relpath(episode.info_path, playlist_dir)
                if episode.info_path and episode.info_path.exists()
                else None,
                "thumbnail": os.path.relpath(episode.thumbnail_path, playlist_dir)
                if episode.thumbnail_path and episode.thumbnail_path.exists()
                else None,
                "thumbnail_square": episode_artwork_rel,
                "thumbnail_source": episode.thumbnail_url,
            }
        )

    payload = {
        "channel": {
            "id": channel_entry.channel.id,
            "slug": channel_entry.channel.slug,
            "title": channel_entry.channel.title,
            "description": channel_entry.channel.description,
            "square_cover": channel_cover_rel,
        },
        "playlist": {
            "id": playlist_entry.playlist.id,
            "youtube_playlist_id": playlist_entry.playlist.youtube_playlist_id,
            "title": playlist_entry.playlist.title,
            "square_cover": playlist_cover_rel,
        },
        "episodes": playlist_meta,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    output_json = metadata_dir / "playlist.json"
    with output_json.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


async def process_playlist_entry(
    client: AutomationServiceClient,
    channel_entry: PipelineChannel,
    playlist_entry: PipelinePlaylist,
    download_root: Path,
    audio_format: str,
    dry_run: bool,
    castopod_client: CastopodClient | None,
    allow_castopod_upload: bool,
    job_tracker: JobTracker | None = None,
    propagate_errors: bool = False,
) -> DownloadResult | None:
    playlist = playlist_entry.playlist
    playlist_dir = download_root / channel_entry.channel.slug / (
        playlist.title or playlist.youtube_playlist_id
    )

    podcast_id: int | None = None
    existing_slugs: set[str] | None = None
    if castopod_client and (playlist.castopod_slug or playlist.castopod_uuid):
        podcast_id = castopod_client.resolve_podcast_id(playlist)
        if podcast_id is not None:
            existing_slugs = castopod_client.get_episode_slugs(podcast_id)

    run_record = await client.create_run(
        playlist_id=playlist.id,
        status="in_progress",
        message=f"Starting download into {playlist_dir}",
    )
    run_tracker = RunTracker(client, run_record.id)
    try:
        if job_tracker:
            await job_tracker.ensure_active()
            await job_tracker.patch(
                current_task="downloading",
                progress_message="YouTube 다운로드 준비",
                progress_total=0,
                progress_completed=0,
            )
        await run_tracker.patch(
            current_task="downloading",
            progress_message="YouTube 다운로드 준비",
            progress_total=0,
            progress_completed=0,
        )
        result = await download_playlist(
            playlist_entry,
            playlist_dir,
            audio_format,
            dry_run,
            existing_slugs=existing_slugs,
            job_tracker=job_tracker,
        )
        write_playlist_metadata(
            playlist_dir,
            channel_entry,
            playlist_entry,
            result,
        )
        message = (
            f"{'Simulated' if dry_run else 'Downloaded'} {result.downloaded} entries"
        )
        console.print(f"[green]✓[/green] {playlist_dir} — {message}")
        if job_tracker:
            await job_tracker.patch(
                progress_total=result.downloaded,
                progress_completed=0,
                current_task="metadata",
                progress_message="메타데이터 생성 중",
            )
        await run_tracker.patch(
            progress_total=result.downloaded,
            progress_completed=0,
            current_task="metadata",
            progress_message="메타데이터 생성 중",
        )
        if (
            not dry_run
            and allow_castopod_upload
            and castopod_client is not None
            and playlist.castopod_slug
            and playlist.castopod_uuid
        ):
            await upload_playlist_to_castopod(
                castopod_client,
                playlist_entry,
                result,
                podcast_id=podcast_id,
                job_tracker=job_tracker,
                run_tracker=run_tracker,
            )
            if job_tracker:
                await job_tracker.patch(
                    progress_message="Castopod 업로드 완료",
                    current_task=None,
                )
            await run_tracker.patch(
                progress_total=result.downloaded,
                progress_completed=result.downloaded,
                progress_message="Castopod 업로드 완료",
                current_task=None,
            )
        else:
            if job_tracker:
                await job_tracker.patch(
                    progress_completed=result.downloaded,
                    progress_message="다운로드 완료",
                    current_task=None,
                )
            await run_tracker.patch(
                progress_total=result.downloaded,
                progress_completed=result.downloaded,
                progress_message="다운로드 완료",
                current_task=None,
            )
        await client.update_run(
            run_record.id,
            status="finished",
            message=message,
            finished_at=datetime.now(UTC),
        )
        return result
    except JobCancelledError:
        await client.update_run(
            run_record.id,
            status="cancelled",
            message="Job cancelled by user",
            finished_at=datetime.now(UTC),
        )
        if job_tracker:
            await job_tracker.patch(
                progress_message="사용자 취소",
                current_task=None,
            )
        await run_tracker.patch(
            progress_message="사용자 취소",
            current_task=None,
        )
        if propagate_errors:
            raise
        return None
    except Exception as exc:  # pragma: no cover - runtime logging
        await client.update_run(
            run_record.id,
            status="failed",
            message=str(exc),
            finished_at=datetime.now(UTC),
        )
        console.print(f"[red]✗ {playlist.youtube_playlist_id} 실패:[/red] {exc}")
        if job_tracker:
            await job_tracker.patch(
                progress_message=str(exc),
                current_task=None,
            )
        await run_tracker.patch(
            progress_message=str(exc),
            current_task=None,
        )
        if propagate_errors:
            raise
        return None


async def upload_playlist_to_castopod(
    castopod_client: CastopodClient,
    playlist_entry: PipelinePlaylist,
    result: DownloadResult,
    podcast_id: int | None = None,
    job_tracker: JobTracker | None = None,
    run_tracker: RunTracker | None = None,
) -> None:
    playlist = playlist_entry.playlist
    if podcast_id is None:
        podcast_id = castopod_client.resolve_podcast_id(playlist)
    if podcast_id is None:
        console.print(
            f"[yellow]경고:[/yellow] Castopod podcast를 찾을 수 없습니다 — "
            f"{playlist.castopod_slug or playlist.castopod_uuid}"
        )
        return
    for index, episode in enumerate(result.episodes, start=1):
        if job_tracker:
            await job_tracker.ensure_active()
        audio_path = episode.audio_path
        if not audio_path.exists():
            console.print(
                f"[yellow]경고:[/yellow] 오디오 파일이 없어 업로드를 건너뜁니다 — {audio_path}"
            )
            continue
        slug = slugify(episode.video_id or audio_path.stem)
        title = episode.title or audio_path.stem
        publication_dt = _episode_publication_datetime(episode)
        try:
            response = castopod_client.upload_episode(
                podcast_id,
                slug,
                title,
                episode.description,
                audio_path,
                episode.square_cover_path,
                publication_dt,
            )
            if response is not None:
                console.print(
                    f"[green]Castopod 업로드 완료[/green] — {title} ({slug})"
                )
            if job_tracker:
                await job_tracker.patch(
                    progress_completed=index,
                    progress_message=f"{index}/{result.downloaded} 업로드 완료",
                )
            if run_tracker:
                await run_tracker.patch(
                    progress_total=result.downloaded,
                    progress_completed=index,
                    progress_message=f"{index}/{result.downloaded} 업로드 완료",
                    current_task="castopod_upload",
                )
        except Exception as exc:
            console.print(
                f"[red]Castopod 업로드 실패[/red] — {title} ({slug}): {exc}"
            )


async def process_job_queue(
    client: AutomationServiceClient,
    config: PipelineConfiguration,
    download_root: Path,
    audio_format: str,
    dry_run: bool,
    castopod_client: CastopodClient | None,
) -> list[DownloadResult]:
    results: list[DownloadResult] = []
    jobs = await client.fetch_jobs()
    if not jobs:
        return results

    playlist_lookup: dict[int, tuple[PipelineChannel, PipelinePlaylist]] = {}
    for channel_entry in config.channels:
        for playlist_entry in channel_entry.playlists:
            playlist_lookup[playlist_entry.playlist.id] = (channel_entry, playlist_entry)

    for job in jobs:
        if job.status not in {"queued", "cancelling"}:
            continue
        mapping = playlist_lookup.get(job.playlist_id)
        if mapping is None:
            await client.update_job(job.id, status="failed", progress_message="Playlist not active")
            console.print(
                f"[red]작업 실패[/red] — playlist {job.playlist_id} not active"
            )
            continue
        console.rule(f"작업 실행: Job #{job.id}", style="magenta")
        tracker = JobTracker(client, job)
        if job.status == "cancelling":
            await tracker.patch(status="cancelled", progress_message="사용자 취소", current_task=None)
            continue
        await tracker.patch(
            status="in_progress",
            progress_total=0,
            progress_completed=0,
            current_task="downloading",
            progress_message="대기 중",
        )
        channel_entry, playlist_entry = mapping
        await tracker.start_watch()
        try:
            result = await process_playlist_entry(
                client,
                channel_entry,
                playlist_entry,
                download_root,
                audio_format,
                dry_run,
                castopod_client,
                allow_castopod_upload=job.should_castopod_upload,
                job_tracker=tracker,
                propagate_errors=True,
            )
            if result is None:
                continue
            await tracker.patch(
                status="finished",
                progress_total=result.downloaded,
                progress_completed=result.downloaded,
                current_task=None,
                progress_message="완료",
            )
            results.append(result)
        except JobCancelledError:
            await tracker.patch(
                status="cancelled",
                current_task=None,
                progress_message="사용자 취소",
            )
            console.print(f"[yellow]작업 취소[/yellow] — Job #{job.id}")
        except Exception as exc:  # pragma: no cover - runtime logging
            await tracker.patch(
                status="failed",
                progress_message=str(exc),
                current_task=None,
            )
            console.print(f"[red]작업 실패[/red] — Job #{job.id}: {exc}")
        finally:
            await tracker.stop_watch()
    return results

async def process_configuration(
    client: AutomationServiceClient,
    config: PipelineConfiguration,
    download_root: Path,
    audio_format: str,
    dry_run: bool,
    castopod_client: CastopodClient | None,
) -> list[DownloadResult]:
    results: list[DownloadResult] = []

    for channel_entry in config.channels:
        channel = channel_entry.channel
        for playlist_entry in channel_entry.playlists:
            console.rule(
                f"{channel.title}: {playlist_entry.playlist.title or playlist_entry.playlist.youtube_playlist_id}",
                style="cyan",
            )
            result = await process_playlist_entry(
                client,
                channel_entry,
                playlist_entry,
                download_root,
                audio_format,
                dry_run,
                castopod_client,
                allow_castopod_upload=True,
            )
            if result is not None:
                results.append(result)
    return results


async def async_main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute podcast automation pipeline")
    parser.add_argument(
        "--download-dir",
        default=os.getenv("PIPELINE_DOWNLOAD_DIR", "downloads"),
        help="Downloaded files destination (default: downloads)",
    )
    parser.add_argument(
        "--audio-format",
        default=os.getenv("PIPELINE_AUDIO_FORMAT", "mp3"),
        help="Audio format for extracted files (default: mp3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not download files, only simulate",
    )
    skip_config_default = env_flag("PIPELINE_SKIP_CONFIGURATION", False)
    parser.add_argument(
        "--skip-configuration",
        action="store_true",
        default=skip_config_default,
        help="Skip configured channels/playlists (default: env PIPELINE_SKIP_CONFIGURATION)",
    )
    parser.add_argument(
        "--include-configuration",
        dest="skip_configuration",
        action="store_false",
        help="Force processing configured channels even if skip flag/env is set",
    )
    parser.set_defaults(skip_configuration=skip_config_default)

    args = parser.parse_args(list(argv) if argv is not None else None)

    download_root = Path(args.download_dir).expanduser()

    console.print("[bold]Podcast Automation Pipeline[/bold]")
    console.print(f"Download dir: {download_root}")
    console.print(f"Audio format: {args.audio_format}")
    console.print(f"Dry run    : {args.dry_run}")

    castopod_config = load_castopod_config_from_env()
    castopod_client = CastopodClient(castopod_config) if castopod_config else None
    if castopod_client:
        console.print(
            f"[cyan]Castopod API 업로드 활성화됨 — {castopod_client._config.base_url}[/cyan]"
        )

    async with AutomationServiceClient() as client:
        config = await client.fetch_configuration()
        if not config.channels:
            console.print("[yellow]No channels configured. Nothing to do.[/yellow]")
            return 0
        job_results = await process_job_queue(
            client,
            config,
            download_root,
            args.audio_format,
            args.dry_run,
            castopod_client,
        )
        schedule_results: list[DownloadResult] = []
        if args.skip_configuration:
            console.print("[yellow]구성 채널 실행을 건너뜁니다 (skip-configuration 활성화)[/yellow]")
        else:
            schedule_results = await process_configuration(
                client,
                config,
                download_root,
                args.audio_format,
                args.dry_run,
                castopod_client,
            )

    if castopod_client:
        castopod_client.close()

    results = job_results + schedule_results

    table = Table(title="Pipeline summary")
    table.add_column("Playlist")
    table.add_column("Downloaded")
    table.add_column("Mode")
    for result in results:
        table.add_row(
            result.playlist_url,
            str(result.downloaded),
            "dry-run" if result.dry_run else "download",
        )
    console.print(table)

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
