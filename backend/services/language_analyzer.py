import math
from typing import Any, Dict, List

from utils.language_map import get_language_name


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_attr(obj: Any, key: str, default=None):
    """Works whether obj is a Pydantic/dataclass object or a plain dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _segment_confidence(segment: Any) -> float:
    """
    Convert Whisper's avg_logprob (≤ 0) to a 0-1 confidence score via
    math.exp().  Falls back to 0.5 if the field is missing or invalid.
    """
    raw = _get_attr(segment, "avg_logprob")
    if raw is None:
        return 0.5
    try:
        return round(min(1.0, max(0.0, math.exp(float(raw)))), 4)
    except (ValueError, TypeError):
        return 0.5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_languages(whisper_response: Any, raw_segments: List[Any]) -> Dict:
    """
    Build a processed segment list with per-segment language codes (with
    inheritance fallback) and compute the video-level language profile.

    Returns:
        {
            "language_profile": {
                "mix": {"Hindi": 62.3, "English": 37.7},
                "dominant_language": "Hindi",
                "type": "Code-mixed",
                "detected_languages": ["Hindi", "English"],
            },
            "processed_segments": [
                {"start": 0.0, "end": 4.2, "language": "hi",
                 "confidence": 0.82, "text": "..."},
                …
            ],
        }
    """
    top_level_language: str = _get_attr(whisper_response, "language") or "en"

    processed: List[Dict] = []
    prev_language = top_level_language

    for seg in raw_segments:
        lang = _get_attr(seg, "language") or prev_language
        prev_language = lang

        processed.append(
            {
                "start": float(_get_attr(seg, "start") or 0.0),
                "end": float(_get_attr(seg, "end") or 0.0),
                "language": lang,
                "confidence": _segment_confidence(seg),
                "text": (_get_attr(seg, "text") or "").strip(),
            }
        )

    # --- Language mix by total duration ---
    duration_by_lang: Dict[str, float] = {}
    total_duration = 0.0
    for seg in processed:
        d = seg["end"] - seg["start"]
        duration_by_lang[seg["language"]] = duration_by_lang.get(seg["language"], 0.0) + d
        total_duration += d

    mix: Dict[str, float] = {}
    if total_duration > 0:
        for code, dur in duration_by_lang.items():
            name = get_language_name(code)
            mix[name] = round((dur / total_duration) * 100, 1)

    # --- Dominant language ---
    dominant_code = (
        max(duration_by_lang, key=lambda k: duration_by_lang[k])
        if duration_by_lang
        else top_level_language
    )
    dominant_language = get_language_name(dominant_code)

    # --- Type classification ---
    num_langs = len(duration_by_lang)
    dominant_pct = mix.get(dominant_language, 100.0)

    if num_langs == 1 or dominant_pct >= 90:
        lang_type = "Monolingual"
    elif dominant_pct >= 60:
        lang_type = "Code-mixed"
    else:
        lang_type = "Heavily Mixed"

    detected_languages = [get_language_name(c) for c in duration_by_lang]

    return {
        "language_profile": {
            "mix": mix,
            "dominant_language": dominant_language,
            "type": lang_type,
            "detected_languages": detected_languages,
        },
        "processed_segments": processed,
    }


def group_segments_by_language(processed_segments: List[Dict]) -> List[Dict]:
    """
    Merge consecutive segments that share the same language code into a
    single timeline block.  Confidence is averaged across the merged block.
    """
    if not processed_segments:
        return []

    grouped: List[Dict] = []
    current: Dict | None = None
    current_count = 0

    for seg in processed_segments:
        if current is None:
            current = {**seg}
            current_count = 1
        elif seg["language"] == current["language"]:
            current["end"] = seg["end"]
            # Incremental mean for confidence
            current_count += 1
            current["confidence"] += (seg["confidence"] - current["confidence"]) / current_count
            current["text"] = (current["text"] + " " + seg["text"]).strip()
        else:
            current["confidence"] = round(current["confidence"], 4)
            grouped.append(current)
            current = {**seg}
            current_count = 1

    if current:
        current["confidence"] = round(current["confidence"], 4)
        grouped.append(current)

    return grouped
