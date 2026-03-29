import os
import time

import groq as groq_module
from fastapi import APIRouter, HTTPException

from models.schemas import Stage1Request, Stage2Request
from services.audio_extractor import extract_audio, validate_youtube_url
from services.language_analyzer import analyze_languages, group_segments_by_language
from services.summarizer import generate_summary
from services.transcriber import transcribe_audio
from utils.language_map import get_language_name

router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# In-memory transcript store
# key:   video_id (str)
# value: { transcript_text, segments, language_analysis, created_at }
# ---------------------------------------------------------------------------
transcript_store: dict = {}


# ---------------------------------------------------------------------------
# Stage 1 — Audio extraction + language analysis
# ---------------------------------------------------------------------------

@router.post("/stage1")
async def stage1(request: Stage1Request):
    # 1. Validate URL
    if not validate_youtube_url(request.youtube_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must be a YouTube URL (youtube.com or youtu.be).",
        )

    # 2. Extract audio
    try:
        video_id, audio_path = await extract_audio(request.youtube_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        err_lower = str(exc).lower()
        if any(w in err_lower for w in ("private", "unavailable", "not available", "members only")):
            raise HTTPException(
                status_code=400, detail=f"Video is private or unavailable: {exc}"
            )
        raise HTTPException(status_code=500, detail=f"Audio extraction failed: {exc}")

    # 3. Transcribe
    try:
        whisper_response = await transcribe_audio(audio_path)
    except groq_module.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Groq rate limit reached. Please wait a moment and try again.",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")
    finally:
        # Always clean up the mp3
        if os.path.exists(audio_path):
            os.remove(audio_path)

    # 4. Analyze languages
    raw_segments = getattr(whisper_response, "segments", []) or []
    analysis = analyze_languages(whisper_response, raw_segments)
    grouped_segments = group_segments_by_language(analysis["processed_segments"])

    # 5. Build available_languages — detected codes + "en", deduplicated, sorted
    detected_codes = {seg["language"] for seg in analysis["processed_segments"]}
    detected_codes.add("en")
    available_languages = sorted(get_language_name(c) for c in detected_codes)

    # 6. Cache in memory
    transcript_store[video_id] = {
        "transcript_text": getattr(whisper_response, "text", "") or "",
        "segments": analysis["processed_segments"],
        "language_analysis": analysis["language_profile"],
        "created_at": time.time(),
    }

    # 7. Return
    return {
        "video_id": video_id,
        "language_profile": analysis["language_profile"],
        "segments": [
            {
                "start": seg["start"],
                "end": seg["end"],
                "language": get_language_name(seg["language"]),
                "confidence": seg["confidence"],
            }
            for seg in grouped_segments
        ],
        "available_languages": available_languages,
    }


# ---------------------------------------------------------------------------
# Stage 2 — Summary generation
# ---------------------------------------------------------------------------

@router.post("/stage2")
async def stage2(request: Stage2Request):
    # 1. Retrieve cached transcript
    entry = transcript_store.get(request.video_id)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Video not found in cache. Please re-analyze the video first.",
        )

    # 2. Generate summary
    try:
        summary, processing_time = await generate_summary(
            transcript_text=entry["transcript_text"],
            segments=entry["segments"],
            language_profile=entry["language_analysis"],
            output_language=request.output_language,
        )
    except groq_module.RateLimitError as exc:
        msg = str(exc)
        if "413" in msg or "too large" in msg.lower() or "request too large" in msg.lower():
            raise HTTPException(
                status_code=413,
                detail="Transcript too long for the model's token limit. Try a shorter video.",
            )
        raise HTTPException(
            status_code=429,
            detail="Groq rate limit reached. Please wait a moment and try again.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        err = str(exc)
        if "413" in err or "too large" in err.lower():
            raise HTTPException(
                status_code=413,
                detail="Transcript too long for the model's token limit. Try a shorter video.",
            )
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}")

    return {
        "summary": summary,
        "output_language": request.output_language,
        "processing_time_seconds": processing_time,
    }
