from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class Stage1Request(BaseModel):
    youtube_url: str


class Stage2Request(BaseModel):
    video_id: str
    output_language: str


class LanguageSegment(BaseModel):
    start: float
    end: float
    language: str
    confidence: float


class LanguageProfile(BaseModel):
    mix: Dict[str, float]
    dominant_language: str
    type: str
    detected_languages: List[str]


class Stage1Response(BaseModel):
    video_id: str
    language_profile: LanguageProfile
    segments: List[LanguageSegment]
    available_languages: List[str]


class TimestampEntry(BaseModel):
    time: float
    label: str


class SummaryContent(BaseModel):
    title: str
    overview: str
    key_points: List[str]
    timestamps: List[Any]
    conclusion: str


class Stage2Response(BaseModel):
    summary: SummaryContent
    output_language: str
    processing_time_seconds: float
