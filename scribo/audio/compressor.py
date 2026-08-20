"""Audio preprocessing, conversion, and downsampling module.

Converts multi-channel lecture recordings into single-channel mono MP3 at 32-48 kbps
to ensure 50-minute lectures stay well below upload limits while retaining spoken clarity.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from pydub import AudioSegment

from scribo.config import settings


class AudioMetadata(BaseModel):
    """Audio file details and metrics."""
    file_path: str
    format: str
    size_bytes: int
    size_mb: float
    duration_seconds: float
    channels: int
    sample_rate: int
    bitrate: Optional[str] = None


def check_ffmpeg() -> bool:
    """Verify if ffmpeg is accessible on system PATH."""
    return shutil.which("ffmpeg") is not None


def get_audio_metadata(file_path: Path | str) -> AudioMetadata:
    """Extract metadata and metrics from an audio file."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    size_bytes = path.stat().st_size
    size_mb = round(size_bytes / (1024 * 1024), 2)
    ext = path.suffix.lower().lstrip(".")

    try:
        audio = AudioSegment.from_file(str(path))
        duration_sec = round(len(audio) / 1000.0, 2)
        channels = audio.channels
        sample_rate = audio.frame_rate
    except Exception as e:
        # Fallback to estimation or generic info if pydub header read fails
        duration_sec = 0.0
        channels = 1
        sample_rate = settings.AUDIO_SAMPLE_RATE

    return AudioMetadata(
        file_path=str(path),
        format=ext,
        size_bytes=size_bytes,
        size_mb=size_mb,
        duration_seconds=duration_sec,
        channels=channels,
        sample_rate=sample_rate,
    )


def compress_audio(
    input_path: Path | str,
    output_path: Optional[Path | str] = None,
    bitrate: str = settings.AUDIO_BITRATE,
    sample_rate: int = settings.AUDIO_SAMPLE_RATE,
    channels: int = settings.AUDIO_CHANNELS,
) -> tuple[Path, AudioMetadata, AudioMetadata]:
    """Compress and downsample audio to mono MP3 at target bitrate.

    Args:
        input_path: Path to the input audio file (.m4a, .wav, .mp3, etc.)
        output_path: Optional destination path. If not provided, a file in temp directory is used.
        bitrate: Target bitrate (e.g. '32k', '48k').
        sample_rate: Target sample rate (e.g. 16000).
        channels: Target channel count (1 for mono).

    Returns:
        tuple[Path, AudioMetadata, AudioMetadata]: (compressed_path, original_meta, compressed_meta)
    """
    in_path = Path(input_path).resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {in_path}")

    original_meta = get_audio_metadata(in_path)

    if output_path is None:
        out_filename = f"{in_path.stem}_compressed_{bitrate}.mp3"
        out_path = settings.TEMP_STORAGE_DIR / out_filename
    else:
        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use ffmpeg directly if available for optimal speed and reliability, fallback to pydub
    if check_ffmpeg():
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", str(in_path),
            "-ac", str(channels),
            "-ar", str(sample_rate),
            "-b:a", bitrate,
            "-vn",  # Discard any video tracks if present in m4a/mp4
            str(out_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg compression failed: {result.stderr}")
    else:
        audio = AudioSegment.from_file(str(in_path))
        if channels == 1:
            audio = audio.set_channels(1)
        audio = audio.set_frame_rate(sample_rate)
        audio.export(str(out_path), format="mp3", bitrate=bitrate)

    compressed_meta = get_audio_metadata(out_path)
    compressed_meta.bitrate = bitrate

    return out_path, original_meta, compressed_meta
