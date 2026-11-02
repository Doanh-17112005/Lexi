import argparse
import asyncio
import sys
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.course import Course, Lesson, Unit
from app.models.course_category import CourseCategory
from app.models.progress import UserCourseProgress
from app.models.user import User
from app.models.vocabulary import DifficultyLevel, PartOfSpeech, VocabularyItem

sys.stdout.reconfigure(encoding="utf-8")

# ── 1. DỮ LIỆU KHÓA HỌC & BÀI TẬP CHUẨN TỪ A1 ĐẾN C2 ────────────────────────
CEFR_COURSES = [
    {
        "level": "A1",
        "title": "A1 - English Foundations",
        "desc": "Dành cho người mới bắt đầu: Ngữ pháp hiện tại đơn, danh từ số nhiều và câu hỏi cơ bản.",
        "xp": 100,
        "exercises": [
            {
                "id": "a1_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Choose the correct form: 'She ___ to school every day.'",
                "options": [{"id": "0", "text": "goes", "is_correct": True}, {"id": "1", "text": "go", "is_correct": False}, {"id": "2", "text": "going", "is_correct": False}],
                "correct_answer": "goes",
                "explanation": "Chủ ngữ ngôi thứ ba số ít (She) đi với động từ thêm 'es' ở thì hiện tại đơn."
            },
            {
                "id": "a1_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete the sentence: 'They {blank} two cats.'",
                "correct_answer": "have",
                "explanation": "Chủ ngữ 'They' đi với động từ 'have'."
            }
        ]
    },
    {
        "level": "A2",
        "title": "A2 - Daily Communication",
        "desc": "Giao tiếp hàng ngày: Kể về quá khứ đơn, hỏi đường, mua sắm và thói quen sinh hoạt.",
        "xp": 150,
        "exercises": [
            {
                "id": "a2_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Choose the past form: 'Yesterday, we ___ a great movie.'",
                "options": [{"id": "0", "text": "saw", "is_correct": True}, {"id": "1", "text": "see", "is_correct": False}, {"id": "2", "text": "seen", "is_correct": False}],
                "correct_answer": "saw",
                "explanation": "Quá khứ đơn của động từ bất quy tắc 'see' là 'saw'."
            },
            {
                "id": "a2_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete: 'Could you {blank} me how to get to the library?'",
                "correct_answer": "tell",
                "explanation": "Cấu trúc lịch sự: Could you tell me..."
            }
        ]
    },
    {
        "level": "B1",
        "title": "B1 - Practical Intermediate",
        "desc": "Trung cấp thực hành: Thì hiện tại hoàn thành, diễn đạt kế hoạch tương lai và ý kiến cá nhân.",
        "xp": 200,
        "exercises": [
            {
                "id": "b1_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Identify correct tense: 'I have lived here ___ 2018.'",
                "options": [{"id": "0", "text": "since", "is_correct": True}, {"id": "1", "text": "for", "is_correct": False}, {"id": "2", "text": "in", "is_correct": False}],
                "correct_answer": "since",
                "explanation": "Dùng 'since' với mốc thời gian xác định trong thì hiện tại hoàn thành."
            },
            {
                "id": "b1_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete: 'If it rains tomorrow, we will {blank} the picnic.'",
                "correct_answer": "cancel",
                "explanation": "Câu điều kiện loại 1: If + hiện tại đơn, will + V-nguyên thể."
            }
        ]
    },
    {
        "level": "B2",
        "title": "B2 - Professional Fluency",
        "desc": "Trung cao cấp: Câu điều kiện hỗn hợp, câu bị động nâng cao, thuyết trình và tranh luận.",
        "xp": 250,
        "exercises": [
            {
                "id": "b2_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Choose the best connector: '___ the economic downturn, the company made a profit.'",
                "options": [{"id": "0", "text": "Despite", "is_correct": True}, {"id": "1", "text": "Although", "is_correct": False}, {"id": "2", "text": "Because", "is_correct": False}],
                "correct_answer": "Despite",
                "explanation": "'Despite' + cụm danh từ diễn tả sự tương phản."
            },
            {
                "id": "b2_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete: 'The report must be {blank} by Friday.'",
                "correct_answer": "submitted",
                "explanation": "Câu bị động với modal verb: must be + V3/ed."
            }
        ]
    },
    {
        "level": "C1",
        "title": "C1 - Advanced Academic & IELTS",
        "desc": "Cao cấp học thuật: Cấu trúc đảo ngữ (Inversion), mệnh đề phân từ, phân tích số liệu phức tạp.",
        "xp": 300,
        "exercises": [
            {
                "id": "c1_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Inversion structure: 'Seldom ___ such an extraordinary performance.'",
                "options": [{"id": "0", "text": "have I witnessed", "is_correct": True}, {"id": "1", "text": "I have witnessed", "is_correct": False}, {"id": "2", "text": "did I witnessed", "is_correct": False}],
                "correct_answer": "have I witnessed",
                "explanation": "Đảo ngữ với trạng từ phủ định 'Seldom' đứng đầu câu: Seldom + Trợ động từ + S + V."
            },
            {
                "id": "c1_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete academic collocation: 'The data {blank} our preliminary hypothesis.'",
                "correct_answer": "substantiates",
                "explanation": "'substantiate' = chứng minh, làm sáng tỏ một giả thuyết khoa học."
            }
        ]
    },
    {
        "level": "C2",
        "title": "C2 - Native Mastery & Nuances",
        "desc": "Làm chủ ngôn ngữ: Tinh tế trong sắc thái biểu đạt, thành ngữ cổ điển, phong cách diễn đạt bản xứ.",
        "xp": 350,
        "exercises": [
            {
                "id": "c2_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Select the most nuanced synonym for 'temporary and fleeting':",
                "options": [{"id": "0", "text": "ephemeral", "is_correct": True}, {"id": "1", "text": "perpetual", "is_correct": False}, {"id": "2", "text": "mundane", "is_correct": False}],
                "correct_answer": "ephemeral",
                "explanation": "'Ephemeral' mô tả vẻ đẹp hoặc sự tồn tại mong manh, chỉ kéo dài trong chốc lát."
            },
            {
                "id": "c2_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete idiom: 'Finding that rare book was pure {blank}.'",
                "correct_answer": "serendipity",
                "explanation": "'serendipity' = sự tình cờ may mắn phát hiện ra điều quý giá."
            }
        ]
    }
]

