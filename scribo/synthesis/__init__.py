"""Note synthesis and LLM processing module."""

from .synthesizer import NoteSynthesizer
from .prompts import (
    SYSTEM_ACADEMIC_NOTE_PROMPT,
    build_audio_synthesis_prompt,
    build_transcript_synthesis_prompt,
    build_transcription_prompt,
)

__all__ = [
    "NoteSynthesizer",
    "SYSTEM_ACADEMIC_NOTE_PROMPT",
    "build_audio_synthesis_prompt",
    "build_transcript_synthesis_prompt",
    "build_transcription_prompt",
]
