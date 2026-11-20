"""Idempotent upsert script for CEFR A1-C2 Vocabulary catalog.

Safety guarantees:
- Defaults to --target test (refuses any DB name not ending in '_test') and --dry-run.
- Writing to local primary DB requires explicit `--target local --apply`.
- Never deletes users, user_vocabulary rows, or non-CEFR vocabulary items.
- Preserves AI_GENERATED + NEEDS_REVIEW provenance/QA metadata unless verified.
- Never logs database credentials or secrets.

Usage:
    cd backend-service
    venv/Scripts/python.exe -m scripts.seed_cefr_vocabulary --target test --apply
    venv/Scripts/python.exe -m scripts.seed_cefr_vocabulary --target local --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.cefr_vocabulary_data import (
    AUDIT_STATUS_CONFIRMED_SOURCE,
    CEFR_LEVELS,
    CEFR_VOCABULARY,
    QA_STATUS_VERIFIED,
    build_cefr_seed_tags,
    validate_cefr_vocabulary,
)
from app.core.config import settings
from app.core.database import Base
from app.models.vocabulary import DifficultyLevel, PartOfSpeech, VocabularyItem

_VOCAB_UUID_NAMESPACE = uuid.UUID("72a151d6-2c44-4a98-99b6-9a3f84d15a10")


def deterministic_vocab_uuid(level: str, word: str) -> uuid.UUID:
    """Return deterministic UUIDv5 for a canonical CEFR vocabulary headword."""
    return uuid.uuid5(_VOCAB_UUID_NAMESPACE, f"cefr:{level.upper()}:{word.casefold()}")


def _resolve_target_url(target: str) -> str:
    if target == "test":
        env_test = os.getenv("TEST_DATABASE_URL")
        if env_test:
            url = make_url(env_test)
        else:
            base = make_url(settings.DATABASE_URL)
            url = base.set(database="lexilingo_test")
        if not (url.database or "").endswith("_test"):
            raise RuntimeError(
                f"Refusing test seed on non-test database '{url.database}'"
            )
        return url.render_as_string(hide_password=False)

    if target == "local":
        return settings.DATABASE_URL

    raise ValueError(f"Unsupported target: {target}")


def _build_translation_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "vi": item["meaning"],
        "examples": [item["example"]],
    }


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _normalize_levels(levels: Sequence[str] | None) -> set[str] | None:
    if not levels:
        return None
    normalized: set[str] = set()
    for raw in levels:
        for part in str(raw).split(","):
            lvl = part.strip().upper()
            if not lvl:
                continue
            if lvl not in CEFR_LEVELS:
                raise ValueError(f"Unsupported CEFR level filter: {lvl}")
            normalized.add(lvl)
    return normalized or None


def select_cefr_items(
    *,
    only_verified: bool = False,
    only_confirmed_source: bool = False,
    levels: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Select a validated subset of CEFR_VOCABULARY without altering provenance."""
    validate_cefr_vocabulary(CEFR_VOCABULARY)
    allowed_levels = _normalize_levels(levels)
    items = list(CEFR_VOCABULARY)
    if only_verified:
        items = [item for item in items if item["qa_status"] == QA_STATUS_VERIFIED]
    if only_confirmed_source:
        items = [
            item
            for item in items
            if item.get("audit_status") == AUDIT_STATUS_CONFIRMED_SOURCE
        ]
    if allowed_levels is not None:
        items = [item for item in items if item["level"] in allowed_levels]
    return items


