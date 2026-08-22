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
    """
    chunks = []
    
    # Split text on headers (H1, H2, H3)
    # The regex matches ^#+ followed by space and capturing the rest of the line
    header_pattern = re.compile(r'^(#{1,3})\s+(.*)$', re.MULTILINE)
    
    # Find all matches
    matches = list(header_pattern.finditer(markdown_text))
    
    if not matches:
        # If no headers found, treat entire text as one chunk
        chunks.append(Chunk(
            text=markdown_text.strip(),
            metadata=ChunkMetadata(
                course_id=course_id,
                lecture_id=lecture_id,
                header="Unknown"
            )
        ))
        return chunks

    for i, match in enumerate(matches):
        header_text = match.group(2).strip()
        
        # Extract timestamp if exists: [MM:SS]
        timestamp_match = re.search(r'\[(\d{2}:\d{2})\]', header_text)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        # Determine the start and end of this chunk's content
        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(markdown_text)
        
        content = markdown_text[start_idx:end_idx].strip()
        
        if content:
            chunks.append(Chunk(
                text=content,
                metadata=ChunkMetadata(
                    course_id=course_id,
                    lecture_id=lecture_id,
                    header=header_text,
                    timestamp=timestamp
                )
            ))
            
    return chunks
