"""Tests for local storage and course/lecture persistence."""

from pathlib import Path
from scribo.storage.local_store import (
    save_lecture,
    save_transcript_only,
    load_lecture_notes,
    load_lecture_transcript,
    load_lecture_meta,
    list_courses,
    list_lectures,
    LectureMetadata,
)
from scribo.config import settings


def test_save_and_load_lecture(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "COURSES_DATA_DIR", tmp_path)

    notes_content = "# Lecture 1: Calculus\n\n## Limits\nDefinition of limits."
    transcript_content = "Welcome everyone. Today we discuss limits in calculus."
    audio_meta = {"duration_seconds": 120.5, "compressed_size_mb": 1.2}

    notes_p, trans_p, meta_p, meta = save_lecture(
        course_id="math101",
        lecture_id="lec01",
        title="Calculus Introduction",
        notes_content=notes_content,
        transcript_content=transcript_content,
        audio_meta=audio_meta,
        keywords=["limits", "derivatives"],
        synthesis_model="gemini-2.5-flash",
        stt_provider="gemini",
    )

    assert notes_p.exists()
    assert trans_p.exists()
    assert meta_p.exists()
    assert isinstance(meta, LectureMetadata)
    assert meta.course_id == "math101"
    assert meta.lecture_id == "lec01"
    assert meta.stt_provider == "gemini"

    # Test loading notes and transcript
    loaded_notes = load_lecture_notes("math101", "lec01")
    assert loaded_notes == notes_content

    loaded_transcript = load_lecture_transcript("math101", "lec01")
    assert loaded_transcript == transcript_content

    loaded_meta = load_lecture_meta("math101", "lec01")
    assert loaded_meta.lecture_title == "Calculus Introduction"
    assert loaded_meta.audio_metadata == audio_meta

    # Test listing
    courses = list_courses()
    assert "math101" in courses

    lectures = list_lectures("math101")
    assert len(lectures) == 1
    assert lectures[0].lecture_id == "lec01"
    assert lectures[0].transcript_file is not None


def test_save_transcript_only(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "COURSES_DATA_DIR", tmp_path)

    saved_p = save_transcript_only(
        course_id="cs101",
        lecture_id="lec02",
        transcript_content="Audio transcript text.",
    )
    assert saved_p.exists()
    assert load_lecture_transcript("cs101", "lec02") == "Audio transcript text."
