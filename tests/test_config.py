"""Tests for configuration."""

from scribo.config import settings


def test_settings_initialization():
    assert settings.COURSES_DATA_DIR.exists()
    assert settings.TEMP_STORAGE_DIR.exists()
    assert isinstance(settings.AUDIO_BITRATE, str)
    assert settings.AUDIO_SAMPLE_RATE > 0


def test_validate_gemini_key():
    assert isinstance(settings.validate_gemini_key(), bool)
