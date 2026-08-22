"""Tests for AudioTranscriber STT engine with timestamps."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scribo.audio.transcriber import (
    AudioTranscriber,
    TranscriptResult,
    TranscriptSegment,
    format_seconds_to_timestamp,
    group_segments_into_paragraphs,
)


def test_format_seconds_to_timestamp():
    assert format_seconds_to_timestamp(45.2) == "00:45"
    assert format_seconds_to_timestamp(125.0) == "02:05"
    assert format_seconds_to_timestamp(3665.0) == "01:01:05"


def test_group_segments_into_paragraphs():
    segments = [
        TranscriptSegment(id=0, start=0.0, end=10.0, text="Hello students."),
        TranscriptSegment(id=1, start=10.5, end=25.0, text="Today we discuss syntax."),
        TranscriptSegment(id=2, start=35.0, end=50.0, text="Now let's examine verbs."),
    ]
    formatted = group_segments_into_paragraphs(segments, group_interval_seconds=30.0)
    assert "[00:00]" in formatted
    assert "[00:35]" in formatted
    assert "Hello students. Today we discuss syntax." in formatted
    assert "Now let's examine verbs." in formatted


def test_transcriber_unsupported_provider(tmp_path: Path):
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"dummy audio")

    transcriber = AudioTranscriber(provider="invalid_provider")
    with pytest.raises(ValueError, match="Unsupported STT provider"):
        transcriber.transcribe(audio_file)


def test_transcriber_missing_file():
    transcriber = AudioTranscriber(provider="gemini")
    with pytest.raises(FileNotFoundError):
        transcriber.transcribe("non_existent_path.mp3")


def test_transcriber_gemini_mocked(tmp_path: Path):
    audio_file = tmp_path / "lecture.mp3"
    audio_file.write_bytes(b"dummy audio")

    transcriber = AudioTranscriber(provider="gemini", gemini_api_key="fake_key")

    with patch("scribo.audio.transcriber.genai.Client") as MockGenaiClient:
        mock_client = MagicMock()
        MockGenaiClient.return_value = mock_client

        mock_file_ref = MagicMock()
        mock_file_ref.name = "files/test_audio"
        mock_client.files.upload.return_value = mock_file_ref

        mock_response = MagicMock()
        mock_response.text = "[00:00] Hello students, today is lecture one."
        mock_client.models.generate_content.return_value = mock_response

        res = transcriber.transcribe(audio_file, keywords=["Fourier", "Nyquist"])

        assert isinstance(res, TranscriptResult)
        assert "[00:00]" in res.formatted_text
        mock_client.files.upload.assert_called_once_with(file=str(audio_file))
        mock_client.files.delete.assert_called_once_with(name="files/test_audio")


def test_transcriber_groq_mocked(tmp_path: Path):
    audio_file = tmp_path / "lecture.mp3"
    audio_file.write_bytes(b"dummy audio")

    transcriber = AudioTranscriber(provider="groq", groq_api_key="fake_groq_key")

    with patch("scribo.audio.transcriber.httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "This is a transcript from Groq Whisper.",
            "language": "english",
            "duration": 15.0,
            "segments": [
                {"id": 0, "start": 0.0, "end": 5.0, "text": "This is a transcript"},
                {"id": 1, "start": 5.1, "end": 15.0, "text": "from Groq Whisper."},
            ],
        }
        mock_post.return_value = mock_response

        res = transcriber.transcribe(audio_file, keywords=["Kalman"])

        assert isinstance(res, TranscriptResult)
        assert res.raw_text == "This is a transcript from Groq Whisper."
        assert len(res.segments) == 2
        assert "[00:00]" in res.formatted_text
