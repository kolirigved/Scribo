"""Local persistence for synthesized lecture notes, transcripts, and metadata.

Saves lecture assets into a structured course hierarchy:
  data/courses/<course_id>/lecture_<lecture_id>.md              # Structured notes
  data/courses/<course_id>/lecture_<lecture_id>_transcript.txt  # Human-readable timestamped transcript
  data/courses/<course_id>/lecture_<lecture_id>_transcript.json # Structured segment transcript (Frontend ready)
  data/courses/<course_id>/lecture_<lecture_id>_meta.json       # Metadata & metrics
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field

from scribo.config import settings


class LectureMetadata(BaseModel):
    """Schema for lecture metadata."""
    course_id: str
    lecture_id: str
    lecture_title: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes_file: str
    transcript_file: Optional[str] = None
    transcript_json_file: Optional[str] = None
    metadata_file: str
    keywords: list[str] = Field(default_factory=list)
    synthesis_model: Optional[str] = None
    stt_provider: Optional[str] = None
    audio_metadata: Optional[dict[str, Any]] = None
    extra: dict[str, Any] = Field(default_factory=dict)


def get_course_dir(course_id: str) -> Path:
    """Get or create the directory path for a course."""
    normalized_course = course_id.strip().lower()
    course_dir = settings.COURSES_DATA_DIR / normalized_course
    course_dir.mkdir(parents=True, exist_ok=True)
    return course_dir


def save_lecture(
    course_id: str,
    lecture_id: str,
    title: str,
    notes_content: str,
    transcript_content: Optional[str] = None,
    transcript_segments: Optional[list[dict[str, Any]]] = None,
    audio_meta: Optional[dict[str, Any]] = None,
    keywords: Optional[list[str]] = None,
    synthesis_model: Optional[str] = None,
    stt_provider: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> tuple[Path, Optional[Path], Path, LectureMetadata]:
    """Persist synthesized lecture notes, transcript, and metadata.

    Args:
        course_id: Identifier for the course (e.g., 'cs101').
        lecture_id: Identifier for the lecture (e.g., 'lec01').
        title: Title of the lecture.
        notes_content: Synthesized Markdown content.
        transcript_content: Optional formatted transcript text.
        transcript_segments: Optional list of segment dicts with timestamps.
        audio_meta: Optional audio metrics and compression stats.
        keywords: Optional technical keywords.
        synthesis_model: Model used for synthesis.
        stt_provider: STT provider used (e.g., "gemini", "groq", "openai").
        extra: Additional metadata attributes.

    Returns:
        tuple[Path, Optional[Path], Path, LectureMetadata]:
            (notes_path, transcript_path, metadata_path, metadata_obj)
    """
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")

    notes_filename = f"lecture_{safe_lecture_id}.md"
    transcript_filename = f"lecture_{safe_lecture_id}_transcript.txt"
    transcript_json_filename = f"lecture_{safe_lecture_id}_transcript.json"
    meta_filename = f"lecture_{safe_lecture_id}_meta.json"

    notes_path = course_dir / notes_filename
    meta_path = course_dir / meta_filename
    transcript_path = None
    transcript_json_path = None

    # Save markdown notes
    notes_path.write_text(notes_content, encoding="utf-8")

    # Save human-readable formatted transcript
    if transcript_content is not None:
        transcript_path = course_dir / transcript_filename
        transcript_path.write_text(transcript_content, encoding="utf-8")

    # Save structured segment transcript for frontend player
    if transcript_segments is not None:
        transcript_json_path = course_dir / transcript_json_filename
        transcript_json_data = {
            "course_id": course_id,
            "lecture_id": safe_lecture_id,
            "title": title,
            "segments": transcript_segments,
        }
        transcript_json_path.write_text(json.dumps(transcript_json_data, indent=2), encoding="utf-8")

    # Build and save metadata
    metadata = LectureMetadata(
        course_id=course_id,
        lecture_id=safe_lecture_id,
        lecture_title=title,
        notes_file=str(notes_path),
        transcript_file=str(transcript_path) if transcript_path else None,
        transcript_json_file=str(transcript_json_path) if transcript_json_path else None,
        metadata_file=str(meta_path),
        keywords=keywords or [],
        synthesis_model=synthesis_model or settings.DEFAULT_MODEL,
        stt_provider=stt_provider,
        audio_metadata=audio_meta,
        extra=extra or {},
    )

    meta_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    return notes_path, transcript_path, meta_path, metadata


def save_transcript_only(
    course_id: str,
    lecture_id: str,
    transcript_content: str,
    transcript_segments: Optional[list[dict[str, Any]]] = None,
    title: Optional[str] = None,
    audio_meta: Optional[dict[str, Any]] = None,
    stt_provider: Optional[str] = None,
    keywords: Optional[list[str]] = None,
) -> tuple[Path, Optional[Path]]:
    """Save raw and JSON transcript files independently."""
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")
    transcript_path = course_dir / f"lecture_{safe_lecture_id}_transcript.txt"
    transcript_path.write_text(transcript_content, encoding="utf-8")

    transcript_json_path = None
    if transcript_segments is not None:
        transcript_json_path = course_dir / f"lecture_{safe_lecture_id}_transcript.json"
        transcript_json_data = {
            "course_id": course_id,
            "lecture_id": safe_lecture_id,
            "title": title or f"Lecture {safe_lecture_id}",
            "segments": transcript_segments,
        }
        transcript_json_path.write_text(json.dumps(transcript_json_data, indent=2), encoding="utf-8")

    return transcript_path, transcript_json_path


def load_lecture_notes(course_id: str, lecture_id: str) -> str:
    """Load Markdown notes for a lecture."""
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")
    notes_path = course_dir / f"lecture_{safe_lecture_id}.md"

    if not notes_path.exists():
        raise FileNotFoundError(f"Lecture notes not found: {notes_path}")

    return notes_path.read_text(encoding="utf-8")


def load_lecture_transcript(course_id: str, lecture_id: str) -> str:
    """Load raw transcript for a lecture."""
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")
    transcript_path = course_dir / f"lecture_{safe_lecture_id}_transcript.txt"

    if not transcript_path.exists():
        raise FileNotFoundError(f"Lecture transcript not found: {transcript_path}")

    return transcript_path.read_text(encoding="utf-8")


def save_slides_text(course_id: str, lecture_id: str, text: str) -> Path:
    """Save extracted slide text."""
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")
    slides_path = course_dir / f"lecture_{safe_lecture_id}_slides.txt"
    slides_path.write_text(text, encoding="utf-8")
    return slides_path


def load_slides_text(course_id: str, lecture_id: str) -> str:
    """Load extracted slide text."""
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")
    slides_path = course_dir / f"lecture_{safe_lecture_id}_slides.txt"

    if not slides_path.exists():
        raise FileNotFoundError(f"Lecture slides not found: {slides_path}")

    return slides_path.read_text(encoding="utf-8")



def load_lecture_transcript_json(course_id: str, lecture_id: str) -> dict[str, Any]:
    """Load structured JSON transcript with timestamps."""
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")
    json_path = course_dir / f"lecture_{safe_lecture_id}_transcript.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Structured transcript JSON not found: {json_path}")

    return json.loads(json_path.read_text(encoding="utf-8"))


def load_lecture_meta(course_id: str, lecture_id: str) -> LectureMetadata:
    """Load metadata for a lecture."""
    course_dir = get_course_dir(course_id)
    safe_lecture_id = lecture_id.strip().lower().replace(" ", "_")
    meta_path = course_dir / f"lecture_{safe_lecture_id}_meta.json"

    if not meta_path.exists():
        raise FileNotFoundError(f"Lecture metadata not found: {meta_path}")

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return LectureMetadata(**data)


def list_courses() -> list[str]:
    """List all courses in local storage."""
    if not settings.COURSES_DATA_DIR.exists():
        return []
    return sorted(
        [p.name for p in settings.COURSES_DATA_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]
    )


def list_lectures(course_id: str) -> list[LectureMetadata]:
    """List all lectures in a course with metadata."""
    course_dir = get_course_dir(course_id)
    lectures = []

    for meta_file in sorted(course_dir.glob("lecture_*_meta.json")):
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            lectures.append(LectureMetadata(**data))
        except Exception:
            continue

    return lectures
