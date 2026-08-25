"""Command-Line Interface for Scribo."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from scribo import __version__
from scribo.config import settings
from scribo.pipeline.audio.compressor import compress_audio, get_audio_metadata, check_ffmpeg
from scribo.pipeline.audio.transcriber import AudioTranscriber
from scribo.pipeline.synthesis.synthesizer import NoteSynthesizer
from scribo.storage.local_store import (
    save_lecture,
    save_transcript_only,
    load_lecture_notes,
    load_lecture_transcript,
    save_slides_text,
    list_courses,
    list_lectures,
)
from scribo.pipeline.slides.extractor import extract_pdf_text
from scribo.rag.chunker import split_markdown_by_headers
from scribo.rag.vector_store import VectorStore
from scribo.rag.query_engine import QueryEngine

console = Console()


@click.group()
@click.version_option(__version__, prog_name="Scribo")
def main():
    """Scribo: Academic knowledge engine and lecture ingestion pipeline."""
    pass


@main.command(name="info")
def info():
    """Display system configuration, API status, and environment."""
    table = Table(title="📜 Scribo System Status", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="bold")
    table.add_column("Status / Value", style="green")

    table.add_row("Scribo Version", __version__)
    table.add_row("Python Interpreter", sys.version.split()[0])
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    table.add_row(
        "FFmpeg Available",
        "[green]Yes[/green]" if ffmpeg_ok else "[yellow]No (Using pydub fallback)[/yellow]"
    )

    # Check API Keys
    has_gemini = settings.validate_gemini_key()
    has_groq = settings.validate_groq_key()
    has_openai = settings.validate_openai_key()

    table.add_row(
        "Gemini API Key",
        "[green]Configured[/green]" if has_gemini else "[red]Not Configured (GEMINI_API_KEY in .env)[/red]"
    )
    table.add_row(
        "Groq API Key (Whisper)",
        "[green]Configured[/green]" if has_groq else "[dim]Not Configured (Optional GROQ_API_KEY)[/dim]"
    )
    table.add_row(
        "OpenAI API Key (Whisper)",
        "[green]Configured[/green]" if has_openai else "[dim]Not Configured (Optional OPENAI_API_KEY)[/dim]"
    )

    available_stt = settings.get_available_stt_providers()
    table.add_row("Active STT Provider", f"[cyan]{settings.DEFAULT_STT_PROVIDER}[/cyan]")
    table.add_row("Available STT Engines", ", ".join(available_stt) if available_stt else "[red]None[/red]")
    table.add_row("Default Synthesis Model", settings.DEFAULT_MODEL)
    table.add_row("Target Bitrate", settings.AUDIO_BITRATE)
    table.add_row("Courses Storage", str(settings.COURSES_DATA_DIR))

    console.print(table)


@main.command(name="compress")
@click.option("--input", "-i", "input_path", required=True, type=click.Path(exists=True), help="Input audio file.")
@click.option("--output", "-o", "output_path", type=click.Path(), default=None, help="Output compressed MP3 file.")
@click.option("--bitrate", "-b", default=settings.AUDIO_BITRATE, help="Target bitrate (e.g. 32k, 48k).")
def compress_cmd(input_path: str, output_path: Optional[str], bitrate: str):
    """Compress and downsample an audio file to mono MP3."""
    with console.status("[bold blue]Compressing audio file...", spinner="dots"):
        try:
            out_file, orig_meta, comp_meta = compress_audio(
                input_path=input_path,
                output_path=output_path,
                bitrate=bitrate,
            )
        except Exception as e:
            console.print(f"[bold red]Compression error:[/bold red] {e}")
            sys.exit(1)

    table = Table(title="Audio Compression Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Original", style="yellow")
    table.add_column("Compressed", style="green")

    table.add_row("File Size", f"{orig_meta.size_mb} MB", f"{comp_meta.size_mb} MB")
    table.add_row("Channels", str(orig_meta.channels), str(comp_meta.channels))
    table.add_row("Sample Rate", f"{orig_meta.sample_rate} Hz", f"{comp_meta.sample_rate} Hz")
    table.add_row("Duration", f"{orig_meta.duration_seconds}s", f"{comp_meta.duration_seconds}s")
    table.add_row("Bitrate", orig_meta.bitrate or "Original", bitrate)

    console.print(table)
    console.print(f"[bold green]Saved compressed audio to:[/bold green] {out_file}")


@main.command(name="transcribe")
@click.option("--audio", "-a", required=True, type=click.Path(exists=True), help="Path to audio file.")
@click.option("--output", "-o", default=None, help="Output transcript text file path.")
@click.option("--keywords", "-k", default="", help="Comma-separated technical keywords.")
@click.option("--provider", "-p", default=None, type=click.Choice(["gemini", "groq", "openai"], case_sensitive=False), help="STT provider.")
@click.option("--course", "-c", default=None, help="Optional course ID to persist transcript.")
@click.option("--lecture", "-l", default=None, help="Optional lecture ID to persist transcript.")
def transcribe_cmd(
    audio: str,
    output: Optional[str],
    keywords: str,
    provider: Optional[str],
    course: Optional[str],
    lecture: Optional[str],
):
    """Transcribe audio with segment timestamps using Whisper (Groq/OpenAI) or Gemini STT."""
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    stt_provider = provider or settings.DEFAULT_STT_PROVIDER

    with console.status(f"[bold blue]Transcribing audio using {stt_provider.upper()} STT...", spinner="dots"):
        transcriber = AudioTranscriber(provider=stt_provider)
        try:
            transcript_res = transcriber.transcribe(audio_path=audio, keywords=kw_list)
        except Exception as e:
            console.print(f"[bold red]Transcription failed:[/bold red] {e}")
            sys.exit(1)

    if course and lecture:
        segments_dict = [s.model_dump() for s in transcript_res.segments]
        saved_txt, saved_json = save_transcript_only(
            course_id=course,
            lecture_id=lecture,
            transcript_content=transcript_res.formatted_text,
            transcript_segments=segments_dict,
            stt_provider=stt_provider,
            keywords=kw_list,
        )
        console.print(f"[bold green]Formatted transcript saved:[/bold green] {saved_txt}")
        if saved_json:
            console.print(f"[bold green]Segment JSON saved:[/bold green] {saved_json}")
    elif output:
        out_p = Path(output)
        out_p.write_text(transcript_res.formatted_text, encoding="utf-8")
        console.print(f"[bold green]Saved transcript to:[/bold green] {out_p}")
    else:
        console.print(Panel(transcript_res.formatted_text, title="Timestamped Transcript Output"))


@main.command(name="process")
@click.option("--course", "-c", required=True, help="Course identifier (e.g. cs101).")
@click.option("--lecture", "-l", required=True, help="Lecture identifier (e.g. lec01).")
@click.option("--audio", "-a", required=True, type=click.Path(exists=True), help="Path to lecture audio recording.")
@click.option("--title", "-t", default=None, help="Lecture title.")
@click.option("--keywords", "-k", default="", help="Comma-separated technical keywords/jargon hints.")
@click.option("--provider", "-p", default=None, type=click.Choice(["gemini", "groq", "openai"], case_sensitive=False), help="STT provider.")
@click.option("--model", "-m", default=None, help="Gemini model override for synthesis.")
@click.option("--compress/--no-compress", default=True, help="Whether to compress audio before STT.")
@click.option("--bitrate", "-b", default=settings.AUDIO_BITRATE, help="Audio compression bitrate.")
def process_cmd(
    course: str,
    lecture: str,
    audio: str,
    title: Optional[str],
    keywords: str,
    provider: Optional[str],
    model: Optional[str],
    compress: bool,
    bitrate: str,
):
    """Full Audio Ingestion Pipeline: Compress -> Timestamped Transcript -> Synthesize Notes -> Persist."""
    if not settings.validate_gemini_key():
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY is not configured. Please set it in your .env file.")
        sys.exit(1)

    lecture_title = title or f"Lecture {lecture.upper()}"
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    stt_provider = provider or settings.DEFAULT_STT_PROVIDER
    target_audio_path = Path(audio)
    audio_stats = None

    # Step 1: Compress Audio
    if compress:
        with console.status("[bold blue]Step 1/3: Compressing & downsampling audio...", spinner="dots"):
            try:
                target_audio_path, orig_meta, comp_meta = compress_audio(
                    input_path=audio,
                    bitrate=bitrate,
                )
                audio_stats = {
                    "original_path": orig_meta.file_path,
                    "original_size_mb": orig_meta.size_mb,
                    "compressed_path": str(target_audio_path),
                    "compressed_size_mb": comp_meta.size_mb,
                    "duration_seconds": comp_meta.duration_seconds,
                    "bitrate": bitrate,
                }
                console.print(
                    f"[green]Audio compressed:[/green] {orig_meta.size_mb} MB -> "
                    f"[bold green]{comp_meta.size_mb} MB[/bold green]"
                )
            except Exception as e:
                console.print(f"[bold red]Audio compression error:[/bold red] {e}")
                sys.exit(1)

    # Step 2: Extract Timestamped Transcript via STT
    with console.status(f"[bold blue]Step 2/3: Extracting timestamped transcript using {stt_provider.upper()} STT...", spinner="dots"):
        transcriber = AudioTranscriber(provider=stt_provider)
        try:
            transcript_res = transcriber.transcribe(
                audio_path=target_audio_path,
                keywords=kw_list,
            )
            console.print(
                f"[green]Transcript extracted:[/green] {len(transcript_res.raw_text.split())} words, "
                f"{len(transcript_res.segments)} timestamped segments"
            )
        except Exception as e:
            console.print(f"[bold red]Transcription error:[/bold red] {e}")
            sys.exit(1)

    # Step 3: Synthesize Structured Notes from Transcript
    with console.status(f"[bold blue]Step 3/3: Synthesizing notes with {model or settings.DEFAULT_MODEL}...", spinner="dots"):
        synthesizer = NoteSynthesizer(model=model)
        try:
            notes_content = synthesizer.synthesize_from_transcript(
                transcript=transcript_res.formatted_text,
                lecture_title=lecture_title,
                course_id=course,
                keywords=kw_list,
                model=model,
            )
        except Exception as e:
            console.print(f"[bold red]Note synthesis error:[/bold red] {e}")
            sys.exit(1)

    # Step 4: Persist Notes, Formatted Transcript, Segment JSON, and Metadata
    segments_dict = [s.model_dump() for s in transcript_res.segments]
    notes_path, transcript_path, meta_path, meta = save_lecture(
        course_id=course,
        lecture_id=lecture,
        title=lecture_title,
        notes_content=notes_content,
        transcript_content=transcript_res.formatted_text,
        transcript_segments=segments_dict,
        audio_meta=audio_stats,
        keywords=kw_list,
        synthesis_model=model or settings.DEFAULT_MODEL,
        stt_provider=stt_provider,
    )

    console.print(Panel(
        f"[bold green]Ingestion pipeline successfully completed![/bold green]\n\n"
        f"• [bold]Course:[/bold] {course}\n"
        f"• [bold]Lecture ID:[/bold] {lecture}\n"
        f"• [bold]Title:[/bold] {lecture_title}\n"
        f"• [bold]Transcript Text:[/bold] {transcript_path}\n"
        f"• [bold]Transcript JSON:[/bold] {meta.transcript_json_file}\n"
        f"• [bold]Notes File:[/bold] {notes_path}\n"
        f"• [bold]Metadata File:[/bold] {meta_path}",
        title="✨ Ingestion Complete",
        border_style="green",
    ))

    # Step 5: Index into ChromaDB
    with console.status("[bold blue]Step 5: Indexing chunks into ChromaDB...", spinner="dots"):
        try:
            chunks = split_markdown_by_headers(notes_content, course, lecture)
            vs = VectorStore()
            vs.add_chunks(chunks)
            console.print(f"[green]Indexed {len(chunks)} chunks into vector store.[/green]")
        except Exception as e:
            console.print(f"[bold red]Indexing error:[/bold red] {e}")


@main.command(name="slides")
@click.option("--course", "-c", required=True, help="Course identifier (e.g. cs101).")
@click.option("--lecture", "-l", required=True, help="Lecture identifier (e.g. lec01).")
@click.option("--pdf", "-p", required=True, type=click.Path(exists=True), help="Path to lecture slide deck (PDF).")
def slides_cmd(course: str, lecture: str, pdf: str):
    """Extract and persist text from a lecture slide deck (PDF)."""
    with console.status("[bold blue]Extracting slide text...", spinner="dots"):
        try:
            slides_text = extract_pdf_text(pdf)
            console.print(f"[green]Extracted {len(slides_text.split())} words from {pdf}.[/green]")
        except Exception as e:
            console.print(f"[bold red]Extraction error:[/bold red] {e}")
            sys.exit(1)
            
    try:
        slides_path = save_slides_text(course_id=course, lecture_id=lecture, text=slides_text)
        console.print(f"[bold green]Saved slide text to:[/bold green] {slides_path}")
    except Exception as e:
        console.print(f"[bold red]Storage error:[/bold red] {e}")
        sys.exit(1)


@main.command(name="process-audio")
@click.option("--course", "-c", required=True, help="Course identifier (e.g. cs101).")
@click.option("--lecture", "-l", required=True, help="Lecture identifier (e.g. lec01).")
@click.option("--audio", "-a", required=True, type=click.Path(exists=True), help="Path to lecture audio recording.")
@click.option("--title", "-t", default=None, help="Lecture title.")
@click.option("--keywords", "-k", default="", help="Comma-separated technical keywords/jargon hints.")
@click.option("--provider", "-p", default=None, type=click.Choice(["gemini", "groq", "openai"], case_sensitive=False), help="STT provider.")
@click.option("--model", "-m", default=None, help="Gemini model override.")
@click.option("--compress/--no-compress", default=True, help="Whether to compress audio before sending.")
@click.option("--bitrate", "-b", default=settings.AUDIO_BITRATE, help="Audio compression bitrate.")
@click.pass_context
def process_audio_alias(ctx, **kwargs):
    """Alias for process command."""
    ctx.forward(process_cmd)


@main.command(name="synthesize")
@click.option("--course", "-c", required=True, help="Course identifier.")
@click.option("--lecture", "-l", required=True, help="Lecture identifier.")
@click.option("--transcript", "-t", required=True, type=click.Path(exists=True), help="Path to transcript text file.")
@click.option("--title", default=None, help="Lecture title.")
@click.option("--keywords", "-k", default="", help="Comma-separated technical keywords.")
@click.option("--model", "-m", default=None, help="Gemini model override.")
def synthesize_cmd(
    course: str,
    lecture: str,
    transcript: str,
    title: Optional[str],
    keywords: str,
    model: Optional[str],
):
    """Synthesize structured notes from a text transcript file."""
    if not settings.validate_gemini_key():
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY is not configured.")
        sys.exit(1)

    transcript_text = Path(transcript).read_text(encoding="utf-8")
    lecture_title = title or f"Lecture {lecture.upper()}"
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]

    with console.status("[bold blue]Synthesizing academic notes from transcript...", spinner="dots"):
        synthesizer = NoteSynthesizer(model=model)
        try:
            notes_content = synthesizer.synthesize_from_transcript(
                transcript=transcript_text,
                lecture_title=lecture_title,
                course_id=course,
                keywords=kw_list,
                model=model,
            )
        except Exception as e:
            console.print(f"[bold red]Synthesis failed:[/bold red] {e}")
            sys.exit(1)

    notes_path, transcript_path, meta_path, _ = save_lecture(
        course_id=course,
        lecture_id=lecture,
        title=lecture_title,
        notes_content=notes_content,
        transcript_content=transcript_text,
        keywords=kw_list,
        synthesis_model=model or settings.DEFAULT_MODEL,
    )

    console.print(f"[bold green]Synthesized notes saved to:[/bold green] {notes_path}")


@main.command(name="list")
@click.option("--course", "-c", default=None, help="Filter by course ID.")
def list_cmd(course: Optional[str]):
    """List stored courses and lecture notes."""
    courses = [course] if course else list_courses()
    if not courses:
        console.print("[yellow]No courses found in local storage.[/yellow]")
        return

    for c in courses:
        lectures = list_lectures(c)
        table = Table(title=f"📚 Course: {c.upper()}", show_header=True)
        table.add_column("Lecture ID", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Transcript", style="magenta")
        table.add_column("Created", style="dim")
        table.add_column("Model", style="green")

        if not lectures:
            table.add_row("-", "No lectures ingested yet", "-", "-", "-")
        else:
            for lec in lectures:
                has_transcript = "✓" if lec.transcript_file and Path(lec.transcript_file).exists() else "✗"
                table.add_row(
                    lec.lecture_id,
                    lec.lecture_title,
                    has_transcript,
                    lec.created_at[:19].replace("T", " "),
                    lec.synthesis_model or "-",
                )

        console.print(table)
        console.print()


@main.command(name="view")
@click.option("--course", "-c", required=True, help="Course identifier.")
@click.option("--lecture", "-l", required=True, help="Lecture identifier.")
@click.option("--transcript", is_flag=True, default=False, help="View formatted transcript instead of notes.")
def view_cmd(course: str, lecture: str, transcript: bool):
    """View synthesized lecture notes or formatted timestamped transcript."""
    try:
        if transcript:
            content = load_lecture_transcript(course, lecture)
            console.print(Panel(content, title=f"Transcript: {course.upper()} - {lecture}"))
        else:
            content = load_lecture_notes(course, lecture)
            console.print(Markdown(content))
    except Exception as e:
        console.print(f"[bold red]Error loading content:[/bold red] {e}")
        sys.exit(1)


@main.command(name="ask")
@click.argument("question")
@click.option("--course", "-c", default=None, help="Optional course identifier to filter search.")
def ask_cmd(question: str, course: Optional[str]):
    """Query the knowledge base using grounded RAG."""
    with console.status("[bold blue]Querying vector base and synthesizing answer...", spinner="dots"):
        try:
            engine = QueryEngine()
            result = engine.query(question, course_id=course)
        except Exception as e:
            console.print(f"[bold red]Query failed:[/bold red] {e}")
            sys.exit(1)

    console.print(Panel(
        Markdown(result["answer"]),
        title="🤖 Scribo RAG Response",
        border_style="blue"
    ))
    
    if result["citations"]:
        console.print("\n[bold dim]Retrieved Citations:[/bold dim]")
        for cite in result["citations"]:
            meta = cite["metadata"]
            ts = f" @ {meta.get('timestamp', '')}" if meta.get("timestamp") else ""
            console.print(f"• [dim]{meta['course_id'].upper()} - {meta['lecture_id']}{ts}: {meta['header']}[/dim]")

@main.command(name="index")
@click.option("--course", "-c", default=None, help="Course identifier (e.g. eng448). If omitted, indexes all courses.")
@click.option("--lecture", "-l", default=None, help="Lecture identifier (e.g. lec01). If omitted, indexes all lectures in the course.")
def index_cmd(course: Optional[str], lecture: Optional[str]):
    """Manually index lecture notes into the ChromaDB vector store."""
    if not settings.validate_gemini_key():
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY is not configured.")
        sys.exit(1)

    vs = VectorStore()
    courses_to_index = [course.lower()] if course else [c for c in list_courses()]

    if not courses_to_index:
        console.print("[yellow]No courses found to index.[/yellow]")
        return

    total_chunks = 0
    total_lectures = 0

    for c in courses_to_index:
        course_dir = settings.COURSES_DATA_DIR / c
        if not course_dir.exists():
            console.print(f"[yellow]Course directory not found:[/yellow] {course_dir}")
            continue

        if lecture:
            md_files = [course_dir / f"lecture_{lecture.lower()}.md"]
        else:
            md_files = list(course_dir.glob("lecture_*.md"))

        for md_file in md_files:
            if not md_file.exists():
                console.print(f"[yellow]Lecture file not found:[/yellow] {md_file.name}")
                continue

            lec_id = md_file.stem.replace("lecture_", "")
            with console.status(f"[bold blue]Indexing {c.upper()} - {lec_id}...", spinner="dots"):
                try:
                    text = md_file.read_text(encoding="utf-8")
                    chunks = split_markdown_by_headers(text, c, lec_id)
                    
                    # Also try to index slides if they exist
                    slides_file = course_dir / f"lecture_{lec_id}_slides.txt"
                    if slides_file.exists():
                        slides_text = slides_file.read_text(encoding="utf-8")
                        try:
                            from scribo.rag.chunker import split_slides_by_page
                            slides_chunks = split_slides_by_page(slides_text, c, lec_id)
                            chunks.extend(slides_chunks)
                        except ImportError:
                            pass
                            
                    if chunks:
                        vs.add_chunks(chunks)
                        total_chunks += len(chunks)
                        total_lectures += 1
                        console.print(f"[green]✓ Indexed {len(chunks)} chunks from {c.upper()} - {lec_id}[/green]")
                    else:
                        console.print(f"[yellow]No content chunks found in {md_file.name}[/yellow]")
                except Exception as e:
                    console.print(f"[bold red]Failed to index {md_file.name}:[/bold red] {e}")

    console.print(Panel(
        f"Indexed [bold green]{total_chunks}[/bold green] chunks across [bold green]{total_lectures}[/bold green] lecture(s).",
        title="📚 Indexing Complete",
        border_style="green"
    ))
if __name__ == "__main__":
    main()
