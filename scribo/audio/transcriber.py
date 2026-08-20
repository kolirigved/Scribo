"""Speech-to-Text (STT) transcription module supporting Gemini and Whisper (Groq/OpenAI)."""

import os
from pathlib import Path
from typing import Optional, Literal
import httpx
from google import genai
from google.genai import types

from scribo.config import settings
from scribo.synthesis.prompts import build_transcription_prompt

STTProvider = Literal["gemini", "groq", "openai"]


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
        self.gemini_api_key = gemini_api_key or settings.GEMINI_API_KEY
        self.groq_api_key = groq_api_key or settings.GROQ_API_KEY
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY

    def transcribe(
        self,
        audio_path: Path | str,
        keywords: Optional[list[str]] = None,
        provider: Optional[str] = None,
    ) -> str:
        """Transcribe an audio file into text.

        Args:
            audio_path: Path to the audio file.
            keywords: Optional list of technical terminology hints.
            provider: Override STT provider ("gemini", "groq", "openai").

        Returns:
            str: Raw transcript text.
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

    def _transcribe_gemini(self, path: Path, keywords: Optional[list[str]] = None) -> str:
        """Transcribe using Google Gemini audio understanding."""
        if not self.gemini_api_key or self.gemini_api_key.startswith("your_"):
            raise ValueError("GEMINI_API_KEY is not configured for Gemini STT.")

        client = genai.Client(api_key=self.gemini_api_key)
        prompt_text = build_transcription_prompt(keywords=keywords)

        uploaded_file = None
        try:
            uploaded_file = client.files.upload(file=str(path))
            response = client.models.generate_content(
                model=settings.DEFAULT_MODEL,
                contents=[uploaded_file, prompt_text],
                config=types.GenerateContentConfig(temperature=0.0),
            )
            return response.text or ""
        finally:
            if uploaded_file is not None and hasattr(uploaded_file, "name"):
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

    def _transcribe_groq(self, path: Path, keywords: Optional[list[str]] = None) -> str:
        """Transcribe using Groq Whisper large-v3."""
        if not self.groq_api_key or self.groq_api_key.startswith("your_"):
            raise ValueError("GROQ_API_KEY is not configured for Groq Whisper STT.")

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}"}

        data = {"model": "whisper-large-v3", "response_format": "text"}
        if keywords:
            data["prompt"] = ", ".join(keywords)

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "audio/mpeg")}
            response = httpx.post(url, headers=headers, data=data, files=files, timeout=300.0)

        if response.status_code != 200:
            raise RuntimeError(f"Groq Whisper transcription failed: {response.text}")

        return response.text.strip()

    def _transcribe_openai(self, path: Path, keywords: Optional[list[str]] = None) -> str:
        """Transcribe using OpenAI Whisper API."""
        if not self.openai_api_key or self.openai_api_key.startswith("your_"):
            raise ValueError("OPENAI_API_KEY is not configured for OpenAI Whisper STT.")

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}"}

        data = {"model": "whisper-1", "response_format": "text"}
        if keywords:
            data["prompt"] = ", ".join(keywords)

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "audio/mpeg")}
            response = httpx.post(url, headers=headers, data=data, files=files, timeout=300.0)

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI Whisper transcription failed: {response.text}")

        return response.text.strip()


def transcribe_audio(
    audio_path: Path | str,
    keywords: Optional[list[str]] = None,
    provider: Optional[str] = None,
) -> str:
    """Convenience helper to transcribe audio with auto-configured provider."""
    transcriber = AudioTranscriber(provider=provider)
    return transcriber.transcribe(audio_path, keywords=keywords)
