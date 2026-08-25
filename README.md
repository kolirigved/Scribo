# Scribo 📜

**Scribo** is an academic knowledge engine and ingestion pipeline designed to process lecture recordings and slide decks into structured LaTeX Markdown notes, indexing them for multi-lecture revision and grounded question answering (RAG).

The repository is organized as a modern **Monorepo**:
- **`backend/`**: Python engine containing the audio ingestion pipeline, Gemini synthesis, local ChromaDB vector store, RAG query engine, CLI tools, and FastAPI backend.
- **`frontend/`**: Next.js 15 web application featuring a dark-themed glassmorphism interface, interactive LaTeX math rendering, and a real-time RAG study assistant.

---

## ✨ Features

- **Audio Compression & Preprocessing**: Converts multi-channel recordings (`.m4a`, `.wav`, `.mp3`) into single-channel mono MP3 at 32–48 kbps using `ffmpeg`/`pydub`.
- **Two-Stage Audio $\to$ Transcript $\to$ Notes Pipeline**:
  1. Extract verbatim transcripts with exact `[MM:SS]` segment timestamps using **Whisper** (Groq / OpenAI) or **Gemini STT**.
  2. Synthesize structured academic notes from the extracted transcript using **Gemini**.
- **Advanced RAG Engine**:
  - **Hierarchical Chunking**: Markdown chunker that prepends ancestral section paths to preserve deep context and timestamp metadata.
  - **Hybrid Search**: Fuses dense vector search (ChromaDB + `gemini-embedding-2` in batches) with lexical search (BM25) using Reciprocal Rank Fusion (RRF) for precise technical retrieval.
  - **Cross-Encoder Re-Ranking**: Uses FlashRank to re-score candidate chunks and filter out irrelevant noise before passing context to the LLM.
  - **Grounded Generation**: Inline citations linking directly to exact audio segments (`[Course - Lecture @ MM:SS]`).
- **Interactive Web Interface**:
  - Split-screen workspace (interactive LaTeX notes on the left, RAG chat assistant on the right).
  - Glassmorphic dark UI tailored for distraction-free studying.

---

## 🚀 Quickstart

### 1. Setup Python Backend & CLI

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies & editable package
pip install -r backend/requirements.txt
pip install -e backend/ --no-deps
```

Configure backend environment variables:
```bash
cp backend/.env.example backend/.env
```
Add your `GEMINI_API_KEY` (and optional `GROQ_API_KEY` / `OPENAI_API_KEY` for Whisper STT) to `backend/.env`.

### 2. Setup Next.js Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
cd ..
```

---

## 💻 Running the Web Application

To use the interactive web UI, run both the FastAPI backend and Next.js frontend:

**Terminal 1: FastAPI Backend**
```bash
cd backend
../.venv/bin/uvicorn api.main:app --reload --port 8000
```

**Terminal 2: Next.js Frontend**
```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser!

---

## 🛠️ CLI Usage

The Scribo CLI is available for background processing and terminal-based interactions:

```bash
# Check system and API key status
scribo info

# Run full ingestion pipeline (Compress -> Transcribe -> Synthesize -> Index into ChromaDB)
scribo process \
  --course eng448 \
  --lecture lec01 \
  --audio "/path/to/lecture.m4a" \
  --title "Introduction to Dravidian Languages"

# Extract transcript only
scribo transcribe --course cs101 --lecture lec01 --audio /path/to/lecture.m4a

# Synthesize notes from an existing transcript file
scribo synthesize --course cs101 --lecture lec01 --transcript /path/to/transcript.txt --title "Lecture 1"

# Query the knowledge base via CLI using Grounded RAG
scribo ask --course eng448 "What is zero copula?"

# List all ingested courses and lectures
scribo list --course eng448

# View synthesized notes or transcripts in terminal
scribo view --course eng448 --lecture lec01
scribo view --course eng448 --lecture lec01 --transcript
```

---

## 🧪 Testing

The backend test suite is fully isolated and mocked to ensure zero API token consumption:

```bash
.venv/bin/pytest backend/tests/
```
