from __future__ import annotations

import httpx

from config import settings

ORTHO_BASE = "https://api.orth.sh/v1/run"


async def ortho_post(api: str, path: str, *, query: dict | None = None, body: dict | None = None) -> dict:
    payload: dict = {"api": api, "path": path}
    if query:
        payload["query"] = query
    if body:
        payload["body"] = body

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            ORTHO_BASE,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.orthogonal_api_key}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        return resp.json()
