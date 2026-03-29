# yt-multilingual-summariser

> Transcribe, analyze, and summarize any YouTube video — across languages — in under two minutes. For people with shrinking attention spans who'd rather read a sharp summary than sit through 40 minutes at 2x speed.


A two-stage pipeline that extracts audio from YouTube, runs multilingual transcription via Groq Whisper, detects language distribution at the segment level, and produces a structured LLM summary in any target language. Designed for regional language content where auto-captions fail and code-switching is the norm.


---

## Motivation

A significant share of high-quality YouTube content — finance, education, news analysis — exists in Hindi, Tamil, Telugu, Kannada, and other regional languages. This content is largely inaccessible to:

- Non-native speakers who want the information but not the language barrier
- Native speakers who want to filter content before committing watch time
- Researchers and analysts working across multiple language sources

Existing solutions fall short: YouTube's auto-captions break on regional languages and code-switching, and no tool surfaces *which language was spoken when* alongside a summary.

---

## Features

- **Segment-level language detection** — identifies language per Whisper segment with inheritance fallback, not just a single top-level label
- **Language mix visualization** — percentage breakdown and full timeline showing exactly when each language was spoken
- **Structured summaries** — title, overview, key points (with actual content, not topic labels), real timestamps from transcript data, and conclusion
- **Any output language** — summarize a Telugu video in English, a Hindi video in Tamil, or keep it in the original
- **Monolingual / Code-mixed / Heavily Mixed classification** — automatically categorized based on dominant language distribution
- **1-hour TTL cache** — transcripts stored in memory with background eviction; no database required

---

## Architecture

```
POST /api/stage1                          POST /api/stage2
      │                                         │
      ▼                                         ▼
yt-dlp → ffmpeg (mp3)             In-memory transcript store
      │                                         │
      ▼                                         ▼
Groq Whisper                    Groq LLaMA 3.3 70B (structured JSON)
(verbose_json, auto-detect)               │
      │                                         ▼
      ▼                           title · overview · key_points
Segment language analysis         timestamps · conclusion
+ grouping + mix %
      │
      ▼
In-memory store (TTL: 1hr)
```

**Backend:** Python · FastAPI · uvicorn · yt-dlp · Groq SDK

**Frontend:** React · Vite · Tailwind CSS

---

## Getting started

### Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | |
| Node.js 18+ | |
| ffmpeg | `brew install ffmpeg` on macOS |
| Groq API key | Free tier available at [console.groq.com](https://console.groq.com) |

### Backend

```bash
cd backend

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env .env.local   # or edit .env directly
# Set GROQ_API_KEY=gsk_...

uvicorn main:app --reload
# Listening on http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Listening on http://localhost:5173
```

---

## API

### `POST /api/stage1`

Validates the URL, downloads audio, transcribes, and returns the language profile.

```json
// Request
{ "youtube_url": "https://youtube.com/watch?v=..." }

// Response
{
  "video_id": "dQw4w9WgXcQ",
  "language_profile": {
    "mix": { "Hindi": 68.4, "English": 31.6 },
    "dominant_language": "Hindi",
    "type": "Code-mixed",
    "detected_languages": ["Hindi", "English"]
  },
  "segments": [
    { "start": 0.0, "end": 12.4, "language": "Hindi", "confidence": 0.91 }
  ],
  "available_languages": ["English", "Hindi"]
}
```

### `POST /api/stage2`

Retrieves the cached transcript and generates a structured summary.

```json
// Request
{ "video_id": "dQw4w9WgXcQ", "output_language": "English" }

// Response
{
  "summary": {
    "title": "...",
    "overview": "...",
    "key_points": ["...", "..."],
    "timestamps": [{ "time": 94.0, "label": "..." }],
    "conclusion": "..."
  },
  "output_language": "English",
  "processing_time_seconds": 18.4
}
```

### `GET /health`

Returns server status and number of active cached transcripts.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Required. Groq API key |
| `MAX_VIDEO_DURATION_MINUTES` | `30` | Videos exceeding this are rejected before download |

---

## Constraints

- Free Groq tier: ~12k tokens per minute. Very long videos may require a retry.
- Transcript cache is in-memory — restarting the server clears it. Re-analyze if needed.
- Per-segment language fields from Whisper are not guaranteed; segments without a language tag inherit from the previous segment (fallback: top-level detected language).
