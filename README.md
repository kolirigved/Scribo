# Scribo 📜

**Scribo** is an academic knowledge engine and ingestion pipeline designed to process lecture recordings and slide decks into structured notes, indexing them for multi-lecture revision and grounded question answering.

The repository is structured as a **Monorepo**:
- **`backend/`**: Contains the core audio/synthesis pipeline (CLI) and a FastAPI server for data retrieval.
- **`frontend/`**: Contains a Next.js (React) web UI with Markdown & LaTeX rendering.

## Features (Phase 1 & 2)

- **Audio Downsampling & Compression**: Converts multi-channel recordings (`.m4a`, `.wav`, `.mp3`) into single-channel mono MP3 at 32–48 kbps using `ffmpeg`/`pydub`.
- **Two-Stage Audio $\to$ Transcript $\to$ Notes Pipeline**:
  1. Extract verbatim transcripts with strict `[MM:SS]` timestamps using **Whisper** (Groq / OpenAI) or **Gemini STT**.
  2. Synthesize structured academic notes from the extracted transcript using **Gemini**.
- **Interactive UI & LaTeX Rendering**: Beautifully formats mathematical formulations, with timestamped segments ready for audio seeking in the Next.js frontend.
- **Local Data Persistence**:
  - `backend/data/courses/<course_id>/lecture_<id>.md` (Synthesized notes)
  - `backend/data/courses/<course_id>/lecture_<id>_transcript.txt` (Verbatim transcript)
  - `backend/data/courses/<course_id>/lecture_<id>_transcript.json` (Structured segments for UI player)

---

## 🚀 Quickstart

### 1. Setup Python Backend & CLI
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -e backend/ --no-deps
```

Configure backend API keys:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env` to include your `GEMINI_API_KEY` (and optionally Groq/OpenAI for Whisper).

### 2. Setup Next.js Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
cd ..
```

---

## 💻 Running the Web App

You need to run both the FastAPI server and the Next.js frontend to use the web viewer.

**Terminal 1: Backend API**
```bash
cd backend
../.venv/bin/uvicorn api.main:app --reload --port 8000
```

**Terminal 2: Frontend Web UI**
```bash
cd frontend
npm run dev
```
Open **http://localhost:3000** in your browser!

---

## 🛠️ Usage (Command Line Interface)

The Scribo CLI is used for headless background processing of lecture audio. Ensure your `.venv` is activated.

```bash
# Run full pipeline (Audio -> Transcript -> Notes -> Storage)
scribo process \
  --course eng448 \
  --lecture lec01 \
  --audio "/path/to/lecture.m4a" \
  --title "Introduction to Dravidian Languages"

# Extract transcript only
scribo transcribe --course cs101 --lecture lec01 --audio /path/to/lecture.m4a

# Synthesize notes from an existing transcript
scribo synthesize --course cs101 --lecture lec01 --transcript /path/to/transcript.txt --title "Lecture 1"

# List ingested lectures
scribo list --course cs101

# View synthesized notes or raw transcript in terminal
scribo view --course cs101 --lecture lec01
```
