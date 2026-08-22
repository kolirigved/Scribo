"""Speech-to-Text (STT) transcription module supporting timestamped segments and structured output."""

import os
from pathlib import Path
from typing import Optional, Literal
import httpx
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from scribo.config import settings
from scribo.pipeline.synthesis.prompts import build_transcription_prompt

STTProvider = Literal["gemini", "groq", "openai"]


class TranscriptSegment(BaseModel):
    """An individual timestamped speech segment."""
    id: int
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    """Rich transcription result with segments and formatted text."""
    raw_text: str
    formatted_text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)
    language: Optional[str] = "english"
    duration_seconds: Optional[float] = None
    provider: str = "gemini"


def format_seconds_to_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS string."""
    total_sec = int(round(seconds))
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def group_segments_into_paragraphs(
    segments: list[TranscriptSegment],
    group_interval_seconds: float = 30.0,
) -> str:
    """Format speech segments into timestamped, readable paragraph blocks."""
    if not segments:
        return ""

    paragraphs = []
    current_block_text = []
    block_start_time = segments[0].start

    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue

        # If current block exceeds group interval or natural sentence break, flush paragraph
        if current_block_text and (seg.start - block_start_time >= group_interval_seconds):
            time_tag = format_seconds_to_timestamp(block_start_time)
            paragraph_body = " ".join(current_block_text)
            paragraphs.append(f"[{time_tag}] {paragraph_body}")
            current_block_text = [text]
            block_start_time = seg.start
        else:
            current_block_text.append(text)

    if current_block_text:
        time_tag = format_seconds_to_timestamp(block_start_time)
        paragraph_body = " ".join(current_block_text)
        paragraphs.append(f"[{time_tag}] {paragraph_body}")

    return "\n\n".join(paragraphs)


class AudioTranscriber:
    """Unified transcription engine supporting Gemini, Groq Whisper, and OpenAI Whisper."""

    def __init__(
        self,
        provider: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.provider = (provider or settings.DEFAULT_STT_PROVIDER).lower()
        self.gemini_api_key = gemini_api_key if gemini_api_key is not None else settings.GEMINI_API_KEY
        self.groq_api_key = groq_api_key if groq_api_key is not None else settings.GROQ_API_KEY
        self.openai_api_key = openai_api_key if openai_api_key is not None else settings.OPENAI_API_KEY

    def transcribe(
        self,
        audio_path: Path | str,
        keywords: Optional[list[str]] = None,
        provider: Optional[str] = None,
    ) -> TranscriptResult:
        """Transcribe an audio file into a rich TranscriptResult.

        Args:
            audio_path: Path to the audio file.
            keywords: Optional list of technical terminology hints.
            provider: Override STT provider ("gemini", "groq", "openai").

        Returns:
            TranscriptResult: Contains raw_text, timestamped formatted_text, and segment objects.
        """
        path = Path(audio_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        chosen_provider = (provider or self.provider).lower()

        if chosen_provider == "gemini":
            return self._transcribe_gemini(path, keywords=keywords)
        elif chosen_provider == "groq":
            return self._transcribe_groq(path, keywords=keywords)
        elif chosen_provider == "openai":
            return self._transcribe_openai(path, keywords=keywords)
        else:
            raise ValueError(
                f"Unsupported STT provider: '{chosen_provider}'. Choose from 'gemini', 'groq', or 'openai'."
            )

    def _transcribe_gemini(self, path: Path, keywords: Optional[list[str]] = None) -> TranscriptResult:
        """Transcribe using Google Gemini audio understanding with timestamp markers."""
        if not self.gemini_api_key or self.gemini_api_key.startswith("your_"):
            raise ValueError("GEMINI_API_KEY is not configured for Gemini STT.")

        client = genai.Client(api_key=self.gemini_api_key)
        prompt_text = (
            "Please transcribe the following lecture audio verbatim. "
            "Format the output into clear paragraphs with timestamps at the beginning of each major topic or paragraph in the format [MM:SS]."
        )
        if keywords:
            prompt_text += f" Technical terminology hints: {', '.join(keywords)}."

        uploaded_file = None
        try:
            uploaded_file = client.files.upload(file=str(path))
            response = client.models.generate_content(
                model=settings.DEFAULT_MODEL,
                contents=[uploaded_file, prompt_text],
                config=types.GenerateContentConfig(temperature=0.0),
            )
            raw_text = response.text or ""
            return TranscriptResult(
                raw_text=raw_text,
                formatted_text=raw_text,
                segments=[],
                provider="gemini",
            )
        finally:
            if uploaded_file is not None and hasattr(uploaded_file, "name"):
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

    def _transcribe_groq(self, path: Path, keywords: Optional[list[str]] = None) -> TranscriptResult:
        """Transcribe using Groq Whisper large-v3 with verbose JSON segment timestamps."""
        if not self.groq_api_key or self.groq_api_key.startswith("your_"):
            raise ValueError("GROQ_API_KEY is not configured for Groq Whisper STT.")

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}"}

        data = {
            "model": "whisper-large-v3",
            "response_format": "verbose_json",
        }
        if keywords:
            data["prompt"] = ", ".join(keywords)

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "audio/mpeg")}
            response = httpx.post(url, headers=headers, data=data, files=files, timeout=300.0)

        if response.status_code != 200:
            raise RuntimeError(f"Groq Whisper transcription failed: {response.text}")

        res_json = response.json()
        raw_text = res_json.get("text", "").strip()
        raw_segments = res_json.get("segments", [])

        segments = [
            TranscriptSegment(
                id=idx,
                start=round(float(s.get("start", 0.0)), 2),
                end=round(float(s.get("end", 0.0)), 2),
                text=s.get("text", "").strip(),
            )
            for idx, s in enumerate(raw_segments)
        ]

        formatted_text = group_segments_into_paragraphs(segments)
        if not formatted_text:
            formatted_text = raw_text

        return TranscriptResult(
            raw_text=raw_text,
            formatted_text=formatted_text,
            segments=segments,
            language=res_json.get("language", "english"),
            duration_seconds=res_json.get("duration"),
            provider="groq",
        )

    def _transcribe_openai(self, path: Path, keywords: Optional[list[str]] = None) -> TranscriptResult:
        """Transcribe using OpenAI Whisper API with verbose JSON timestamps."""
        if not self.openai_api_key or self.openai_api_key.startswith("your_"):
            raise ValueError("OPENAI_API_KEY is not configured for OpenAI Whisper STT.")

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}"}

        data = {
            "model": "whisper-1",
            "response_format": "verbose_json",
        }
        if keywords:
            data["prompt"] = ", ".join(keywords)

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "audio/mpeg")}
            response = httpx.post(url, headers=headers, data=data, files=files, timeout=300.0)

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI Whisper transcription failed: {response.text}")

        res_json = response.json()
        raw_text = res_json.get("text", "").strip()
        raw_segments = res_json.get("segments", [])

        segments = [
            TranscriptSegment(
                id=idx,
                start=round(float(s.get("start", 0.0)), 2),
                end=round(float(s.get("end", 0.0)), 2),
                text=s.get("text", "").strip(),
            )
            for idx, s in enumerate(raw_segments)
        ]

        formatted_text = group_segments_into_paragraphs(segments)
        if not formatted_text:
            formatted_text = raw_text

        return TranscriptResult(
            raw_text=raw_text,
            formatted_text=formatted_text,
            segments=segments,
            language=res_json.get("language", "english"),
            duration_seconds=res_json.get("duration"),
            provider="openai",
        )


def transcribe_audio(
    audio_path: Path | str,
    keywords: Optional[list[str]] = None,
    provider: Optional[str] = None,
) -> TranscriptResult:
    """Convenience helper to transcribe audio with auto-configured provider."""
    transcriber = AudioTranscriber(provider=provider)
    return transcriber.transcribe(audio_path, keywords=keywords)
