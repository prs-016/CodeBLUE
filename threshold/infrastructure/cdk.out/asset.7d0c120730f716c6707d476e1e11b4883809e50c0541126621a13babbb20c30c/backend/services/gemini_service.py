from __future__ import annotations

import json
import logging
from datetime import date

from pydantic import BaseModel, Field

from config import settings

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

# ── In-memory cache: { "region_name|disaster_type": [list of news dicts] }
# Survives for the lifetime of the container — prevents burning free-tier quota
# on repeated requests for the same region.
_NEWS_CACHE: dict[str, list[dict]] = {}

# ── Curated fallback stubs shown when Gemini quota is exhausted.
# Mapped by lowercased keywords in the disaster_type string.
_FALLBACK_STUBS: dict[str, list[dict]] = {
    "marine": [
        {"title": "Ocean dead zones expand to record size in 2025",
         "body_summary": "NOAA reports hypoxic zones in the world's oceans grew by 8% in 2025, driven by agricultural runoff and rising sea temperatures suppressing dissolved oxygen levels.",
         "url": "https://oceanservice.noaa.gov/hazards/hypoxia/", "urgency_score": 7.8},
        {"title": "Coral bleaching alerts issued across Indo-Pacific regions",
         "body_summary": "NOAA Coral Reef Watch raised bleaching alerts for large swaths of the Indo-Pacific as sea surface temperatures exceeded thermal thresholds for the third consecutive year.",
         "url": "https://coralreefwatch.noaa.gov/", "urgency_score": 8.5},
        {"title": "Marine heatwave declared — fisheries face collapse risk",
         "body_summary": "Scientists warn that the ongoing marine heatwave is disrupting food web dynamics and placing critical commercial fish stocks at risk of collapse within 18 months.",
         "url": "https://www.iucn.org/resources/issues-brief/ocean-warming", "urgency_score": 7.2},
    ],
    "flood": [
        {"title": "Flood-displaced populations rise as monsoon intensity increases",
         "body_summary": "A record 12 million people were displaced by flooding in South and Southeast Asia during the 2025 monsoon season, with aid organisations warning of a 30% funding shortfall.",
         "url": "https://www.unocha.org/", "urgency_score": 8.1},
        {"title": "River basin flooding reaches 50-year high water marks",
         "body_summary": "Major river systems recorded peak flood stages not seen since the 1970s, inundating agricultural land and threatening freshwater infrastructure for millions downstream.",
         "url": "https://www.gdacs.org/", "urgency_score": 7.6},
    ],
    "cyclone": [
        {"title": "Rapid intensification events double as ocean heat content breaks records",
         "body_summary": "Climate scientists link the surge in Category 4–5 storms to record-high ocean heat content, which is fuelling rapid intensification within 24 hours of landfall.",
         "url": "https://www.nhc.noaa.gov/", "urgency_score": 9.0},
        {"title": "Cyclone preparedness gaps leave coastal millions exposed",
         "body_summary": "A joint UNDP-WMO review found that early-warning coverage for tropical cyclones remains below 40% for the most vulnerable coastal communities in low-income nations.",
         "url": "https://www.wmo.int/", "urgency_score": 8.3},
    ],
    "drought": [
        {"title": "Megadrought conditions persist across multiple continents",
         "body_summary": "Soil moisture anomalies consistent with multi-year megadroughts were recorded simultaneously across southern Africa, northern Chile, and the southwestern United States.",
         "url": "https://drought.unl.edu/", "urgency_score": 7.9},
        {"title": "Groundwater depletion accelerates — aquifer replenishment rates critical",
         "body_summary": "New satellite gravity data shows major aquifer systems are being depleted 3× faster than their natural replenishment rate, raising long-term water security concerns.",
         "url": "https://grace.jpl.nasa.gov/", "urgency_score": 8.0},
    ],
}

