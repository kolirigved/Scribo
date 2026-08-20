"""Prompts for academic lecture note synthesis and speech transcription."""

from typing import Optional

SYSTEM_ACADEMIC_NOTE_PROMPT = """You are Scribo, an elite academic knowledge engine designed to convert raw lecture material into crystal-clear, rigorous, and highly structured academic notes.

Your Core Rules:
1. NO DISFLUENCIES OR CONVERSATIONAL FILLER:
   - Strip out filler words ("uh", "um", "like", "you know", "basically", etc.).
   - Discard administrative chatter, tangents, microphone tests, and classroom logistics.
2. RIGOROUS ACADEMIC STRUCTURE:
   - Organize hierarchically using standard Markdown headings:
     # <Lecture Title>
     ## Executive Summary
     ## Core Topics & Definitions
     ## Detailed Explanations & Walkthroughs
     ## Mathematical Formulations & Key Formulas (if applicable)
     ## Practical Examples & Applications
     ## Review Questions & Key Takeaways
3. MATHEMATICAL & TECHNICAL ACCURACY:
   - Format all mathematical equations, variables, and symbols in LaTeX notation:
     - Use `$inline$` for in-text symbols and short expressions.
     - Use `$$display$$` for multi-line or prominent equations.
   - Accurately preserve technical jargon, theorem names, and definitions.
4. FAITHFULNESS & ZERO HALLUCINATION:
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
        "\nEnsure the notes are clean, structured with Markdown headings, and formatted with LaTeX formulas where applicable."
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
