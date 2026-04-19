from __future__ import annotations

import json
import logging

from pydantic import BaseModel, Field

from config import settings

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class Charity(BaseModel):
    name: str = Field(description="Name of the charity, NGO, or humanitarian agency.")
    url: str = Field(description="Valid website URL where users can learn more or donate. Provide a valid URL, otherwise empty string.")
    focus: str = Field(description="A brief 3-5 word phrase describing their specific relief focus.")

class CharitiesResponse(BaseModel):
    charities: list[Charity]

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
