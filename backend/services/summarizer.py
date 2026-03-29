import json
import os
import re
import time
from typing import Dict, List, Tuple

from groq import AsyncGroq

from utils.language_map import get_language_name


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_system_prompt(language_profile: Dict, output_language: str) -> str:
    lang_type = language_profile["type"]
    dominant = language_profile["dominant_language"]
    mix_str = ", ".join(
        f"{lang}: {pct}%" for lang, pct in language_profile["mix"].items()
    )

    return f"""You are an expert financial and news content analyst fluent in multiple languages.

The video has the following language profile:
- Type: {lang_type}
- Dominant language: {dominant}
- Language mix: {mix_str}

Your task: Write a DETAILED, SUBSTANTIVE summary of this video in **{output_language}**.

CONTENT RULES — this is the most important part:
- Extract SPECIFIC facts: names of people, companies, banks, regulators, exact figures, percentages, dates, policy decisions, stock movements, RBI actions, government orders — whatever is actually mentioned.
- NEVER write generic filler like "the speaker discusses X" or "the video covers Y". Instead write WHAT was actually said about X.
- Each key point must be a self-contained, informative sentence with concrete detail from the transcript — not a topic label.
- The overview must read like a dense news brief: who, what, why, what happened, what's the impact.
- The conclusion must state the actual takeaway or implication, not just "the video provides an update on...".

FORMAT RULES:
1. Return ONLY valid JSON — no markdown fences, no preamble, no trailing text.
2. Only reference timestamps that explicitly appear in the provided segment data. Do NOT invent timestamps.
3. The JSON must have exactly these five keys: title, overview, key_points, timestamps, conclusion.
4. key_points: 5–8 detailed bullet strings, each containing specific information.
5. timestamps: array of objects with keys "time" (number, seconds) and "label" (string — describe what specific thing is said/shown at that moment). Use [] if no meaningful timestamps exist.
6. Write ALL content in {output_language}.

Required JSON structure (follow exactly):
{{
  "title": "...",
  "overview": "...",
  "key_points": ["...", "...", "...", "...", "..."],
  "timestamps": [{{"time": 0, "label": "..."}}],
  "conclusion": "..."
}}"""


def _build_user_prompt(
    transcript_text: str, segments: List[Dict], output_language: str
) -> str:
    # Build a readable segment timeline — cap at 60 segments to stay within token budget
    timeline_lines: List[str] = []
    for seg in segments[:60]:
        lang_name = get_language_name(seg["language"])
        preview = seg.get("text", "").strip()[:80]
        timeline_lines.append(
            f"[{seg['start']:.1f}s – {seg['end']:.1f}s] ({lang_name}): {preview}"
        )
    timeline_str = "\n".join(timeline_lines)

    # Truncate full transcript to stay within token limits
    truncated = transcript_text[:4000]
    if len(transcript_text) > 4000:
        truncated += "\n[... transcript truncated ...]"

    return f"""Segment timeline (use ONLY these timestamps in your response):
{timeline_str}

Full transcript:
{truncated}

Summarize the above in {output_language}. Return only the JSON object."""


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------

def _parse_llm_json(content: str) -> Dict:
    """Strip markdown fences and extract the first complete JSON object."""
    content = content.strip()

    # Remove ```json ... ``` or ``` ... ``` fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if fence:
        content = fence.group(1).strip()

    # Fallback: find the outermost { … }
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end > start:
        content = content[start : end + 1]

    return json.loads(content)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_summary(
    transcript_text: str,
    segments: List[Dict],
    language_profile: Dict,
    output_language: str,
) -> Tuple[Dict, float]:
    """
    Call Groq llama-3.3-70b-versatile and return (summary_dict, elapsed_seconds).
    Raises ValueError if required keys are missing from the LLM response.
    """
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    system_prompt = _build_system_prompt(language_profile, output_language)
    user_prompt = _build_user_prompt(transcript_text, segments, output_language)

    t0 = time.perf_counter()

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1500,
        temperature=0.3,
    )

    elapsed = round(time.perf_counter() - t0, 2)
    raw_content = (response.choices[0].message.content or "").strip()
    summary = _parse_llm_json(raw_content)

    required_keys = {"title", "overview", "key_points", "timestamps", "conclusion"}
    missing = required_keys - set(summary.keys())
    if missing:
        raise ValueError(f"LLM response is missing required keys: {missing}")

    return summary, elapsed
