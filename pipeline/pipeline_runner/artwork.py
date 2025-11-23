from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import httpx
from PIL import Image


def _sort_thumbnails(thumbnails: Sequence[Mapping[str, object]] | None) -> list[str]:
    if not thumbnails:
        return []
    scored = []
    for item in thumbnails:
        url = item.get("url") if isinstance(item, Mapping) else None
        if not isinstance(url, str):
            continue
        width = item.get("width") if isinstance(item, Mapping) else None
        height = item.get("height") if isinstance(item, Mapping) else None
        try:
            w = int(width) if width is not None else 0
            h = int(height) if height is not None else 0
        except (TypeError, ValueError):
            w = 0
            h = 0
        scored.append((w * h, url))
    scored.sort(key=lambda item: item[0], reverse=True)
    seen: set[str] = set()
    ordered: list[str] = []
    for _score, url in scored:
        if url in seen:
            continue
        seen.add(url)
        ordered.append(url)
    return ordered


def gather_thumbnail_urls(
    thumbnail_url: str | None,
    thumbnails: Sequence[Mapping[str, object]] | None,
) -> list[str]:
    candidates = _sort_thumbnails(thumbnails)
    if thumbnail_url and thumbnail_url not in candidates:
        candidates.append(thumbnail_url)
    return candidates


def _fetch_remote_image(urls: Iterable[str]) -> bytes | None:
    for url in urls:
        try:
            response = httpx.get(url, timeout=15.0, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError:
            continue
        return response.content
    return None


def _load_image_bytes(local_source: Path | None, remote_candidates: Iterable[str]) -> bytes | None:
    if local_source and local_source.exists():
        try:
            return local_source.read_bytes()
        except OSError:
            pass
    return _fetch_remote_image(remote_candidates)


def _pad_to_square(image: Image.Image, background_color: tuple[int, int, int]) -> Image.Image:
    width, height = image.size
    size = max(width, height)
    square = Image.new("RGB", (size, size), background_color)
    offset = ((size - width) // 2, (size - height) // 2)
    square.paste(image, offset)
    return square


def create_square_artwork(
    dest_path: Path,
    *,
    local_source: Path | None = None,
    remote_candidates: Iterable[str] = (),
    background_color: tuple[int, int, int] = (0, 0, 0),
) -> Path | None:
    image_bytes = _load_image_bytes(local_source, remote_candidates)
    if not image_bytes:
        return None

    rgb_image: Image.Image | None = None
    square_image: Image.Image | None = None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            rgb_image = img.convert("RGB")
        square_image = _pad_to_square(rgb_image, background_color)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        square_image.save(dest_path, format="JPEG", quality=95)
        return dest_path
    except OSError:
        return None
    finally:
        if rgb_image is not None:
            rgb_image.close()
        if square_image is not None:
            square_image.close()
