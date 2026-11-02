import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.course import Course, Lesson
from app.models.vocabulary import VocabularyItem

async def check_cefr():
    async with AsyncSessionLocal() as db:
        print("=== KIEM TRA DU LIEU CAP DO CEFR (A1 -> C2) ===")

        # 1. Khoa hoc theo CEFR
        courses = (await db.execute(select(Course))).scalars().all()
        print(f"\nTong so khoa hoc: {len(courses)}")
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        for lvl in levels:
            matching = [c for c in courses if getattr(c, "level", None) == lvl or lvl in (c.title or "")]
            print(f"- Cap do {lvl}: {len(matching)} khoa hoc")
            for c in matching[:2]:
                print(f"    * [{lvl}] {c.title} (ID: {c.id})")

        # 2. Bai hoc (Lessons)
        total_lessons = await db.scalar(select(func.count(Lesson.id)))
        print(f"\nTong so bai hoc (Lessons): {total_lessons}")

        # 3. Tu vung theo CEFR
        vocab_total = await db.scalar(select(func.count(VocabularyItem.id)))
        print(f"\nTong so tu vung: {vocab_total}")
        for lvl in levels:
            cnt = await db.scalar(select(func.count(VocabularyItem.id)).where(VocabularyItem.difficulty_level == lvl))
            print(f"- Tu vung cap {lvl}: {cnt} tu")

if __name__ == "__main__":
    asyncio.run(check_cefr())
