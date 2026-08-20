"""Tests for AudioTranscriber STT engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scribo.audio.transcriber import AudioTranscriber


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
        mock_response.text = "Hello students, today is lecture one."
        mock_client.models.generate_content.return_value = mock_response

        transcript = transcriber.transcribe(audio_file, keywords=["Fourier", "Nyquist"])

        assert transcript == "Hello students, today is lecture one."
        mock_client.files.upload.assert_called_once_with(file=str(audio_file))
        mock_client.files.delete.assert_called_once_with(name="files/test_audio")


def test_transcriber_groq_mocked(tmp_path: Path):
    audio_file = tmp_path / "lecture.mp3"
    audio_file.write_bytes(b"dummy audio")

    transcriber = AudioTranscriber(provider="groq", groq_api_key="fake_groq_key")

    with patch("scribo.audio.transcriber.httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "This is a transcript from Groq Whisper."
        mock_post.return_value = mock_response

        transcript = transcriber.transcribe(audio_file, keywords=["Kalman"])

        assert transcript == "This is a transcript from Groq Whisper."
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["data"]["prompt"] == "Kalman"