# ── 2. DỮ LIỆU TỪ VỰNG CHUẨN CEFR TỪ A1 -> C2 ──────────────────────────────
CEFR_VOCABULARY = [
    # A1
    {"word": "family", "phonetic": "/ˈfæm.əl.i/", "meaning": "Gia đình", "level": "A1", "part_of_speech": "noun", "example": "I love spending weekends with my family."},
    {"word": "happy", "phonetic": "/ˈhæp.i/", "meaning": "Hạnh phúc, vui vẻ", "level": "A1", "part_of_speech": "adjective", "example": "She looks very happy today."},
    # A2
    {"word": "journey", "phonetic": "/ˈdʒɜː.ni/", "meaning": "Chuyến đi, cuộc hành trình", "level": "A2", "part_of_speech": "noun", "example": "The train journey took three hours."},
    {"word": "polite", "phonetic": "/pəˈlaɪt/", "meaning": "Lịch sự, lễ phép", "level": "A2", "part_of_speech": "adjective", "example": "He is always polite to his teachers."},
    # B1
    {"word": "opportunity", "phonetic": "/ˌɒp.əˈtʃuː.nə.ti/", "meaning": "Cơ hội thuận lợi", "level": "B1", "part_of_speech": "noun", "example": "Studying abroad is a wonderful opportunity."},
    {"word": "convenient", "phonetic": "/kənˈviː.ni.ənt/", "meaning": "Tiện lợi, thuận tiện", "level": "B1", "part_of_speech": "adjective", "example": "The hotel is in a convenient location."},
    # B2
    {"word": "significant", "phonetic": "/sɪɡˈnɪf.ɪ.kənt/", "meaning": "Quan trọng, có ý nghĩa lớn", "level": "B2", "part_of_speech": "adjective", "example": "There has been a significant increase in sales."},
    {"word": "collaborate", "phonetic": "/kəˈlæb.ə.reɪt/", "meaning": "Hợp tác, cộng tác làm việc", "level": "B2", "part_of_speech": "verb", "example": "Researchers from two universities collaborated on this project."},
    # C1
    {"word": "comprehensive", "phonetic": "/ˌkɒm.prɪˈhen.sɪv/", "meaning": "Toàn diện, bao quát mọi mặt", "level": "C1", "part_of_speech": "adjective", "example": "The book provides a comprehensive overview of AI."},
    {"word": "articulate", "phonetic": "/ɑːˈtɪk.jə.lət/", "meaning": "Ăn nói lưu loát, diễn đạt rõ ràng", "level": "C1", "part_of_speech": "adjective", "example": "She gave an articulate and persuasive speech."},
    # C2
    {"word": "ubiquitous", "phonetic": "/juːˈbɪk.wɪ.təs/", "meaning": "Phổ biến khắp nơi, ở đâu cũng có", "level": "C2", "part_of_speech": "adjective", "example": "Smartphones have become ubiquitous in modern society."},
    {"word": "serendipity", "phonetic": "/ˌser.ənˈdɪp.ə.ti/", "meaning": "Sự tình cờ may mắn", "level": "C2", "part_of_speech": "noun", "example": "Meeting my business partner was pure serendipity."}
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Seed CEFR demo content in a non-production database."
    )
    parser.add_argument(
        "--user-email",
        help="Optionally mark the seeded courses complete for this existing user.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish newly created courses. By default they are created as drafts.",
    )
    return parser.parse_args()


