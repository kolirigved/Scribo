from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

from scribo.config import settings

app = FastAPI(title="Scribo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/courses")
def list_courses():
    courses = []
    if not settings.COURSES_DATA_DIR.exists():
        return courses
    for course_dir in settings.COURSES_DATA_DIR.iterdir():
        if course_dir.is_dir() and not course_dir.name.startswith("."):
            courses.append(course_dir.name)
    return {"courses": courses}

@app.get("/courses/{course_id}")
def get_course_lectures(course_id: str):
    course_path = settings.COURSES_DATA_DIR / course_id
    if not course_path.exists():
        raise HTTPException(status_code=404, detail="Course not found")
    
    lectures = []
    for file in course_path.glob("lecture_*.md"):
        lecture_id = file.stem.replace("lecture_", "")
        lectures.append(lecture_id)
    return {"course": course_id, "lectures": lectures}

@app.get("/courses/{course_id}/lectures/{lecture_id}")
def get_lecture_details(course_id: str, lecture_id: str):
    course_path = settings.COURSES_DATA_DIR / course_id
    md_path = course_path / f"lecture_{lecture_id}.md"
    json_path = course_path / f"lecture_{lecture_id}_transcript.json"
    
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Lecture not found")
        
    markdown_content = md_path.read_text(encoding="utf-8")
    
    transcript_segments = []
    if json_path.exists():
        try:
            transcript_segments = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
            
    return {
        "course": course_id,
        "lecture": lecture_id,
        "markdown": markdown_content,
        "segments": transcript_segments
    }

class QueryRequest(BaseModel):
    query: str
    course_id: str | None = None
    query_rewriting: bool = True
    history: list[dict] | None = None

@app.post("/query")
def query_rag(request: QueryRequest):
    from scribo.rag.query_engine import QueryEngine
    try:
        engine = QueryEngine()
        return engine.query(
            question=request.query,
            course_id=request.course_id,
            enable_query_rewriting=request.query_rewriting,
            history=request.history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
