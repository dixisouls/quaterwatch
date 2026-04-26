import re
import logging
from typing import Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
from backend.config import get_settings

settings = get_settings()
logger = logging.getLogger("worker.segmentation")

# Pydanctic schema for Gemini structured output
class TranscriptSegment(BaseModel):
    name: str
    text: str

class SegmentationResult(BaseModel):
    segments: list[TranscriptSegment]
    
# Gemini call with tenacity retry logic
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type((APIError,Exception)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_gemini(transcript: str) -> SegmentationResult:
    """
    Calls Gemini with structured output enforced via response_schema.
    Tenacity retries this up to 3 times on any API error with 
    exponential backoff and jitter.
    """
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
    
    prompt = f"""You are analyzing an earnings call transcript.
    Split the following transcript into named segments based on speaker sections
    and logical divisions such as Opening Remarks, CEO Remarks, CFO Review, Q&A Session.

    Return ONLY a valid JSON array with no preamble or explanation. Each element must have:
    - "name": a short descriptive name for the segment (string)
    - "text": the full text of that segment (string)

    Example format:
    [
    {{"name": "Opening Remarks", "text": "..."}},
    {{"name": "CEO Remarks", "text": "..."}},
    {{"name": "Q&A Session", "text": "..."}}
    ]

    Transcript:
    {transcript}
    """

    response = await client.aio.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SegmentationResult,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(
                thinking_level="MINIMAL"
            ),
        ),
    )

    return response.parsed

# Rule-based fallback

SEGMENT_PATTERNS = [
    re.compile(r"^([A-Z][a-zA-Z\s\-']+):\s*$", re.MULTILINE),
    re.compile(r"^\*\*([A-Z][a-zA-Z\s\-']+)\*\*\s*$", re.MULTILINE),
    re.compile(
        r"^(Operator|Opening Remarks|Prepared Remarks|"
        r"Question(?:s)?(?:\s*and\s*|\s*&\s*)Answer(?:s)?|Q&A|"
        r"Financial Review|CFO Review|CEO (?:Remarks|Comments|Statement)|"
        r"Management Discussion)\s*[:\-]?\s*$",
        re.MULTILINE | re.IGNORECASE,
    ),
]

def _rule_based_segment(transcript: str) -> list[dict]:
    """
    Attempts to split transcript into segments using regex patterns.
    Returns a list of dicts with "name" and "text" keys.
    """
    lines = transcript.split("\n")
    segments = []
    current_name : Optional[str] = None
    current_lines : list[str] = []

    for line in lines:
        matched = False
        for pattern in SEGMENT_PATTERNS:
            m = pattern.match(line.strip())
            if m:
                if current_name and current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        segments.append({
                            "name": current_name,
                            "text": text,
                        })
                current_name = m.group(1).strip()
                current_lines = []
                matched = True
                break
        if not matched:
            current_lines.append(line)
    if current_name and current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            segments.append({
                "name": current_name,
                "text": text,
            })
    return segments

# Public entry point
async def segment_transcript(transcript: str) -> tuple[list[dict], Optional[str]]:
    """
    Segments a transcript into named sections.
    1. Gemini with structured output (upto 3 attempt with tenacity)
    2. Rule-based fallback (regex patterns)
    3. Fallback to single "Full Transcript" segment if <2 segments detected
    """

    # Step 1: Try Gemini with tenacity
    try:
        result = await _call_gemini(transcript)
        segments = [
            {"name": s.name, "text": s.text}
            for s in result.segments
            if s.text.strip()
        ]
        if len(segments) >= 2:
            logger.info(f"[segmentation] Successfully segmented transcript with Gemini ({len(segments)} segments)")
            return segments, None
        logger.warning(
            f"[segmentation] Gemini segmentation failed with {len(segments)} segments, "
            f"falling back to rule-based segmentation"
        )
    except Exception as e:
        logger.error(
            f"[segmentation] Unexpected error during Gemini segmentation: {e}"
            f"falling back to rule-based segmentation"
        )
    
    # Step 2: Rule-based fallback
    segments = _rule_based_segment(transcript)
    logger.info(f"[segmentation] Rule-based segmentation found {len(segments)} segments")
    
    if len(segments) >= 2:
        return segments, None
    
    # Step 3: Fallback to full transcript
    logger.warning(
        f"[segmentation] Rule-based segmentation found {len(segments)} segments, "
        f"Using full transcript as single segment"
    )
    notice = "Segment detection was limited for this transcript."
    return [{"name": "Full Transcript", "text": transcript}], notice