import asyncio
import logging
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env before importing anything that reads env vars
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.summarize import router, transcript_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

_TTL_SECONDS = 3600  # 1 hour
_CLEANUP_INTERVAL = 300  # check every 5 minutes


async def _cleanup_loop() -> None:
    """Background task: evict transcript_store entries older than TTL."""
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL)
        now = time.time()
        expired = [
            k
            for k, v in list(transcript_store.items())
            if now - v["created_at"] > _TTL_SECONDS
        ]
        for key in expired:
            del transcript_store[key]
            logger.info("Evicted cached transcript: %s", key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    logger.info("Transcript cleanup task started (TTL=%ds, interval=%ds)", _TTL_SECONDS, _CLEANUP_INTERVAL)
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Transcript cleanup task stopped.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="YouTube Regional Summarizer API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "cached_videos": len(transcript_store)}