async def upsert_cefr_vocabulary(
    db: AsyncSession,
    *,
    only_verified: bool = False,
    only_confirmed_source: bool = False,
    levels: Sequence[str] | None = None,
) -> dict[str, int]:
    """Idempotently upsert CEFR A1-C2 vocabulary items while preserving extra rows."""
    items = select_cefr_items(
        only_verified=only_verified,
        only_confirmed_source=only_confirmed_source,
        levels=levels,
    )

    stats = {
        "selected": len(items),
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "preserved_non_cefr": 0,
    }

    existing_rows = (await db.execute(select(VocabularyItem))).scalars().all()
    by_word: dict[str, VocabularyItem] = {
        row.word.strip().casefold(): row for row in existing_rows
    }
    seed_keys = {item["word"].strip().casefold() for item in CEFR_VOCABULARY}
    stats["preserved_non_cefr"] = sum(
        1 for key in by_word if key not in seed_keys
    )

    for item in items:
        key = item["word"].strip().casefold()
        target_translation = _build_translation_payload(item)
        target_pronunciation = item["phonetic"] or None
        target_pos = PartOfSpeech(item["part_of_speech"])
        target_level = DifficultyLevel(item["level"])
        target_tags = build_cefr_seed_tags(item)

        existing = by_word.get(key)
        if existing is None:
            row = VocabularyItem(
                id=deterministic_vocab_uuid(item["level"], item["word"]),
                word=item["word"],
                definition=item["definition"],
                translation=target_translation,
                pronunciation=target_pronunciation,
                part_of_speech=target_pos,
                difficulty_level=target_level,
                tags=target_tags,
            )
            db.add(row)
            by_word[key] = row
            stats["created"] += 1
            continue

        changed = False
        if existing.definition != item["definition"]:
            existing.definition = item["definition"]
            changed = True
        if existing.translation != target_translation:
            existing.translation = target_translation
            changed = True
        if target_pronunciation and existing.pronunciation != target_pronunciation:
            existing.pronunciation = target_pronunciation
            changed = True
        if _enum_value(existing.part_of_speech) != target_pos.value:
            existing.part_of_speech = target_pos
            changed = True
        if _enum_value(existing.difficulty_level) != target_level.value:
            existing.difficulty_level = target_level
            changed = True
        if existing.tags != target_tags:
            existing.tags = target_tags
            changed = True

        if changed:
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    await db.flush()
    return stats


async def _run_cli(
    target: str,
    apply: bool,
    only_verified: bool,
    only_confirmed_source: bool = False,
    levels: Sequence[str] | None = None,
) -> dict[str, Any]:
    dsn = _resolve_target_url(target)
    engine = create_async_engine(dsn, poolclass=NullPool, echo=False)
    try:
        if target == "test":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as db:
            stats = await upsert_cefr_vocabulary(
                db,
                only_verified=only_verified,
                only_confirmed_source=only_confirmed_source,
                levels=levels,
            )
            total_after_flush = await db.scalar(select(func.count(VocabularyItem.id)))
            stats["total_rows_after_flush"] = int(total_after_flush or 0)
            if apply:
                await db.commit()
            else:
                await db.rollback()
            return stats
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Idempotent upsert for CEFR A1-C2 vocabulary catalog."
    )
    parser.add_argument(
        "--target",
        choices=["test", "local"],
        default="test",
        help="Target database: 'test' (lexilingo_test) or 'local' (configured DATABASE_URL).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit changes; without --apply, runs as a rolled-back dry run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry run (default when --apply is omitted).",
    )
    parser.add_argument(
        "--only-verified",
        action="store_true",
        help="Seed only items with qa_status == VERIFIED.",
    )
    parser.add_argument(
        "--only-confirmed-source",
        action="store_true",
        help=(
            "Seed only CONFIRMED_SOURCE items (preserving AI_GENERATED + "
            "NEEDS_REVIEW provenance without auto-promoting to VERIFIED)."
        ),
    )
    parser.add_argument(
        "--levels",
        nargs="*",
        help="Optional CEFR level filter (e.g. --levels A1 A2 or --levels A1,A2).",
    )
    args = parser.parse_args()
    apply = bool(args.apply and not args.dry_run)

    mode = "APPLY" if apply else "DRY-RUN (rolled back)"
    print(
        f"Running CEFR vocabulary upsert [target={args.target}, mode={mode}, "
        f"only_verified={args.only_verified}, "
        f"only_confirmed_source={args.only_confirmed_source}, "
        f"levels={args.levels or 'ALL'}]..."
    )
    stats = asyncio.run(
        _run_cli(
            args.target,
            apply,
            args.only_verified,
            args.only_confirmed_source,
            args.levels,
        )
    )
    for key, value in stats.items():
        print(f"  {key}={value}")


if __name__ == "__main__":
    main()
