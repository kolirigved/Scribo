import re
from typing import List
from pydantic import BaseModel

class ChunkMetadata(BaseModel):
    course_id: str
    lecture_id: str
    header: str
    timestamp: str | None = None

class Chunk(BaseModel):
    text: str
    metadata: ChunkMetadata

def split_markdown_by_headers(markdown_text: str, course_id: str, lecture_id: str) -> List[Chunk]:
    """
    Splits a markdown document into chunks based on headers.
    Extracts timestamps like [MM:SS] if present in the header.
    Prepends the chunk with hierarchical context.
    """
    chunks = []
    
    header_pattern = re.compile(r'^(#{1,3})\s+(.*)$', re.MULTILINE)
    matches = list(header_pattern.finditer(markdown_text))
    
    course_id = course_id.lower()
    lecture_id = lecture_id.lower()

    if not matches:
        chunks.append(Chunk(
            text=markdown_text.strip(),
            metadata=ChunkMetadata(
                course_id=course_id,
                lecture_id=lecture_id,
                header="Unknown"
            )
        ))
        return chunks

    # Keep track of header hierarchy
    hierarchy = {}

    for i, match in enumerate(matches):
        level = len(match.group(1))
        header_text = match.group(2).strip()
        
        # Update hierarchy
        hierarchy[level] = header_text
        # Clear deeper levels
        for l in list(hierarchy.keys()):
            if l > level:
                del hierarchy[l]
        
        # Build hierarchy path
        path_parts = [hierarchy[l] for l in sorted(hierarchy.keys())]
        header_path = " -> ".join(path_parts)
        
        timestamp_match = re.search(r'\[(\d{2}:\d{2}(?::\d{2})?)\]', header_text)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(markdown_text)
        
        content = markdown_text[start_idx:end_idx].strip()
        
        if content:
            # Prepend context to text for better embedding
            contextual_text = f"[Course: {course_id.upper()} | Lecture: {lecture_id} | Section: {header_path}]\n{content}"
            chunks.append(Chunk(
                text=contextual_text,
                metadata=ChunkMetadata(
                    course_id=course_id,
                    lecture_id=lecture_id,
                    header=header_path,
                    timestamp=timestamp
                )
            ))
            
    return chunks

def split_slides_by_page(slides_text: str, course_id: str, lecture_id: str) -> List[Chunk]:
    """
    Splits slide extracted text into chunks based on page breadcrumbs.
    """
    chunks = []
    
    # Pattern to match [Slide: Page X]
    page_pattern = re.compile(r'^\[Slide: Page (\d+)\]', re.MULTILINE)
    matches = list(page_pattern.finditer(slides_text))
    
    course_id = course_id.lower()
    lecture_id = lecture_id.lower()
    
    if not matches:
        chunks.append(Chunk(
            text=slides_text.strip(),
            metadata=ChunkMetadata(
                course_id=course_id,
                lecture_id=lecture_id,
                header="Slide Text"
            )
        ))
        return chunks
        
    for i, match in enumerate(matches):
        page_num = match.group(1)
        header_text = f"Slide {page_num}"
        
        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(slides_text)
        
        content = slides_text[start_idx:end_idx].strip()
        
        if content:
            contextual_text = f"[Course: {course_id.upper()} | Lecture: {lecture_id} | Section: {header_text}]\n{content}"
            chunks.append(Chunk(
                text=contextual_text,
                metadata=ChunkMetadata(
                    course_id=course_id,
                    lecture_id=lecture_id,
                    header=header_text,
                    timestamp=None
                )
            ))
            
    return chunks
