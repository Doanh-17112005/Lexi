"""Repair the English definition field written by the original CEFR seed.

This migration is intentionally narrow and idempotent: it keeps item IDs and
user collections intact, and only updates a row when its English definition is
empty or still equals the Vietnamese translation from the old seed.
"""

import asyncio
import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.vocabulary import VocabularyItem
from seed_and_test_cefr_a1_c2 import CEFR_VOCABULARY


async def repair(*, apply: bool = False) -> int:
    if settings.is_production:
        raise RuntimeError("Run this repair only after an explicit production review.")

    repaired = 0
    async with AsyncSessionLocal() as db:
        for seed in CEFR_VOCABULARY:
            item = await db.scalar(
                select(VocabularyItem).where(VocabularyItem.word == seed["word"])
            )
            if item is None:
                continue
            if item.definition and item.definition != seed["meaning"]:
                continue
            item.definition = seed["definition"]
            item.translation = {
                "vi": seed["meaning"],
                "examples": [seed["example"]],
            }
            repaired += 1
        if apply:
            await db.commit()
        else:
            await db.rollback()
    return repaired


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit the narrow repair. Without this flag the script is a dry run.",
    )
    args = parser.parse_args()
    count = asyncio.run(repair(apply=args.apply))
    action = "Repaired" if args.apply else "Would repair"
    print(f"{action} {count} CEFR vocabulary definition(s).")
