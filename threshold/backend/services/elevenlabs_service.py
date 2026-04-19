from __future__ import annotations

import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

# ── Tour narration script ──────────────────────────────────────────────────────
TOUR_SCRIPT = """
Welcome to THRESHOLD — a real-time climate crisis intelligence platform built to detect ecological tipping points before they become irreversible.

What you're seeing is the War Room: a live three-dimensional globe showing eight of the world's most critically stressed marine and coastal ecosystems. Each pulsing ring represents a region approaching a point of no return. The color spectrum tells the story — teal for stable, shifting through yellow and orange, to red for critical.

The faint glowing points scattered across the ocean surfaces are live measurements from CalCOFI oceanographic stations — data from the Scripps Institution of Oceanography, tracking chlorophyll anomalies, dissolved oxygen levels, and sea surface temperature in real time. When those points glow orange, a biological alarm is ringing.

In the top right corner, notice the Critical Anomaly badge — this is the most endangered ecosystem on the planet right now, and a precise countdown of exactly how many days remain before it crosses its ecological threshold.

Navigate to Triage to see the full operational priority queue. Every monitored region is ranked by urgency, scored by ThresholdNet — our custom bidirectional LSTM neural network with attention, trained on IPCC, NOAA, and EPA scientific thresholds. This is not a guess. This is physics.

Click into any Region Brief for a full intelligence dossier — live stress signals, sea temperature anomalies, dissolved oxygen depletion curves, funding gaps, and branching intervention scenarios modeled from historical data.

The Counterfactual Engine answers the hardest question in disaster response: what would it have cost if we had acted sooner? The answer is always the same. Prevention costs a fraction of recovery. One dollar deployed before a threshold is crossed is worth up to fourteen dollars after.

The Funding Gap Radar exposes where the system is failing — regions with critical scores that receive almost no committed capital. These are the blind spots where ecosystems collapse quietly, without headlines.

And finally, the Threshold Fund is where data becomes action. Every contribution triggers a Stripe payment and an immutable record on the Solana blockchain — publicly verifiable by anyone, no crypto wallet required.

THRESHOLD was built because the data has been telling us the same story for years. The question is not whether the thresholds will be crossed. The question is whether we act before — or after.

Let's begin.
""".strip()

# Per-step narration scripts
STEP_SCRIPTS: list[str] = [
    "Welcome to THRESHOLD. This three-dimensional globe shows eight of Earth's most threatened marine ecosystems in real time. Each pulsing ring is a region approaching ecological collapse. The brighter and faster the pulse, the closer it is to the point of no return.",
    "The Critical Anomaly badge tracks the most endangered ecosystem on the planet right now — and counts exactly how many days remain before it crosses the threshold. When this number hits zero, recovery costs multiply by up to fourteen times.",
    "These Live Data Feeds power every score you see. Ocean biometrics from Scripps Institution of Oceanography via CalCOFI sensors. GDELT global conflict data queried live from Snowflake. And Gemini AI for grounded, real-time news intelligence.",
    "The Triage Queue is your operational command center. Every monitored region is ranked by urgency. ThresholdNet — our custom bidirectional LSTM neural network — scores each ecosystem from zero to ten using IPCC, NOAA, and EPA scientific thresholds. The most critical rise to the top.",
    "Each region has a full intelligence brief. Live stress signals, dissolved oxygen depletion curves, sea surface temperature anomalies, a funding gap analysis, and branching intervention scenarios modeled from real historical cases. This is the data that drives the decision.",
    "The Counterfactual Engine answers the hardest question in disaster response: what would it have cost if we had acted sooner? Drag the timeline scrubber to explore intervention windows. The cost divergence is dramatic — and it's always the same story.",
    "The Funding Gap Radar exposes systemic market failures. Regions in the bottom-right quadrant — critical scores, almost no committed capital — are the blind spots where ecosystems collapse without headlines. This is where intervention matters most.",
    "The Threshold Fund is where data becomes action. Select an active funding round, donate by card, and we write an immutable Solana blockchain record on your behalf. Publicly verifiable by anyone. No crypto wallet required. This is transparent climate finance.",
]

# In-memory audio cache keyed by step index (-1 = full narration)
_AUDIO_CACHE: dict[int, bytes] = {}


async def generate_audio(text: str, cache_key: int) -> bytes:
    if cache_key in _AUDIO_CACHE:
        logger.info(f"Returning cached audio for key={cache_key}.")
        return _AUDIO_CACHE[cache_key]

    if not settings.elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY is not configured.")

    logger.info(f"Generating audio via ElevenLabs (key={cache_key}, chars={len(text)})...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}",
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.48,
                    "similarity_boost": 0.78,
                    "style": 0.18,
                    "use_speaker_boost": True,
                },
            },
        )
        if not resp.is_success:
            err_body = resp.text
            logger.error(f"ElevenLabs API error {resp.status_code}: {err_body}")
            raise RuntimeError(f"ElevenLabs {resp.status_code}: {err_body[:300]}")
        _AUDIO_CACHE[cache_key] = resp.content
        logger.info(f"Audio cached for key={cache_key} ({len(resp.content)} bytes).")
        return _AUDIO_CACHE[cache_key]


async def generate_tour_audio() -> bytes:
    """Full narration (legacy single-file endpoint)."""
    return await generate_audio(TOUR_SCRIPT, cache_key=-1)
