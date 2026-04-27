import logging
import uuid
import asyncio
from pydantic import BaseModel
from enum import StrEnum
from google.cloud import language_v1
from google.api_core.exceptions import GoogleAPIError
from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
from backend.config import get_settings
from backend.models.models import Entity, Segment

settings = get_settings()
logger = logging.getLogger("worker.entity")

# Entity types from NL API relevant to earnings call
RELEVANT_ENTITY_TYPES = [
    language_v1.Entity.Type.PERSON,
    language_v1.Entity.Type.ORGANIZATION,
    language_v1.Entity.Type.EVENT,
    language_v1.Entity.Type.NUMBER,
]

MIN_SALIENCE = 0.01

# Pydantic schema for Gemini structured output
class EntityType(StrEnum):
    PRODUCT = "PRODUCT"
    SEGMENT = "SEGMENT"
    METRIC = "METRIC"
    COMPETITOR = "COMPETITOR"
    ACQUISITION = "ACQUISITION"
    MARKET = "MARKET"
    INITIATIVE = "INITIATIVE"
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"

class FinancialEntity(BaseModel):
    name: str
    entity_type: EntityType

class FinancialEntityList(BaseModel):
    entities: list[FinancialEntity]

# NL API Pass
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type(GoogleAPIError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_nl_api_entities(text: str) -> list[dict]:
    """
    Calls the NL API analyze_entities and returns filtered entities.
    Keep only earnings relevant entities and high-salience entities.
    """
    client = language_v1.LanguageServiceAsyncClient()
    document = language_v1.Document(
        content=text,
        type_=language_v1.Document.Type.PLAIN_TEXT,
    )
    request = language_v1.AnalyzeEntitiesRequest(
        document=document,
    )
    response = await client.analyze_entities(request=request)
    result = []
    for entity in response.entities:
        entity_type = language_v1.Entity.Type(entity.type_)
        salience = entity.salience
        
        if entity_type not in RELEVANT_ENTITY_TYPES or salience < MIN_SALIENCE:
            continue
        
        result.append({
            "name": entity.name,
            "entity_type": entity_type.name,
            "salience": salience,
            "source": "nl_api",
        })
    return result

# Gemini pass
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type((APIError,Exception)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _call_gemini(text: str) -> list[dict]:
    """
    Calls Gemini with financial-specific entity not caught by NL API.
    Applies hallucination filter: discards any entity whose name is not
    found as a substring in the original segment text.
    """
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )

    prompt = (
        "You are extracting named entities from an earnings call transcript segment. "
        "Only extract entities that are materially significant to an investor analyzing this call. "
        "Rules:\n"
        "- PERSON: executives, analysts, named speakers only — not job titles alone\n"
        "- ORGANIZATION: companies, institutions, named partners/customers — not internal teams, departments, or sports teams\n"
        "- PRODUCT: named product lines or services — not generic category names\n"
        "- SEGMENT: named business units — not vague groupings like 'our consumer business'\n"
        "- METRIC: specific figures with context (e.g. '42% gross margin', '$4.2B guidance') — not bare numbers\n"
        "- COMPETITOR: explicitly named competing companies only\n"
        "- ACQUISITION: named deals only\n"
        "- MARKET: specific named geographies or verticals — not 'the market' or 'our customers'\n"
        "- INITIATIVE: named programs or strategies — not vague goals\n"
        "Prefer fewer high-confidence entities over an exhaustive noisy list. "
        "Only include entities explicitly named in the text.\n\n"
        f"Segment:\n{text}"
    )

    response = await client.aio.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinancialEntityList,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(
                thinking_level="MINIMAL"
            ),
        ),
    )

    parsed = response.parsed
    text_lower = text.lower()
    
    results = []
    for entity in parsed.entities:
        # hallucination filter: discard if name not found in original text
        if entity.name.lower() not in text_lower:
            logger.warning(
                f"[entity] Discarded hallucinated entity: {entity.name} "
                f"not found in original text."
            )
            continue
        results.append({
            "name": entity.name,
            "entity_type": entity.entity_type,
            "salience": None,
            "source": "gemini",
        })
    return results

# Per-segment handler
async def extract_entities_for_segment(
    segment: Segment,
) -> list[Entity]:
    """
    Runs NL API and Gemini passes to extract entities for a single segment.
    Merges results, deduplicates by name.
    If NL API fails, use Gemini only.
    If both fail, return empty list and continue.
    Returns a list of unsaved Entity ORM objects.
    """
    nl_result, gemini_result = await asyncio.gather(
        _call_nl_api_entities(segment.text),
        _call_gemini(segment.text),
        return_exceptions=True,
    )

    if isinstance(nl_result, Exception):
        logger.error(
            f"[entity] NL API failed for segment {segment.id} | {segment.name} : {nl_result} "
            f"Skipping NL API pass"
        )
        nl_entities = []
    else:
        nl_entities = nl_result
        logger.info(
            f"[entity] NL API found {len(nl_entities)} entities "
            f"for segment {segment.id} | {segment.name}"
        )

    if isinstance(gemini_result, Exception):
        logger.error(
            f"[entity] Gemini failed for segment {segment.id} | {segment.name} : {gemini_result} "
            f"Skipping Gemini pass"
        )
        gemini_entities = []
    else:
        gemini_entities = gemini_result
        logger.info(
            f"[entity] Gemini found {len(gemini_entities)} entities "
            f"for segment {segment.id} | {segment.name}"
        )
    # Merge and deduplicate by name
    seen = set()
    merged = []
    
    for e in nl_entities + gemini_entities:
        name_lower = e["name"].lower()
        if name_lower not in seen:
            seen.add(name_lower)
            merged.append(e)
    
    if not merged:
        logger.warning(
            f"[entity] No entities found for segment {segment.id} | {segment.name}"
        )
    
    return [
        Entity(
            segment_id=segment.id,
            name=e["name"],
            entity_type=e["entity_type"],
            source=e["source"],
            salience=e["salience"],
        )
        for e in merged
    ]

# Public entry point
async def extract_entities_for_job(db: AsyncSession, job_id: uuid.UUID) -> list[Entity]:
    """
    Fetches all segments for the job from DB, extracts entities for each.
    A failure on one segment does not block the rest.
    Returns a list of unsaved Entity ORM objects.
    """
    result = await db.execute(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.order_index)
    )

    segments = result.scalars().all()
    results = await asyncio.gather(
        *[extract_entities_for_segment(segment) for segment in segments],
    )
    return [entity for result in results for entity in result]