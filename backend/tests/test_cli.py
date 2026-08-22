"""Tests for Scribo CLI."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from scribo.cli import main
from scribo.config import settings
from scribo.pipeline.audio.transcriber import TranscriptResult, TranscriptSegment


def test_cli_info():
    runner = CliRunner()
    result = runner.invoke(main, ["info"])
    assert result.exit_code == 0
    assert "Scribo System Status" in result.output
    assert "FFmpeg" in result.output
    assert "STT Provider" in result.output


def test_cli_list_empty(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "COURSES_DATA_DIR", tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "No courses found" in result.output


def test_cli_compress(tmp_path: Path):
    import wave, struct, math
    wav_path = tmp_path / "test.wav"
    sample_rate = 16000
    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(sample_rate):
            val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            wf.writeframes(struct.pack("<h", val))

    out_mp3 = tmp_path / "out.mp3"
    runner = CliRunner()
    result = runner.invoke(main, ["compress", "-i", str(wav_path), "-o", str(out_mp3)])
    assert result.exit_code == 0
    assert out_mp3.exists()
    assert "Audio Compression Summary" in result.output


def test_cli_transcribe_cmd(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "COURSES_DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "dummy_key_val")

    audio_file = tmp_path / "lecture.mp3"
    audio_file.write_bytes(b"dummy audio")

    runner = CliRunner()
    with patch("scribo.cli.AudioTranscriber") as MockTranscriber:
        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = TranscriptResult(
            raw_text="Hello and welcome to the class.",
            formatted_text="[00:00] Hello and welcome to the class.",
            segments=[TranscriptSegment(id=0, start=0.0, end=5.0, text="Hello and welcome to the class.")],
            provider="groq",
        )
        MockTranscriber.return_value = mock_instance

        result = runner.invoke(
            main,
            ["transcribe", "-a", str(audio_file), "-c", "cs101", "-l", "lec01"],
        )
        assert result.exit_code == 0
        assert "Formatted transcript saved" in result.output


def test_cli_process_pipeline(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "COURSES_DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "dummy_key_val")

    audio_file = tmp_path / "lecture.mp3"
    audio_file.write_bytes(b"dummy audio")

    runner = CliRunner()
    with patch("scribo.cli.compress_audio") as mock_compress, \
         patch("scribo.cli.AudioTranscriber") as MockTranscriber, \
         patch("scribo.cli.NoteSynthesizer") as MockSynthesizer, \
         patch("scribo.cli.VectorStore") as MockVectorStore, \
         patch("scribo.cli.split_markdown_by_headers") as mock_split:

        from scribo.pipeline.audio.compressor import AudioMetadata
        dummy_meta = AudioMetadata(
            file_path=str(audio_file),
            format="mp3",
            size_bytes=1000,
            size_mb=0.01,
            duration_seconds=10.0,
            channels=1,
            sample_rate=16000,
        )
        mock_compress.return_value = (audio_file, dummy_meta, dummy_meta)

        trans_inst = MagicMock()
        trans_inst.transcribe.return_value = TranscriptResult(
            raw_text="Machine learning overview.",
            formatted_text="[00:00] Machine learning overview.",
            segments=[TranscriptSegment(id=0, start=0.0, end=5.0, text="Machine learning overview.")],
            provider="groq",
        )
        MockTranscriber.return_value = trans_inst

        synth_inst = MagicMock()
        synth_inst.synthesize_from_transcript.return_value = "# ML Notes\n## Overview\nNotes."
        MockSynthesizer.return_value = synth_inst

        result = runner.invoke(
            main,
            [
                "process",
                "-c", "cs229",
                "-l", "lec01",
                "-a", str(audio_file),
                "--title", "Machine Learning 101",
            ],
        )

        assert result.exit_code == 0
        assert "Ingestion pipeline successfully completed" in result.output

    # Test viewing notes and transcript
    view_notes = runner.invoke(main, ["view", "-c", "cs229", "-l", "lec01"])
    assert view_notes.exit_code == 0
    assert "ML Notes" in view_notes.output

    view_trans = runner.invoke(main, ["view", "-c", "cs229", "-l", "lec01", "--transcript"])
    assert view_trans.exit_code == 0
    assert "Machine learning overview" in view_trans.output
