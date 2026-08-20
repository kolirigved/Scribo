# Scribo 📜

**Scribo** is an academic knowledge engine and ingestion pipeline designed to process lecture recordings and slide decks into structured notes, indexing them for multi-lecture revision and grounded question answering.

## Features (Phase 1 MVP)

- **Audio Downsampling & Compression**: Converts multi-channel recordings (`.m4a`, `.wav`, `.mp3`) into single-channel mono MP3 at 32–48 kbps using `ffmpeg`/`pydub`.
- **Two-Stage Audio $\to$ Transcript $\to$ Notes Pipeline**:
  1. Extract verbatim transcripts using **Whisper** (Groq / OpenAI) or **Gemini STT** with technical keyword guidance.
  2. Synthesize structured academic notes from the extracted transcript using **Gemini** (`gemini-2.5-flash`).
- **Clean Academic Note Synthesis**: Eliminates conversational filler, structures topics hierarchically, and formats mathematical formulations cleanly.
- **Local Persistence & Future Frontend Ready**:
  - `data/courses/<course_id>/lecture_<id>.md` (Synthesized notes)
  - `data/courses/<course_id>/lecture_<id>_transcript.txt` (Verbatim transcript)
  - `data/courses/<course_id>/lecture_<id>_meta.json` (Structured metadata)

---

## Quickstart

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
```

### 2. Configure API Keys
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Add your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key

# Optional (for Whisper STT):
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
STT_PROVIDER=gemini # or "groq" / "openai"
```

### 3. Usage CLI

```bash
# Check system and API status
scribo info

# Run full two-stage pipeline (Audio -> Transcript -> Notes -> Storage)
scribo process \
  --course cs101 \
  --lecture lec01 \
  --audio /path/to/lecture.m4a \
  --title "Introduction to Digital Signal Processing" \
  --keywords "Nyquist, Sampling Theorem, FFT"

# Extract transcript only
scribo transcribe \
  --audio /path/to/lecture.m4a \
  --course cs101 \
  --lecture lec01 \
  --keywords "Fourier, Laplace"

# Synthesize notes from an existing transcript
scribo synthesize \
  --course cs101 \
  --lecture lec01 \
  --transcript /path/to/transcript.txt \
  --title "Introduction to Digital Signal Processing"

# List ingested lectures
scribo list --course cs101

# View synthesized notes or raw transcript in terminal
scribo view --course cs101 --lecture lec01
scribo view --course cs101 --lecture lec01 --transcript
```