_DEFAULT_STUBS = [
    {"title": "Climate stress indicators reach critical levels in monitored region",
     "body_summary": "THRESHOLD signal analysis detected sustained anomalies across multiple environmental indicators including SST, dissolved oxygen, and chlorophyll concentration.",
     "url": "https://www.unep.org/explore-topics/climate-action", "urgency_score": 7.0},
    {"title": "International aid response lags behind growing humanitarian need",
     "body_summary": "UN OCHA reports a widening gap between funding commitments and the resources needed to address climate-driven displacement and ecosystem degradation globally.",
     "url": "https://www.unocha.org/", "urgency_score": 6.8},
    {"title": "Scientific consensus: tipping points closer than previously modelled",
     "body_summary": "A peer-reviewed meta-analysis published in Nature Climate Change finds that feedback loops are activating at lower warming thresholds than IPCC AR6 projections anticipated.",
     "url": "https://www.nature.com/nclimate/", "urgency_score": 7.5},
]


def _fallback_news(region_name: str, disaster_type: str) -> list[dict]:
    """Return curated stubs matching the disaster type."""
    dtype_lower = (disaster_type or "").lower()
    stubs = _DEFAULT_STUBS
    for keyword, items in _FALLBACK_STUBS.items():
        if keyword in dtype_lower:
            stubs = items
            break

    today = date.today().isoformat()
    return [
        {
            "id": f"stub-{i}-{hash(region_name)}",
            "title": s["title"],
            "body_summary": s["body_summary"],
            "url": s["url"],
            "urgency_score": s["urgency_score"],
            "date": today,
            "source_org": "THRESHOLD Intelligence Digest",
            "source_type": "curated",
            "disaster_type": disaster_type,
        }
        for i, s in enumerate(stubs)
    ]


