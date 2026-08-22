from pathlib import Path
from scribo.config import settings
from scribo.rag.chunker import split_markdown_by_headers
from scribo.rag.vector_store import VectorStore

course_id = "eng448"
lecture_id = "lec01"
md_path = settings.COURSES_DATA_DIR / course_id / f"lecture_{lecture_id}.md"

if md_path.exists():
    text = md_path.read_text(encoding="utf-8")
    chunks = split_markdown_by_headers(text, course_id, lecture_id)
    print(f"Split into {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  - {chunk.metadata.header} [{chunk.metadata.timestamp}]")
        
    vs = VectorStore()
    vs.add_chunks(chunks)
    print("Successfully indexed!")
else:
    print(f"File not found: {md_path}")
