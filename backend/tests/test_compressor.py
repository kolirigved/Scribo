"""Tests for audio preprocessing and compression."""

import math
import struct
import wave
from pathlib import Path
import pytest

from scribo.pipeline.audio.compressor import (
    compress_audio,
    get_audio_metadata,
    check_ffmpeg,
    AudioMetadata,
)


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    """Generate a clean 1-second sine wave stereo WAV file."""
    wav_path = tmp_path / "test_lecture.wav"
    sample_rate = 44100
    duration_sec = 1.0
    num_samples = int(sample_rate * duration_sec)

    with wave.open(str(wav_path), "w") as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # 440 Hz tone
        for i in range(num_samples):
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            data = struct.pack("<hh", value, value)
            wav_file.writeframes(data)

    return wav_path


def test_get_audio_metadata(sample_wav: Path):
    meta = get_audio_metadata(sample_wav)
    assert isinstance(meta, AudioMetadata)
    assert meta.format == "wav"
    assert meta.channels == 2
    assert meta.sample_rate == 44100
    assert meta.duration_seconds >= 0.9


def test_compress_audio(sample_wav: Path, tmp_path: Path):
    out_path = tmp_path / "compressed_output.mp3"
    result_path, orig_meta, comp_meta = compress_audio(
        input_path=sample_wav,
        output_path=out_path,
        bitrate="32k",
        sample_rate=16000,
        channels=1,
    )

    assert result_path.exists()
    assert result_path == out_path
    assert comp_meta.format == "mp3"
    assert comp_meta.channels == 1
    assert comp_meta.sample_rate == 16000
    assert comp_meta.bitrate == "32k"
    assert comp_meta.size_bytes > 0


def test_compress_audio_nonexistent():
    with pytest.raises(FileNotFoundError):
        compress_audio("non_existent_audio_file.wav")


def test_check_ffmpeg():
    assert isinstance(check_ffmpeg(), bool)
