from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


INGESTION_MODULES = [
    "data.ingestion.keeling_curve",
    "data.ingestion.calcofi",
    "data.ingestion.scripps_pier",
    "data.ingestion.noaa_sst",
    "data.ingestion.coral_reef_watch",
    "data.ingestion.nasa_ocean_color",
    "data.ingestion.ocha_fts",
    "data.ingestion.hdx",
    "data.ingestion.emdat",
    "data.ingestion.world_bank",
    "data.ingestion.reliefweb",
    "data.ingestion.gdelt",
    "data.ingestion.nasa_noaa_press",
    "data.ingestion.charity_navigator",
    "data.ingestion.reliefweb_3w",
    "data.ingestion.givewell",
]

PROCESSING_MODULES = [
    "data.processing.feature_engineering",
    "data.processing.regional_aggregator",
    "data.processing.funding_gap_calculator",
    "data.processing.media_attention_scorer",
]

# Final step: map processed pipeline tables → backend API tables
BACKEND_SYNC_MODULE = "data.seed_backend"


async def run_module(module_name: str) -> tuple[str, int]:
    loop = asyncio.get_running_loop()
    module = importlib.import_module(module_name)
    frame = await loop.run_in_executor(None, module.main)
    rows = len(frame) if hasattr(frame, "__len__") else 0
    return module_name.rsplit(".", 1)[-1], rows


async def main() -> None:
    ingestion_groups = [
        INGESTION_MODULES[:6],
        INGESTION_MODULES[6:10],
        INGESTION_MODULES[10:13],
        INGESTION_MODULES[13:],
    ]
    for group in ingestion_groups:
        results = await asyncio.gather(*(run_module(module_name) for module_name in group), return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                print(f"✗ ingestion step failed: {result}")
            else:
                name, rows = result
                print(f"✓ {name}: {rows:,} rows")

    for module_name in PROCESSING_MODULES:
        result = await run_module(module_name)
        name, rows = result
        print(f"✓ {name}: {rows:,} rows")

    # Sync pipeline output → backend API tables
    print("\n--- Seeding backend database ---")
    result = await run_module(BACKEND_SYNC_MODULE)
    name, rows = result
    print(f"✓ {name}: {rows:,} tables synced")


if __name__ == "__main__":
    asyncio.run(main())
