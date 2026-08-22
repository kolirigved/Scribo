"""Tests for NoteSynthesizer with mocked Gemini API."""

from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from scribo.pipeline.synthesis.synthesizer import NoteSynthesizer


def test_synthesizer_missing_key():
    synthesizer = NoteSynthesizer(api_key="")
    with pytest.raises(ValueError, match="Gemini API key is not configured"):
        _ = synthesizer.client


def test_synthesize_from_transcript_mocked():
    synthesizer = NoteSynthesizer(api_key="fake_test_key_123")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "# Lecture 1: Test\n\n## Summary\nContent."
    mock_client.models.generate_content.return_value = mock_response

    synthesizer._client = mock_client

    result = synthesizer.synthesize_from_transcript(
        transcript="This is a test transcript.",
        lecture_title="Test Title",
        course_id="CS101",
    )

    assert result == "# Lecture 1: Test\n\n## Summary\nContent."
    mock_client.models.generate_content.assert_called_once()


def test_synthesize_from_audio_mocked(tmp_path: Path):
    audio_file = tmp_path / "lecture.mp3"
    audio_file.write_bytes(b"dummy audio data")

    synthesizer = NoteSynthesizer(api_key="fake_test_key_123")

    mock_client = MagicMock()
    mock_file_ref = MagicMock()
    mock_file_ref.name = "files/test123"
    mock_client.files.upload.return_value = mock_file_ref

    mock_response = MagicMock()
    mock_response.text = "# Audio Generated Notes"
    mock_client.models.generate_content.return_value = mock_response

    synthesizer._client = mock_client

    result = synthesizer.synthesize_from_audio(
        audio_path=audio_file,
        lecture_title="Audio Lecture",
        course_id="CS101",
    )

    assert result == "# Audio Generated Notes"
    mock_client.files.upload.assert_called_once_with(file=str(audio_file))
    mock_client.files.delete.assert_called_once_with(name="files/test123")


def test_transcribe_audio_mocked(tmp_path: Path):
    audio_file = tmp_path / "speech.mp3"
    audio_file.write_bytes(b"dummy audio data")

    synthesizer = NoteSynthesizer(api_key="fake_test_key_123")

    mock_client = MagicMock()
    mock_file_ref = MagicMock()
    mock_file_ref.name = "files/speech123"
    mock_client.files.upload.return_value = mock_file_ref

    mock_response = MagicMock()
    mock_response.text = "Verbatim transcription output"
    mock_client.models.generate_content.return_value = mock_response

    synthesizer._client = mock_client

    result = synthesizer.transcribe_audio(audio_path=audio_file)
    assert result == "Verbatim transcription output"
    mock_client.files.delete.assert_called_once_with(name="files/speech123")
