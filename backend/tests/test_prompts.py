"""Tests for synthesis and transcription prompts."""

from scribo.pipeline.synthesis.prompts import (
    SYSTEM_ACADEMIC_NOTE_PROMPT,
    build_audio_synthesis_prompt,
    build_transcript_synthesis_prompt,
    build_transcription_prompt,
)


def test_system_prompt_contains_rules():
    assert "Scribo" in SYSTEM_ACADEMIC_NOTE_PROMPT
    assert "LaTeX" in SYSTEM_ACADEMIC_NOTE_PROMPT
    assert "DISFLUENCIES" in SYSTEM_ACADEMIC_NOTE_PROMPT


def test_build_audio_synthesis_prompt():
    prompt = build_audio_synthesis_prompt(
        lecture_title="Fourier Transform",
        course_id="EE201",
        keywords=["Nyquist", "FFT"],
    )
    assert "Fourier Transform" in prompt
    assert "EE201" in prompt
    assert "Nyquist, FFT" in prompt


def test_build_transcript_synthesis_prompt():
    prompt = build_transcript_synthesis_prompt(
        transcript="Today we will discuss gradient descent.",
        lecture_title="Optimization",
        course_id="CS229",
        keywords=["convexity", "step size"],
    )
    assert "CS229" in prompt
    assert "Optimization" in prompt
    assert "gradient descent" in prompt
    assert "convexity, step size" in prompt


def test_build_transcription_prompt():
    prompt = build_transcription_prompt(keywords=["eigenvalue", "determinant"])
    assert "verbatim" in prompt
    assert "eigenvalue, determinant" in prompt
