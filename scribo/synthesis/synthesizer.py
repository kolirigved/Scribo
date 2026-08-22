"""LLM Note Synthesizer using Google Gemini API."""

import os
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from scribo.config import settings
from scribo.synthesis.prompts import (
    SYSTEM_ACADEMIC_NOTE_PROMPT,
    build_audio_synthesis_prompt,
    build_transcript_synthesis_prompt,
    build_transcription_prompt,
)


class NoteSynthesizer:
    """Synthesizes academic lecture notes from audio recordings or transcripts using Gemini."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.DEFAULT_MODEL
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        """Lazy-initialize GenAI client."""
        if self._client is None:
            if not self.api_key or self.api_key.startswith("your_"):
                raise ValueError(
                    "Gemini API key is not configured. Please set the GEMINI_API_KEY "
                    "environment variable or pass api_key to NoteSynthesizer."
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def synthesize_from_audio(
        self,
        audio_path: Path | str,
        lecture_title: Optional[str] = None,
        course_id: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate structured academic notes directly from an audio file.

        Args:
            audio_path: Path to the audio file (.mp3, .wav, .m4a, etc.).
            lecture_title: Optional title of the lecture.
            course_id: Optional course code/ID.
            keywords: Optional technical terminology hints.
            model: Optional model name override.
            temperature: Sampling temperature.

        Returns:
            str: Synthesized Markdown notes.
        """
        path = Path(audio_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        target_model = model or self.model
        prompt_text = build_audio_synthesis_prompt(
            lecture_title=lecture_title,
            course_id=course_id,
            keywords=keywords,
        )

        uploaded_file = None
        try:
            # Upload audio file to Gemini Files API
            uploaded_file = self.client.files.upload(file=str(path))

            response = self.client.models.generate_content(
                model=target_model,
                contents=[uploaded_file, prompt_text],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_ACADEMIC_NOTE_PROMPT,
                    temperature=temperature,
                ),
            )
            return response.text or ""
        finally:
            # Clean up remote file resource if uploaded
            if uploaded_file is not None and hasattr(uploaded_file, "name"):
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

    def synthesize_from_transcript(
        self,
        transcript: str,
        lecture_title: Optional[str] = None,
        course_id: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate structured academic notes from a text transcript.

        Args:
            transcript: Full raw text transcript of the lecture.
            lecture_title: Optional title of the lecture.
            course_id: Optional course code/ID.
            keywords: Optional technical terminology hints.
            model: Optional model name override.
            temperature: Sampling temperature.

        Returns:
            str: Synthesized Markdown notes.
        """
        target_model = model or self.model
        prompt_text = build_transcript_synthesis_prompt(
            transcript=transcript,
            lecture_title=lecture_title,
            course_id=course_id,
            keywords=keywords,
        )

        response = self.client.models.generate_content(
            model=target_model,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_ACADEMIC_NOTE_PROMPT,
                temperature=temperature,
            ),
        )
        return response.text or ""

    def transcribe_audio(
        self,
        audio_path: Path | str,
        keywords: Optional[list[str]] = None,
        model: Optional[str] = None,
    ) -> str:
        """Transcribe audio verbatim using Gemini.

        Args:
            audio_path: Path to the audio file.
            keywords: Optional terminology hints.
            model: Optional model name override.

        Returns:
            str: Verbatim transcription text.
        """
        path = Path(audio_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        target_model = model or self.model
        prompt_text = build_transcription_prompt(keywords=keywords)

        uploaded_file = None
        try:
            uploaded_file = self.client.files.upload(file=str(path))
            response = self.client.models.generate_content(
                model=target_model,
                contents=[uploaded_file, prompt_text],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                ),
            )
            return response.text or ""
        finally:
            if uploaded_file is not None and hasattr(uploaded_file, "name"):
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass
