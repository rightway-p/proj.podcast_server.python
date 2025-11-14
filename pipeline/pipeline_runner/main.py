from __future__ import annotations

import argparse
import asyncio
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from rich.console import Console
from rich.table import Table
import json

try:
    from yt_dlp import YoutubeDL
except ImportError:  # pragma: no cover - handled in runtime
    YoutubeDL = None  # type: ignore

from pipeline_client.client import (
    AutomationServiceClient,
    PipelineChannel,
    PipelineConfiguration,
    PipelinePlaylist,
)

console = Console()


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


@dataclass
class DownloadResult:
    playlist_url: str
    downloaded: int
    dry_run: bool
    episodes: list[EpisodeRecord]


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
) -> DownloadResult:
    if YoutubeDL is None:  # pragma: no cover - fallback for missing dependency
        raise RuntimeError("yt-dlp is not installed in this environment")

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
    if dry_run:
        ydl_opts["skip_download"] = True

    def _run() -> tuple[int, list[EpisodeRecord]]:
        episodes: list[EpisodeRecord] = []
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=not dry_run)
            if not info:
                return 0, episodes
            entries = info.get("entries") or []
            for entry in entries:
                if not entry:
                    continue
                base_filename = Path(ydl.prepare_filename(entry))
                audio_path = base_filename.with_suffix(f".{audio_format}")
                info_path = base_filename.with_suffix(".info.json")
                thumbnail_path = None
                for ext in (".jpg", ".webp", ".png"):
                    candidate = base_filename.with_suffix(ext)
                    if candidate.exists():
                        thumbnail_path = candidate
                        break
                episodes.append(
                    EpisodeRecord(
                        video_id=entry.get("id", ""),
                        title=entry.get("title", ""),
                        description=entry.get("description"),
                        webpage_url=entry.get("webpage_url"),
                        upload_date=entry.get("upload_date"),
                        duration=entry.get("duration"),
                        audio_path=audio_path,
                        info_path=info_path if info_path.exists() else None,
                        thumbnail_path=thumbnail_path,
                    )
                )
        return len(episodes), episodes

    downloaded, episodes = await asyncio.to_thread(_run)
    return DownloadResult(playlist_url, downloaded, dry_run, episodes)


def write_playlist_metadata(
    playlist_dir: Path,
    channel_entry: PipelineChannel,
    playlist_entry: PipelinePlaylist,
    result: DownloadResult,
) -> None:
    metadata_dir = playlist_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    playlist_meta = []
    for episode in result.episodes:
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
            }
        )

    payload = {
        "channel": {
            "id": channel_entry.channel.id,
            "slug": channel_entry.channel.slug,
            "title": channel_entry.channel.title,
            "description": channel_entry.channel.description,
        },
        "playlist": {
            "id": playlist_entry.playlist.id,
            "youtube_playlist_id": playlist_entry.playlist.youtube_playlist_id,
            "title": playlist_entry.playlist.title,
        },
        "episodes": playlist_meta,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    output_json = metadata_dir / "playlist.json"
    with output_json.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)

async def process_configuration(
    client: AutomationServiceClient,
    config: PipelineConfiguration,
    download_root: Path,
    audio_format: str,
    dry_run: bool,
) -> list[DownloadResult]:
    results: list[DownloadResult] = []

    for channel_entry in config.channels:
        channel = channel_entry.channel
        channel_dir = download_root / channel.slug
        for playlist_entry in channel_entry.playlists:
            playlist = playlist_entry.playlist
            playlist_dir = channel_dir / (playlist.title or playlist.youtube_playlist_id)

            console.rule(
                f"{channel.title}: {playlist.title or playlist.youtube_playlist_id}",
                style="cyan",
            )
            try:
                run_record = await client.create_run(
                    playlist_id=playlist.id,
                    status="in_progress",
                    message=f"Starting download into {playlist_dir}",
                )
                try:
                    result = await download_playlist(
                        playlist_entry,
                        playlist_dir,
                        audio_format,
                        dry_run,
                    )
                    write_playlist_metadata(
                        playlist_dir,
                        channel_entry,
                        playlist_entry,
                        result,
                    )
                    console.print(
                        f"[green]✓[/green] {playlist_dir} — "
                        f"{'simulated' if dry_run else 'downloaded'} {result.downloaded} entries"
                    )
                    await client.update_run(
                        run_record.id,
                        status="finished",
                        message=(
                            f"{'Simulated' if dry_run else 'Downloaded'} {result.downloaded} entries"
                        ),
                        finished_at=datetime.now(UTC),
                    )
                    results.append(result)
                except Exception as exc:  # pragma: no cover - runtime logging
                    await client.update_run(
                        run_record.id,
                        status="failed",
                        message=str(exc),
                        finished_at=datetime.now(UTC),
                    )
                    console.print(
                        f"[red]✗ {playlist_entry.playlist.youtube_playlist_id} 실패:[/red] {exc}"
                    )
                    continue
            except Exception as exc:  # pragma: no cover - runtime logging
                console.print(f"[red]오류:[/red] {exc}")
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

    args = parser.parse_args(list(argv) if argv is not None else None)

    download_root = Path(args.download_dir).expanduser()

    console.print("[bold]Podcast Automation Pipeline[/bold]")
    console.print(f"Download dir: {download_root}")
    console.print(f"Audio format: {args.audio_format}")
    console.print(f"Dry run    : {args.dry_run}")

    async with AutomationServiceClient() as client:
        config = await client.fetch_configuration()
        if not config.channels:
            console.print("[yellow]No channels configured. Nothing to do.[/yellow]")
            return 0
        results = await process_configuration(
            client,
            config,
            download_root,
            args.audio_format,
            args.dry_run,
        )

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
