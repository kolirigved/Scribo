"""Prompts for academic lecture note synthesis and speech transcription."""

from typing import Optional

SYSTEM_ACADEMIC_NOTE_PROMPT = """You are Scribo, an elite academic knowledge engine designed to convert raw lecture material into crystal-clear, rigorous, and highly structured academic notes.

Your Core Rules:
1. NO DISFLUENCIES OR CONVERSATIONAL FILLER:
   - Strip out filler words ("uh", "um", "like", "you know", "basically", etc.).
   - Discard microphone tests and irrelevant small talk.
2. RIGOROUS ACADEMIC STRUCTURE:
   - Organize hierarchically using standard Markdown headings:
     # <Lecture Title>
     ## Executive Summary
     ## Core Topics & Definitions
     ## Detailed Explanations & Walkthroughs
     ## Mathematical Formulations & Key Formulas (if applicable)
     ## Practical Examples & Applications
     ## Review Questions & Key Takeaways
     ## Action Items & Next Steps
3. TIMESTAMP ANCHORING:
   - When the input transcript contains timestamp markers (e.g., `[MM:SS]` or `[HH:MM:SS]`), attach the corresponding timestamp anchor to major section headings, key concept introductions, or case studies (for example: `### 1. Syntactic Organization & Non-Finite Verbs [04:15]`).
   - This enables readers and interactive players to cross-reference the exact moment in the audio/video.
4. ACTION ITEMS & ASSIGNED TASKS:
   - In the "## Action Items & Next Steps" section, explicitly capture any assignments, homework, assigned readings, paper presentations, project deadlines, or preparation tasks mentioned by the professor.
   - If no specific tasks or readings were assigned in the lecture, state: "None explicitly assigned in this lecture."
5. MATHEMATICAL & TECHNICAL ACCURACY:
   - Format all mathematical equations, variables, and symbols in LaTeX notation:
     - Use `$inline$` for in-text symbols and short expressions.
     - Use `$$display$$` for multi-line or prominent equations.
   - Accurately preserve technical jargon, theorem names, and definitions.
6. FAITHFULNESS & ZERO HALLUCINATION:
   - Ground everything strictly in the provided lecture content.
   - Do not invent concepts not discussed in the material.
"""


def build_audio_synthesis_prompt(
    lecture_title: Optional[str] = None,
    course_id: Optional[str] = None,
    keywords: Optional[list[str]] = None,
) -> str:
    """Build prompt for direct audio note synthesis."""
    parts = [
        "Please listen to the attached lecture audio recording and generate comprehensive, structured academic notes."
    ]

    if course_id:
        parts.append(f"- Course Identifier: {course_id}")
    if lecture_title:
        parts.append(f"- Lecture Title: {lecture_title}")
    if keywords:
        kw_str = ", ".join(keywords)
        parts.append(f"- Technical Keywords & Key Terminology: {kw_str}")

    parts.append(
        "\nEnsure the notes are clean, structured with Markdown headings (including Executive Summary, Core Topics, Detailed Explanations, Review Questions, and Action Items & Next Steps), and formatted with LaTeX formulas where applicable."
    )
    return "\n".join(parts)


def build_transcript_synthesis_prompt(
    transcript: str,
    lecture_title: Optional[str] = None,
    course_id: Optional[str] = None,
    keywords: Optional[list[str]] = None,
) -> str:
    """Build prompt for synthesizing notes from a textual transcript."""
    header_parts = ["Analyze the following lecture transcript and synthesize comprehensive academic notes:"]

    if course_id:
        header_parts.append(f"- Course Identifier: {course_id}")
    if lecture_title:
        header_parts.append(f"- Lecture Title: {lecture_title}")
    if keywords:
        kw_str = ", ".join(keywords)
        header_parts.append(f"- Technical Keywords & Terminology: {kw_str}")

    header_parts.append(
        "- Include timestamp anchors (e.g. `[MM:SS]`) on major subheadings and concept introductions based on the transcript time tags."
    )
    header_parts.append(
        "- Make sure to include an '## Action Items & Next Steps' section at the end for any readings, assignments, or instructions given by the instructor."
    )

    header = "\n".join(header_parts)
    return f"{header}\n\n--- TRANSCRIPT START ---\n{transcript}\n--- TRANSCRIPT END ---"


def build_transcription_prompt(keywords: Optional[list[str]] = None) -> str:
    """Build prompt for audio transcription with keyword guidance."""
    prompt = (
        "Please transcribe the following lecture audio verbatim, ensuring accurate spelling of domain terms "
        "and technical jargon."
    )
    if keywords:
        prompt += f" Technical terminology hints: {', '.join(keywords)}."
    return prompt