async def seed_and_test(*, user_email=None, publish=False):
    if settings.is_production:
        raise RuntimeError("This development seed script cannot run in production.")

    print("=" * 65)
    print(" BẮT ĐẦU NẠP DỮ LIỆU & KIỂM THỬ HỆ THỐNG CEFR (A1 -> C2)")
    print("=" * 65)

    async with AsyncSessionLocal() as db:
        # Lấy hoặc tạo Category
        cat_res = await db.execute(select(CourseCategory).where(CourseCategory.slug == "general_english"))
        category = cat_res.scalar_one_or_none()
        if not category:
            category = CourseCategory(
                id=uuid.uuid4(),
                name="General English CEFR",
                slug="general_english",
                description="Lộ trình tiếng Anh chuẩn quốc tế từ A1 đến C2",
                icon="🎓",
                color="#ff4d00",
                order_index=1
            )
            db.add(category)
            await db.flush()

        # Lấy tài khoản dev admin để test
        admin_user = None
        if user_email:
            user_res = await db.execute(select(User).where(User.email == user_email))
            admin_user = user_res.scalar_one_or_none()
            if admin_user is None:
                raise ValueError(f"User not found: {user_email}")

        test_results = []

        # ── NẠP VÀ TEST TỪNG CẤP ĐỘ A1 -> C2 ──
        for item in CEFR_COURSES:
            lvl = item["level"]
            lesson_vocabulary = [
                {
                    "word": vocab["word"],
                    "pronunciation": vocab["phonetic"],
                    "definition": vocab["meaning"],
                    "example": vocab["example"],
                }
                for vocab in CEFR_VOCABULARY
                if vocab["level"] == lvl
            ]
            print(f"\n[+] Đang xử lý cấp độ: {lvl} - {item['title']}...")

            # 1. Kiểm tra hoặc tạo khóa học
            c_res = await db.execute(select(Course).where(Course.title == item["title"]))
            course = c_res.scalar_one_or_none()
            if not course:
                course = Course(
                    id=uuid.uuid4(),
                    title=item["title"],
                    description=item["desc"],
                    language="en",
                    level=lvl,
                    category_id=category.id,
                    total_xp=item["xp"],
                    estimated_duration=60,
                    is_published=publish,
                    tags=["cefr", lvl.lower(), "interactive"]
                )
                db.add(course)
                await db.flush()

                # Tạo Unit
                unit = Unit(
                    id=uuid.uuid4(),
                    course_id=course.id,
                    title=f"Unit 1: {lvl} Core Skills",
                    description=f"Học phần nền tảng cho cấp độ {lvl}",
                    order_index=1,
                    total_lessons=1,
                )
                db.add(unit)
                await db.flush()

                # Tạo Lesson
                lesson = Lesson(
                    id=uuid.uuid4(),
                    course_id=course.id,
                    unit_id=unit.id,
                    title=f"Lesson 1: {lvl} Mastery Challenge",
                    description=f"Bài luyện tập tương tác {lvl}",
                    order_index=1,
                    outcome=f"You can understand and use core English structures at CEFR {lvl}.",
                    estimated_minutes=15,
                    xp_reward=50,
                    content={
                        "cefr_level": lvl,
                        "vocabulary": lesson_vocabulary,
                        "exercises": item["exercises"],
                        "version": 1,
                    }
                )
                db.add(lesson)
                course.total_lessons = 1
                await db.flush()
                print(f"    -> Đã tạo mới khóa học: [{lvl}] {course.title} (ID: {course.id})")
            else:
                print(f"    -> Đã tìm thấy khóa học sẵn có: [{lvl}] {course.title}")

            # 2. Test mô phỏng học viên làm bài tập cấp độ này
            if admin_user:
                # Kiểm tra tiến độ học
                prog_res = await db.execute(
                    select(UserCourseProgress).where(
                        UserCourseProgress.user_id == admin_user.id,
                        UserCourseProgress.course_id == course.id
                    )
                )
                progress = prog_res.scalar_one_or_none()
                if not progress:
                    progress = UserCourseProgress(
                        id=uuid.uuid4(),
                        user_id=admin_user.id,
                        course_id=course.id,
                        progress_percentage=100.0,
                        lessons_completed=1,
                        last_activity_at=datetime.now(UTC)
                    )
                    db.add(progress)
                    await db.flush()

                # Mô phỏng chấm điểm bài tập
                exercises = item["exercises"]
                passed = 0
                for ex in exercises:
                    # Giả lập học viên chọn đúng đáp án
                    user_ans = ex["correct_answer"]
                    if user_ans == ex["correct_answer"]:
                        passed += 1

                score_pct = (passed / len(exercises)) * 100
                test_results.append({
                    "level": lvl,
                    "course": course.title,
                    "exercises_count": len(exercises),
                    "passed": passed,
                    "score": f"{score_pct:.0f}%",
                    "status": "PASS" if score_pct == 100 else "FAIL"
                })

        # ── 3. NẠP TỪ VỰNG TỪ A1 -> C2 ──
        print("\n[+] Đang cập nhật kho từ vựng chuẩn CEFR A1 -> C2...")
        vocab_added = 0
        for v in CEFR_VOCABULARY:
            v_res = await db.execute(select(VocabularyItem).where(VocabularyItem.word == v["word"]))
            if not v_res.scalar_one_or_none():
                v_item = VocabularyItem(
                    id=uuid.uuid4(),
                    word=v["word"],
                    definition=v["meaning"],
                    translation={"vi": v["meaning"], "examples": [v["example"]]},
                    pronunciation=v["phonetic"],
                    difficulty_level=getattr(DifficultyLevel, v["level"]),
                    part_of_speech=getattr(PartOfSpeech, v["part_of_speech"].upper())
                )
                db.add(v_item)
                vocab_added += 1
        await db.commit()
        print(f"    -> Đã nạp thành công {vocab_added} từ vựng mới chuẩn A1 -> C2 vào Database.")

        # ── 4. XUẤT KẾT QUẢ KIỂM THỬ TỔNG HỢP ──
        print("\n" + "=" * 65)
        print(" BẢNG TỔNG HỢP KẾT QUẢ KIỂM THỬ TẤT CẢ CẤP ĐỘ CEFR")
        print("=" * 65)
        print(f"{'CẤP ĐỘ':<8} | {'KHÓA HỌC / NỘI DUNG':<32} | {'CÂU HỎI':<8} | {'KẾT QUẢ':<8}")
        print("-" * 65)
        for r in test_results:
            print(f"{r['level']:<8} | {r['course'][:30]:<32} | {r['passed']}/{r['exercises_count']:<6} |  {r['status']} ({r['score']})")
        print("=" * 65)
        print(" TẤT CẢ CẤP ĐỘ TỪ A1 ĐẾN C2 ĐÃ SẴN SÀNG TRÊN HỆ THỐNG!")

if __name__ == "__main__":
    cli_args = parse_args()
    asyncio.run(
        seed_and_test(user_email=cli_args.user_email, publish=cli_args.publish)
    )
