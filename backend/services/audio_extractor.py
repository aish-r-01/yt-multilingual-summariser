import asyncio
import os
import re
import shutil
from typing import Tuple

import yt_dlp

# Matches youtube.com and youtu.be domains
_YOUTUBE_DOMAIN_RE = re.compile(r"(youtube\.com|youtu\.be)")

# Ordered from most to least specific
_VIDEO_ID_PATTERNS = [
    re.compile(r"[?&]v=([0-9A-Za-z_-]{11})"),
    re.compile(r"youtu\.be/([0-9A-Za-z_-]{11})"),
    re.compile(r"/embed/([0-9A-Za-z_-]{11})"),
    re.compile(r"/shorts/([0-9A-Za-z_-]{11})"),
    re.compile(r"/v/([0-9A-Za-z_-]{11})"),
]


def validate_youtube_url(url: str) -> bool:
    return bool(_YOUTUBE_DOMAIN_RE.search(url))


def extract_video_id(url: str) -> str:
    for pattern in _VIDEO_ID_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def _sync_extract_audio(url: str) -> Tuple[str, str]:
    """
    Download the best audio stream, convert to mp3 via ffmpeg, and return
    (video_id, /tmp/<video_id>.mp3).  Raises ValueError for business-rule
    violations (too long, private, unavailable).
    """
    video_id = extract_video_id(url)
    output_path = f"/tmp/{video_id}.mp3"

    max_minutes = int(os.getenv("MAX_VIDEO_DURATION_MINUTES", "30"))
    max_seconds = max_minutes * 60

    # Resolve ffmpeg — prefer explicit path so the server works regardless of PATH
    ffmpeg_location = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"/tmp/{video_id}.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
        "ffmpeg_location": ffmpeg_location,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Fetch info without downloading first so we can validate
        info = ydl.extract_info(url, download=False)

        if info is None:
            raise ValueError("Video not found or unavailable.")

        # Duration check
        duration = info.get("duration") or 0
        if duration > max_seconds:
            raise ValueError(f"Video too long, max {max_minutes} minutes")

        # Privacy / availability check
        availability = info.get("availability") or ""
        is_private = info.get("is_private", False)
        if is_private or availability in (
            "private",
            "subscriber_only",
            "needs_auth",
            "premium_only",
        ):
            raise ValueError(
                f"Video is private or unavailable (status: {availability or 'private'})."
            )

        # Now actually download
        ydl.download([url])

    return video_id, output_path


async def extract_audio(url: str) -> Tuple[str, str]:
    """Async wrapper — runs the blocking yt-dlp call in a thread pool."""
    return await asyncio.to_thread(_sync_extract_audio, url)