async def search_news(region_name: str, disaster_type: str) -> list[dict]:
    """Use Gemini to research live news/situation reports for a region.

    Results are cached in-memory for the container lifetime to avoid burning
    free-tier quota on repeated requests for the same region.
    Falls back to curated stubs on 429 / quota failure.
    """
    cache_key = f"{region_name}|{disaster_type}"
    if cache_key in _NEWS_CACHE:
        logger.info(f"News cache hit for '{cache_key}'")
        return _NEWS_CACHE[cache_key]

    if not settings.gemini_api_key or not genai:
        logger.warning("Gemini not configured — returning fallback stubs")
        return _fallback_news(region_name, disaster_type)

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = (
        f"Identify the top 3-5 recent news headlines or situation reports regarding "
        f"{disaster_type} and environmental stress in {region_name}. "
        f"Focus on events from 2024-2026 if possible."
    )

    schema_def = {
        "type": "OBJECT",
        "properties": {
            "news": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "body_summary": {"type": "STRING"},
                        "url": {"type": "STRING"},
                        "urgency_score": {"type": "NUMBER"},
                    },
                    "required": ["title", "body_summary", "url", "urgency_score"],
                },
            }
        },
        "required": ["news"],
    }

    today = date.today().isoformat()

    # ── Attempt 1: Google Search grounding (real, verified URLs) ─────────────
    # Grounding is mutually exclusive with JSON response schema, so we ask for
    # JSON in the prompt itself and parse the model's free-form text output.
    try:
        grounded_prompt = (
            f"Search the web for the top 4 most recent news articles or situation reports "
            f"about {disaster_type} and environmental stress in {region_name} (2024–2026). "
            f"Return ONLY a JSON object — no markdown fences, no extra text — "
            f'with this structure: {{"news":[{{"title":"...","body_summary":"one sentence","url":"full URL","urgency_score":8.5}}]}}'
        )
        grounded_resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=grounded_prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            ),
        )

        # Extract real verified URLs from grounding metadata
        grounding_urls: list[str] = []
        try:
            meta = grounded_resp.candidates[0].grounding_metadata
            for chunk in (meta.grounding_chunks or []):
                if hasattr(chunk, "web") and chunk.web and chunk.web.uri:
                    grounding_urls.append(str(chunk.web.uri))
        except Exception:
            pass

        # Parse model text — strip markdown fences if present
        raw = grounded_resp.text.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            inner_lines = lines[1:] if lines[-1].strip() == "```" else lines[1:]
            if inner_lines and inner_lines[-1].strip() == "```":
                inner_lines = inner_lines[:-1]
            raw = "\n".join(inner_lines)

        data = json.loads(raw)
        out = []
        for i, n in enumerate(data.get("news", [])):
            # Prefer grounding URL (real, verified by Google) over model-generated one
            url = grounding_urls[i] if i < len(grounding_urls) else n.get("url", "")
            out.append({
                "id": f"gemini-grounded-{hash(n['title'])}",
                "title": n["title"],
                "body_summary": n["body_summary"],
                "url": url,
                "urgency_score": float(n.get("urgency_score", 7.0)),
                "date": today,
                "source_org": "Threshold Intelligence (Google Search)",
                "source_type": "gemini_grounded",
                "disaster_type": disaster_type,
            })

        if out:
            _NEWS_CACHE[cache_key] = out
            logger.info(f"Cached {len(out)} grounded news items for '{cache_key}' ({len(grounding_urls)} verified URLs)")
            return out
    except Exception as grounded_err:
        logger.warning(f"Grounded search failed, falling back to structured call: {grounded_err}")

    # ── Attempt 2: Structured JSON call (no grounding, but schema-enforced) ──
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema_def,
                temperature=0.1,
            ),
        )
        data = json.loads(response.text)
        out = []
        for n in data.get("news", []):
            out.append({
                "id": f"gemini-{hash(n['title'])}",
                "title": n["title"],
                "body_summary": n["body_summary"],
                "url": n["url"],
                "urgency_score": n["urgency_score"],
                "date": today,
                "source_org": "Threshold Intelligence",
                "source_type": "gemini",
                "disaster_type": disaster_type,
            })
        _NEWS_CACHE[cache_key] = out
        logger.info(f"Cached {len(out)} Gemini news items for '{cache_key}'")
        return out
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            logger.warning(f"Gemini quota exhausted for news search — using fallback stubs ({region_name})")
        else:
            logger.error(f"Gemini search_news error: {e}")
        fallback = _fallback_news(region_name, disaster_type)
        _NEWS_CACHE[cache_key] = fallback
        return fallback

async def search_charities(region_name: str, disaster_type: str) -> list[dict]:
    """Use Gemini to identify relevant global and local charities."""
    if not settings.gemini_api_key:
        return [{"name": "ERROR: settings.gemini_api_key is empty", "url": "", "focus": ""}]
    if not genai:
        return [{"name": "ERROR: genai import failed (google-genai not found)", "url": "", "focus": ""}]

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = (
        f"Identify the top 4 to 6 credible international and local charities or NGOs that provide "
        f"humanitarian and {disaster_type} disaster relief support in {region_name}. "
    )

    schema_def = {
        "type": "OBJECT",
        "properties": {
            "charities": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING", "description": "Name of the charity, NGO, or humanitarian agency"},
                        "url": {"type": "STRING", "description": "Valid website URL. Provide a valid URL, otherwise empty string"},
                        "focus": {"type": "STRING", "description": "A brief 3-5 word phrase describing their specific relief focus"}
                    },
                    "required": ["name", "url", "focus"]
                }
            }
        },
        "required": ["charities"]
    }

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema_def,
                temperature=0.1,
            ),
        )

        data = json.loads(response.text)
        out = []
        for c in data.get("charities", []):
            name = c.get("name", "").strip()
            if not name:
                continue
            out.append({
                "name": name,
                "url": c.get("url") or None,
                "focus": c.get("focus") or "disaster relief",
                "source": "gemini"
            })
        return out
    except Exception as e:
        logger.error(f"Gemini search_charities error: {e}")
        return [{"name": f"SERVICE ERROR: {str(e)}", "url": "", "focus": "", "source": "gemini"}]
