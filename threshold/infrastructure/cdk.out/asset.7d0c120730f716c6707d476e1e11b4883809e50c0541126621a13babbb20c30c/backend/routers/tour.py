from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter()


@router.get("/narration", summary="ElevenLabs tour audio — full or per-step")
async def get_tour_narration(step: int | None = Query(default=None)):
    """
    Returns MP3 audio for the guided tour.
    - `?step=N`  → short narration for step N (0-indexed)
    - no param   → full combined narration (legacy)
    Audio is cached in memory after the first generation.
    """
    from services.elevenlabs_service import (
        generate_audio, generate_tour_audio, STEP_SCRIPTS,
    )
    try:
        if step is not None:
            if step < 0 or step >= len(STEP_SCRIPTS):
                raise HTTPException(status_code=404, detail=f"Step {step} out of range (0–{len(STEP_SCRIPTS)-1})")
            audio = await generate_audio(STEP_SCRIPTS[step], cache_key=step)
        else:
            audio = await generate_tour_audio()
        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {e}")


@router.get("/steps", summary="Tour step metadata")
def get_tour_steps():
    """Returns the number of steps and their scripts — for accessibility/captions."""
    from services.elevenlabs_service import STEP_SCRIPTS
    return {"count": len(STEP_SCRIPTS), "scripts": STEP_SCRIPTS}
