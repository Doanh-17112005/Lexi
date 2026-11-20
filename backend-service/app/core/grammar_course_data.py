"""Curated CEFR A1-C2 Grammar & Multi-Lesson Catalog with explicit provenance & QA status."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.cefr_vocabulary_data import (
    CEFR_LEVELS,
    PROVENANCE_AI_GENERATED,
    QA_STATUS_NEEDS_REVIEW,
)
from app.models.course import base_type_for, option_text

GRAMMAR_DIFFICULTY_TIERS = ("easy", "medium", "hard")
DIFFICULTY_TIER_TO_NUMERIC: dict[str, int] = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
}
TIER_POINTS: dict[str, int] = {
    "easy": 10,
    "medium": 15,
    "hard": 20,
}
_MOJIBAKE_MARKERS = ("\ufffd", "Ã¡", "Ã¢", "Ãª", "Ã´", "Ãº", "Ä‘", "áº", "á»", "Â\xa0", "â€")

# Canonical course metadata matching existing live courses (used only when
# seeding into an empty test DB where base courses are not yet present).
BASE_CEFR_COURSES: list[dict[str, Any]] = [
    {
        "level": "A1",
        "title": "A1 - English Foundations",
        "description": "Essential English foundations for beginners: greetings, core grammar, and everyday expressions.",
        "language": "en",
        "tags": ["cefr", "a1", "interactive"],
        "estimated_duration": 60,
        "unit1_title": "Unit 1: A1 Core Skills",
        "unit1_description": "Core starter practice at CEFR A1.",
        "lesson1_title": "Lesson 1: A1 Mastery Challenge",
        "lesson1_description": "Starter review of basic present verbs and everyday vocabulary.",
        "lesson1_outcome": "You can understand and use core English structures at CEFR A1.",
        "lesson1_exercises": [
            {
                "id": "a1_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Choose the correct form: 'She ___ to school every day.'",
                "options": [
                    {"id": "0", "text": "goes", "is_correct": True},
                    {"id": "1", "text": "go", "is_correct": False},
                    {"id": "2", "text": "going", "is_correct": False},
                ],
                "correct_answer": "goes",
                "explanation": "Chủ ngữ ngôi thứ ba số ít (She) đi với động từ thêm 'es' ở thì hiện tại đơn.",
            },
            {
                "id": "a1_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete the sentence: 'They {blank} two cats.'",
                "correct_answer": "have",
                "explanation": "Chủ ngữ 'They' đi với động từ 'have'.",
            },
        ],
    },
    {
        "level": "A2",
        "title": "A2 - Daily Communication",
        "description": "Build everyday fluency with past events, polite requests, and practical plans.",
        "language": "en",
        "tags": ["cefr", "a2", "interactive"],
        "estimated_duration": 75,
        "unit1_title": "Unit 1: A2 Core Skills",
        "unit1_description": "Core starter practice at CEFR A2.",
        "lesson1_title": "Lesson 1: A2 Mastery Challenge",
        "lesson1_description": "Starter review of simple past forms and polite requests.",
        "lesson1_outcome": "You can understand and use core English structures at CEFR A2.",
        "lesson1_exercises": [
            {
                "id": "a2_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Choose the past form: 'Yesterday, we ___ a great movie.'",
                "options": [
                    {"id": "0", "text": "saw", "is_correct": True},
                    {"id": "1", "text": "see", "is_correct": False},
                    {"id": "2", "text": "seen", "is_correct": False},
                ],
                "correct_answer": "saw",
                "explanation": "Quá khứ đơn của động từ bất quy tắc 'see' là 'saw'.",
            },
            {
                "id": "a2_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete: 'Could you {blank} me how to get to the library?'",
                "correct_answer": "tell",
                "explanation": "Cấu trúc lịch sự: Could you tell me...",
            },
        ],
    },
    {
        "level": "B1",
        "title": "B1 - Practical Intermediate",
        "description": "Handle independent work, travel, and connected discussions with clear grammar.",
        "language": "en",
        "tags": ["cefr", "b1", "interactive"],
        "estimated_duration": 90,
        "unit1_title": "Unit 1: B1 Core Skills",
        "unit1_description": "Core starter practice at CEFR B1.",
        "lesson1_title": "Lesson 1: B1 Mastery Challenge",
        "lesson1_description": "Starter review of time expressions and real conditionals.",
        "lesson1_outcome": "You can understand and use core English structures at CEFR B1.",
        "lesson1_exercises": [
            {
                "id": "b1_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Identify correct tense: 'I have lived here ___ 2018.'",
                "options": [
                    {"id": "0", "text": "since", "is_correct": True},
                    {"id": "1", "text": "for", "is_correct": False},
                    {"id": "2", "text": "in", "is_correct": False},
                ],
                "correct_answer": "since",
                "explanation": "Dùng 'since' với mốc thời gian xác định trong thì hiện tại hoàn thành.",
            },
            {
                "id": "b1_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete: 'If it rains tomorrow, we will {blank} the picnic.'",
                "correct_answer": "cancel",
                "explanation": "Câu điều kiện loại 1: If + hiện tại đơn, will + V-nguyên thể.",
            },
        ],
    },
    {
        "level": "B2",
        "title": "B2 - Professional Fluency",
        "description": "Communicate accurately in professional and academic situations using complex structures.",
        "language": "en",
        "tags": ["cefr", "b2", "interactive"],
        "estimated_duration": 100,
        "unit1_title": "Unit 1: B2 Core Skills",
        "unit1_description": "Core starter practice at CEFR B2.",
        "lesson1_title": "Lesson 1: B2 Mastery Challenge",
        "lesson1_description": "Starter review of discourse connectors and modal passives.",
        "lesson1_outcome": "You can understand and use core English structures at CEFR B2.",
        "lesson1_exercises": [
            {
                "id": "b2_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Choose the best connector: '___ the economic downturn, the company made a profit.'",
                "options": [
                    {"id": "0", "text": "Despite", "is_correct": True},
                    {"id": "1", "text": "Although", "is_correct": False},
                    {"id": "2", "text": "Because", "is_correct": False},
                ],
                "correct_answer": "Despite",
                "explanation": "'Despite' + cụm danh từ diễn tả sự tương phản.",
            },
            {
                "id": "b2_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete: 'The report must be {blank} by Friday.'",
                "correct_answer": "submitted",
                "explanation": "Câu bị động với modal verb: must be + V3/ed.",
            },
        ],
    },
    {
        "level": "C1",
        "title": "C1 - Advanced Academic & IELTS",
        "description": "Master inversion, participle clauses, and high-register academic cohesion.",
        "language": "en",
        "tags": ["cefr", "c1", "interactive"],
        "estimated_duration": 110,
        "unit1_title": "Unit 1: C1 Core Skills",
        "unit1_description": "Core starter practice at CEFR C1.",
        "lesson1_title": "Lesson 1: C1 Mastery Challenge",
        "lesson1_description": "Starter review of inversion and academic collocation.",
        "lesson1_outcome": "You can understand and use core English structures at CEFR C1.",
        "lesson1_exercises": [
            {
                "id": "c1_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Inversion structure: 'Seldom ___ such an extraordinary performance.'",
                "options": [
                    {"id": "0", "text": "have I witnessed", "is_correct": True},
                    {"id": "1", "text": "I have witnessed", "is_correct": False},
                    {"id": "2", "text": "did I witnessed", "is_correct": False},
                ],
                "correct_answer": "have I witnessed",
                "explanation": "Đảo ngữ với trạng từ phủ định 'Seldom' đứng đầu câu: Seldom + Trợ động từ + S + V.",
            },
            {
                "id": "c1_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete academic collocation: 'The data {blank} our preliminary hypothesis.'",
                "correct_answer": "substantiates",
                "explanation": "'substantiate' = chứng minh, làm sáng tỏ một giả thuyết khoa học.",
            },
        ],
    },
    {
        "level": "C2",
        "title": "C2 - Native Mastery & Nuances",
        "description": "Refine near-native precision, literary conditionals, and nuanced formal register.",
        "language": "en",
        "tags": ["cefr", "c2", "interactive"],
        "estimated_duration": 120,
        "unit1_title": "Unit 1: C2 Core Skills",
        "unit1_description": "Core starter practice at CEFR C2.",
        "lesson1_title": "Lesson 1: C2 Mastery Challenge",
        "lesson1_description": "Starter review of nuanced vocabulary and idiomatic precision.",
        "lesson1_outcome": "You can understand and use core English structures at CEFR C2.",
        "lesson1_exercises": [
            {
                "id": "c2_ex_1",
                "type": "multiple_choice",
                "ui_type": "multiple_choice",
                "question": "Select the most nuanced synonym for 'temporary and fleeting':",
                "options": [
                    {"id": "0", "text": "ephemeral", "is_correct": True},
                    {"id": "1", "text": "perpetual", "is_correct": False},
                    {"id": "2", "text": "mundane", "is_correct": False},
                ],
                "correct_answer": "ephemeral",
                "explanation": "'Ephemeral' mô tả vẻ đẹp hoặc sự tồn tại mong manh, chỉ kéo dài trong chốc lát.",
            },
            {
                "id": "c2_ex_2",
                "type": "fill_blank",
                "ui_type": "fill_in_the_blank",
                "question": "Complete idiom: 'Finding that rare book was pure {blank}.'",
                "correct_answer": "serendipity",
                "explanation": "'serendipity' = sự tình cờ may mắn phát hiện ra điều quý giá.",
            },
        ],
    },
]


def deterministic_uuid(namespace_key: str) -> uuid.UUID:
    """Return a deterministic UUID5 so seed upserts are repeatable across environments."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"lexilingo.me/content/{namespace_key}")


def _ex(
    ex_id: str,
    ui_type: str,
    question: str,
    correct_answer: str,
    explanation: str,
    *,
    tier: str,
    phase: str = "task_cycle",
    options: list[str] | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    base_type = base_type_for(ui_type)
    if base_type is None:
        raise ValueError(f"Unsupported ui_type: {ui_type}")
    payload: dict[str, Any] = {
        "id": ex_id,
        "type": base_type,
        "ui_type": ui_type,
        "phase": phase,
        "question": question,
        "correct_answer": correct_answer,
        "explanation": explanation,
        "difficulty": DIFFICULTY_TIER_TO_NUMERIC[tier],
        "difficulty_tier": tier,
        "points": TIER_POINTS[tier],
    }
    if options is not None:
        payload["options"] = list(options)
    if hint is not None:
        payload["hint"] = hint
    return payload


GRAMMAR_UNITS_AND_LESSONS: list[dict[str, Any]] = [
    # ══════════════════════════════════════════════════════════════════════════
    # A1 — Foundations
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "A1",
        "unit_slug": "unit-a1-grammar",
        "unit_title": "Unit 2: A1 Grammar Foundations",
        "unit_description": "Core present simple sentences, verb 'to be', articles, and basic nouns.",
        "unit_order_index": 2,
        "background_color": "#2563EB",
        "lessons": [
            {
                "slug": "a1-grammar-present-simple-to-be",
                "order_index": 1,
                "title": "Grammar 1: To Be & Present Simple",
                "description": "Use am/is/are and positive/negative Present Simple forms accurately.",
                "outcome": "You can introduce yourself and describe daily routines in Present Simple.",
                "estimated_minutes": 10,
                "xp_reward": 35,
                "pass_threshold": 70,
                "grammar": {
                    "slug": "grammar-a1-to-be-present-simple",
                    "title": "Verb 'To Be' & Present Simple Habits",
                    "level": "A1",
                    "topic": "tenses_and_verbs",
                    "summary": "Chia động từ 'to be' (am/is/are) và động từ thường ở thì hiện tại đơn cho thói quen hằng ngày.",
                    "content": (
                        "1. Động từ 'To Be' (am / is / are):\n"
                        "- I + am ('I am a designer.')\n"
                        "- He / She / It / danh từ số ít + is ('The office is quiet.')\n"
                        "- You / We / They / danh từ số nhiều + are ('They are ready.')\n\n"
                        "2. Thì Hiện tại đơn (Present Simple) với động từ thường:\n"
                        "- Diễn tả thói quen lặp lại hoặc sự thật hiển nhiên.\n"
                        "- I / You / We / They + V nguyên thể ('We study every evening.').\n"
                        "- He / She / It + V-s/-es ('She studies; he watches; it works.').\n"
                        "- Phủ định & Câu hỏi: dùng trợ động từ don't / doesn't / Do / Does + V nguyên thể (KHÔNG thêm -s vào động từ chính sau does/doesn't)."
                    ),
                    "grammar_points": [
                        "I am | He/She/It is | You/We/They are",
                        "I/You/We/They + V; He/She/It + V-s/-es",
                        "Sau do/does/don't/doesn't luôn dùng động từ nguyên thể",
                    ],
                    "examples": [
                        {
                            "sentence": "My sister is an engineer, and she works in Da Nang.",
                            "translation": "Chị gái tôi là kỹ sư và chị ấy làm việc tại Đà Nẵng.",
                        },
                        {
                            "sentence": "They do not drink coffee after dinner.",
                            "translation": "Họ không uống cà phê sau bữa tối.",
                        },
                        {
                            "sentence": "Does your brother take the bus to university?",
                            "translation": "Anh trai bạn có đi xe buýt đến trường đại học không?",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "a1_g1_ex1",
                        "multiple_choice",
                        "Choose the correct form of 'to be': 'My parents ___ at home right now.'",
                        "are",
                        "Đúng: 'My parents' là chủ ngữ số nhiều (họ) nên đi với 'are'. Sai: 'is' dùng cho số ít, 'am' chỉ đi với 'I', 'be' là nguyên thể.",
                        tier="easy",
                        phase="pre_task",
                        options=["am", "is", "are", "be"],
                        hint="Count whether 'parents' is singular or plural.",
                    ),
                    _ex(
                        "a1_g1_ex2",
                        "true_or_false",
                        "True or False: 'Does he plays football on Sundays?' is grammatically correct.",
                        "False",
                        "Sai ngữ pháp (False): trong câu hỏi có trợ động từ 'Does', động từ chính phải trở về nguyên thể 'play', không thêm '-s'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Check the main verb form after 'Does'.",
                    ),
                    _ex(
                        "a1_g1_ex3",
                        "fill_in_the_blank",
                        "Complete the sentence using 'study': 'Minh {blank} English for thirty minutes every morning.'",
                        "studies",
                        "Đúng: 'Minh' là ngôi thứ ba số ít và 'every morning' chỉ thói quen. Động từ 'study' kết thúc bằng phụ âm + y nên đổi thành 'studies'.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Use third-person singular of 'study'.",
                    ),
                    _ex(
                        "a1_g1_ex4",
                        "dialogue_completion",
                        "A: Does your team meet on Mondays? B: No, we {blank}. We meet on Tuesdays.",
                        "don't",
                        "Đúng: chủ ngữ câu trả lời là 'we', nên câu trả lời ngắn phủ định ở hiện tại đơn là 'don't' (hoặc 'do not'). Sai: 'doesn't' chỉ dùng cho he/she/it; 'aren't' dùng với tính từ/danh từ/V-ing.",
                        tier="medium",
                        phase="task_cycle",
                        options=["don't", "doesn't", "aren't", "isn't"],
                        hint="Match the auxiliary verb to 'we' and the main verb 'meet'.",
                    ),
                    _ex(
                        "a1_g1_ex5",
                        "grammar_correction",
                        "Choose the corrected sentence for: 'She don't likes spicy food.'",
                        "She doesn't like spicy food.",
                        "Đúng: 'She' cần trợ động từ phủ định 'doesn't', và sau 'doesn't' động từ 'like' giữ nguyên thể không thêm '-s'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "She doesn't like spicy food.",
                            "She doesn't likes spicy food.",
                            "She don't like spicy food.",
                            "She isn't like spicy food.",
                        ],
                        hint="Fix both the auxiliary verb and the main verb ending.",
                    ),
                    _ex(
                        "a1_g1_ex6",
                        "fill_in_the_blank",
                        "Complete the Present Simple question: 'Where {blank} your cousins live?'",
                        "do",
                        "Đúng: 'your cousins' là chủ ngữ số nhiều (they) và động từ chính là 'live', nên câu hỏi dùng trợ động từ 'do'. Không dùng 'are' vì 'live' là động từ thường ở thì hiện tại đơn.",
                        tier="hard",
                        phase="language_focus",
                        hint="Is 'your cousins' singular or plural?",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Which sentence uses 'to be' correctly?",
                        "options": [
                            "I is ready for the lesson.",
                            "They are very friendly neighbors.",
                            "She am an art teacher.",
                            "We is in the library.",
                        ],
                        "answer": "They are very friendly neighbors.",
                        "explanation": "'They' takes 'are'. 'I' takes 'am', 'She' takes 'is', and 'We' takes 'are'.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Choose the correct Present Simple form: 'The train ___ at 6:30 a.m. daily.'",
                        "options": ["leave", "leaves", "leaving", "is leave"],
                        "answer": "leaves",
                        "explanation": "'The train' is singular (it), so Present Simple requires '-s': 'leaves'.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Select the grammatically accurate negative sentence:",
                        "options": [
                            "My brother doesn't watches television.",
                            "My brother don't watch television.",
                            "My brother doesn't watch television.",
                            "My brother isn't watch television.",
                        ],
                        "answer": "My brother doesn't watch television.",
                        "explanation": "Third-person singular uses 'doesn't' followed by the bare infinitive 'watch'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
            {
                "slug": "a1-grammar-articles-and-nouns",
                "order_index": 2,
                "title": "Grammar 2: Articles (a / an / the) & Plurals",
                "description": "Choose between a, an, the, or zero article and form basic plural nouns.",
                "outcome": "You can refer to specific and non-specific everyday objects accurately.",
                "estimated_minutes": 10,
                "xp_reward": 35,
                "pass_threshold": 70,
                "grammar": {
                    "slug": "grammar-a1-articles-and-plurals",
                    "title": "Articles (a / an / the) & Countable Plurals",
                    "level": "A1",
                    "topic": "articles_and_nouns",
                    "summary": "Phân biệt mạo từ bất định a/an theo âm đầu, mạo từ xác định the, và danh từ số nhiều cơ bản.",
                    "content": (
                        "1. Mạo từ bất định a / an (chỉ dùng với danh từ đếm được số ít chưa xác định):\n"
                        "- Dùng 'a' trước ÂM phụ âm: a book, a university (/juː-/).\n"
                        "- Dùng 'an' trước ÂM nguyên âm: an apple, an hour (/aʊ-/ vì 'h' câm).\n\n"
                        "2. Mạo từ xác định 'the':\n"
                        "- Dùng khi người nói và người nghe đều biết rõ đối tượng cụ thể ('Close the front door, please.').\n"
                        "- Không dùng a/an với danh từ số nhiều hoặc khái niệm chung không đếm được.\n\n"
                        "3. Danh từ số nhiều cơ bản:\n"
                        "- Thêm -s (books), -es sau s/sh/ch/x (boxes, watches), và dạng bất quy tắc quen thuộc (child -> children, person -> people)."
                    ),
                    "grammar_points": [
                        "'a' vs 'an' phụ thuộc vào ÂM đầu tiên khi phát âm, không chỉ chữ cái viết",
                        "Dùng 'the' cho vật cụ thể đã xác định với cả hai người",
                        "Không dùng 'a/an' trước danh từ số nhiều",
                    ],
                    "examples": [
                        {
                            "sentence": "She waited for an hour before the museum opened.",
                            "translation": "Cô ấy đã đợi một giờ đồng hồ trước khi bảo tàng mở cửa.",
                        },
                        {
                            "sentence": "He studies at a university near the central station.",
                            "translation": "Anh ấy học tại một trường đại học gần nhà ga trung tâm.",
                        },
                        {
                            "sentence": "The children put their books into two boxes.",
                            "translation": "Lũ trẻ cất sách của mình vào hai cái hộp.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "a1_g2_ex1",
                        "multiple_choice",
                        "Choose the right article: 'I usually eat ___ orange after lunch.'",
                        "an",
                        "Đúng: 'orange' bắt đầu bằng âm nguyên âm /ɒ/ và là danh từ đếm được số ít chưa xác định nên dùng 'an'.",
                        tier="easy",
                        phase="pre_task",
                        options=["a", "an", "the", "these"],
                        hint="Listen to the first sound of 'orange'.",
                    ),
                    _ex(
                        "a1_g2_ex2",
                        "true_or_false",
                        "True or False: 'We saw two childrens in the park.' is grammatically correct.",
                        "False",
                        "Sai (False): số nhiều của 'child' là 'children' (dạng bất quy tắc), không thêm '-s' thành 'childrens'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="'Child' has an irregular plural form.",
                    ),
                    _ex(
                        "a1_g2_ex3",
                        "multiple_choice",
                        "Select the correct phrase: 'My brother works as ___ honest mechanic.'",
                        "an",
                        "Đúng: chữ 'h' trong 'honest' là âm câm (/ˈɒn.ɪst/), âm đầu tiên là nguyên âm nên dùng 'an'.",
                        tier="medium",
                        phase="task_cycle",
                        options=["a", "an", "those", "many"],
                        hint="Pronounce 'honest' aloud: is the 'h' pronounced?",
                    ),
                    _ex(
                        "a1_g2_ex4",
                        "fill_in_the_blank",
                        "Complete with one article: 'Please turn off {blank} kitchen light before sleeping.'",
                        "the",
                        "Đúng: 'the kitchen light' chỉ chiếc đèn cụ thể trong bếp mà cả người nói và người nghe đều biết rõ.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Both speakers know which specific light is meant.",
                    ),
                    _ex(
                        "a1_g2_ex5",
                        "grammar_correction",
                        "Choose the correct sentence for: 'She wants to study at an university in Canada.'",
                        "She wants to study at a university in Canada.",
                        "Đúng: 'university' phát âm bắt đầu bằng âm phụ âm /j/ (/ˌjuː.nɪˈvɜː.sə.ti/), vì vậy phải dùng 'a university', không dùng 'an'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "She wants to study at a university in Canada.",
                            "She wants to study at an university in Canada.",
                            "She wants to study at universitys in Canada.",
                            "She wants to study at the a university in Canada.",
                        ],
                        hint="Focus on the initial /j/ sound of 'university'.",
                    ),
                    _ex(
                        "a1_g2_ex6",
                        "fill_in_the_blank",
                        "Write the irregular plural of 'person': 'Five {blank} are waiting in line.'",
                        "people",
                        "Đúng: dạng số nhiều thông dụng nhất của 'person' trong giao tiếp hằng ngày là 'people' (không dùng 'persons' ở A1).",
                        tier="hard",
                        phase="language_focus",
                        hint="Common irregular plural noun.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Pick the correct option: 'We need ___ umbrella because it is raining.'",
                        "options": ["a", "an", "many", "two"],
                        "answer": "an",
                        "explanation": "'Umbrella' begins with the vowel sound /ʌ/, so singular indefinite requires 'an'.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Why do we say 'an hour' instead of 'a hour'?",
                        "options": [
                            "Because 'hour' is plural",
                            "Because the 'h' is silent and it starts with a vowel sound",
                            "Because 'hour' is an uncountable noun",
                            "Because 'hour' starts with a consonant sound",
                        ],
                        "answer": "Because the 'h' is silent and it starts with a vowel sound",
                        "explanation": "Article choice (a/an) depends on pronunciation (/aʊər/), not spelling.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Which sentence uses articles accurately?",
                        "options": [
                            "He bought an uniform for his new job.",
                            "Look at a moon tonight; it is bright.",
                            "She gave me a useful piece of advice.",
                            "They live in the small apartment near an park.",
                        ],
                        "answer": "She gave me a useful piece of advice.",
                        "explanation": "'Useful' starts with the consonant sound /j/, so 'a useful piece' is correct.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    # A2 — Daily Communication
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "A2",
        "unit_slug": "unit-a2-grammar",
        "unit_title": "Unit 2: A2 Grammar Expansion",
        "unit_description": "Talk about past events, comparisons, and future plans naturally.",
        "unit_order_index": 2,
        "background_color": "#0D9488",
        "lessons": [
            {
                "slug": "a2-grammar-past-simple",
                "order_index": 1,
                "title": "Grammar 1: Past Simple (Regular & Irregular)",
                "description": "Narrate completed past actions with regular -ed and irregular verbs.",
                "outcome": "You can describe completed trips, weekends, and past events accurately.",
                "estimated_minutes": 12,
                "xp_reward": 40,
                "pass_threshold": 70,
                "grammar": {
                    "slug": "grammar-a2-past-simple",
                    "title": "Past Simple: Regular, Irregular & Questions",
                    "level": "A2",
                    "topic": "past_tenses",
                    "summary": "Thì Quá khứ đơn diễn tả hành động đã xảy ra và kết thúc hoàn toàn trong quá khứ.",
                    "content": (
                        "1. Cách dùng: Diễn tả sự việc đã hoàn tất tại một thời điểm xác định trong quá khứ (yesterday, last week, in 2022, two hours ago).\n\n"
                        "2. Dạng khẳng định:\n"
                        "- Động từ có quy tắc: thêm -ed (worked, stopped, studied).\n"
                        "- Động từ bất quy tắc: dùng cột 2 (go -> went, buy -> bought, catch -> caught, write -> wrote).\n"
                        "- 'To be' quá khứ: I/He/She/It -> was; You/We/They -> were.\n\n"
                        "3. Dạng phủ định & Nghi vấn:\n"
                        "- Dùng didn't / Did + S + V nguyên thể ('Did you catch the bus? — No, I didn't catch it.').\n"
                        "- Tuyệt đối KHÔNG chia V2/-ed lần nữa khi đã có 'did' hoặc 'didn't'."
                    ),
                    "grammar_points": [
                        "Khẳng định: V-ed hoặc V2 (bất quy tắc); 'to be' dùng was / were",
                        "Phủ định: didn't + V nguyên thể; wasn't / weren't (không dùng didn't be)",
                        "Câu hỏi: Did + S + V nguyên thể?",
                    ],
                    "examples": [
                        {
                            "sentence": "We caught the early train and arrived before nine.",
                            "translation": "Chúng tôi đã bắt chuyến tàu sớm và đến nơi trước chín giờ.",
                        },
                        {
                            "sentence": "She didn't send the invitation yesterday because she was busy.",
                            "translation": "Cô ấy đã không gửi lời mời hôm qua vì bận.",
                        },
                        {
                            "sentence": "Were your colleagues satisfied with the presentation?",
                            "translation": "Đồng nghiệp của bạn có hài lòng với bài thuyết trình không?",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "a2_g1_ex1",
                        "multiple_choice",
                        "Choose the past simple form: 'Last weekend, we ___ our grandparents in Hue.'",
                        "visited",
                        "Đúng: 'Last weekend' là mốc thời gian quá khứ đã kết thúc; 'visit' là động từ có quy tắc nên thêm '-ed' thành 'visited'.",
                        tier="easy",
                        phase="pre_task",
                        options=["visit", "visits", "visited", "visiting"],
                        hint="Look at the time marker 'Last weekend'.",
                    ),
                    _ex(
                        "a2_g1_ex2",
                        "true_or_false",
                        "True or False: 'Where did you went during the holiday?' is grammatically correct.",
                        "False",
                        "Sai (False): đã có trợ động từ 'did' đứng trước chủ ngữ nên động từ chính phải ở dạng nguyên thể 'go', không dùng 'went'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Check the verb after 'did'.",
                    ),
                    _ex(
                        "a2_g1_ex3",
                        "fill_in_the_blank",
                        "Complete with the irregular past form of 'buy': 'Lan {blank} a new backpack before her trip.'",
                        "bought",
                        "Đúng: quá khứ đơn của động từ bất quy tắc 'buy' là 'bought'. Sai nếu viết 'buyed'.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Irregular past tense of 'buy'.",
                    ),
                    _ex(
                        "a2_g1_ex4",
                        "dialogue_completion",
                        "A: Why were you late this morning? B: Because the traffic {blank} terrible.",
                        "was",
                        "Đúng: 'the traffic' là danh từ không đếm được đi với động từ số ít quá khứ 'was'. Sai: 'did' không đi trực tiếp với tính từ 'terrible'.",
                        tier="medium",
                        phase="task_cycle",
                        options=["was", "were", "did", "is"],
                        hint="'Traffic' is uncountable and singular in the past.",
                    ),
                    _ex(
                        "a2_g1_ex5",
                        "grammar_correction",
                        "Choose the corrected sentence for: 'He didn't wrote any notes during the meeting.'",
                        "He didn't write any notes during the meeting.",
                        "Đúng: sau 'didn't', động từ chính phải ở dạng nguyên thể 'write', không chia cột 2 'wrote'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "He didn't write any notes during the meeting.",
                            "He didn't wrote any notes during the meeting.",
                            "He wasn't write any notes during the meeting.",
                            "He didn't writes any notes during the meeting.",
                        ],
                        hint="Never combine 'didn't' with a past-tense verb form.",
                    ),
                    _ex(
                        "a2_g1_ex6",
                        "fill_in_the_blank",
                        "Complete the Past Simple negative question with one word: 'Why {blank} they at the station on time yesterday?'",
                        "weren't",
                        "Đúng: chủ ngữ số nhiều 'they' + cụm trạng ngữ 'at the station' trong quá khứ ('yesterday') cần dạng phủ định của 'were' là 'weren't' (không dùng 'didn't' khi không có động từ thường).",
                        tier="hard",
                        phase="language_focus",
                        hint="Contraction of 'were not'.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Choose the irregular past simple form of 'take':",
                        "options": ["taked", "took", "taken", "taking"],
                        "answer": "took",
                        "explanation": "'Take -> took -> taken'. Past simple uses 'took'.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Select the correct question: '___ the parcel arrive safely yesterday?'",
                        "options": ["Was", "Did", "Does", "Were"],
                        "answer": "Did",
                        "explanation": "Because 'arrive' is an action verb in base form, form the past question with 'Did'.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Which sentence is completely accurate in Past Simple?",
                        "options": [
                            "She didn't told anyone about the plan.",
                            "Did your manager approved the budget?",
                            "Neither of the trains stopped at that small town.",
                            "We was surprised by the sudden storm.",
                        ],
                        "answer": "Neither of the trains stopped at that small town.",
                        "explanation": "'Stop' doubles the final consonant ('stopped'); the other options misuse 'did/didn't' or 'was/were'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
            {
                "slug": "a2-grammar-comparatives-and-going-to",
                "order_index": 2,
                "title": "Grammar 2: Comparatives & 'Be Going To'",
                "description": "Compare options with -er/more and express clear future intentions.",
                "outcome": "You can compare prices or places and explain planned future actions.",
                "estimated_minutes": 12,
                "xp_reward": 40,
                "pass_threshold": 70,
                "grammar": {
                    "slug": "grammar-a2-comparatives-future-plans",
                    "title": "Comparatives, Superlatives & Future Plans (be going to)",
                    "level": "A2",
                    "topic": "comparison_and_future",
                    "summary": "So sánh hơn/nhất với tính từ ngắn, dài, bất quy tắc và diễn tả kế hoạch tương lai bằng 'be going to'.",
                    "content": (
                        "1. So sánh hơn (Comparatives) & So sánh nhất (Superlatives):\n"
                        "- Tính từ ngắn (1 âm tiết, hoặc 2 âm tiết tận cùng -y): faster than / the fastest; happier than / the happiest.\n"
                        "- Tính từ dài (2+ âm tiết): more comfortable than / the most comfortable.\n"
                        "- Bất quy tắc: good -> better -> best; bad -> worse -> worst; far -> farther/further.\n"
                        "- Tránh lỗi kép: KHÔNG viết 'more better' hoặc 'more faster'.\n\n"
                        "2. Tương lai với 'be going to':\n"
                        "- Cấu trúc: am / is / are + going to + V nguyên thể.\n"
                        "- Diễn tả dự định đã có từ trước ('We are going to visit Hoi An next month.') hoặc dự đoán có dấu hiệu rõ ràng ở hiện tại ('Look at those dark clouds—it is going to rain.')."
                    ),
                    "grammar_points": [
                        "Ngắn: -er / the -est | Dài: more ... / the most ...",
                        "Không ghép 'more' với '-er' hay 'better'",
                        "am/is/are + going to + V nguyên thể cho kế hoạch đã dự định",
                    ],
                    "examples": [
                        {
                            "sentence": "Taking the morning train is faster and more comfortable than driving.",
                            "translation": "Đi tàu buổi sáng nhanh hơn và thoải mái hơn lái xe.",
                        },
                        {
                            "sentence": "This route is the best choice during rush hour.",
                            "translation": "Tuyến đường này là lựa chọn tốt nhất vào giờ cao điểm.",
                        },
                        {
                            "sentence": "Are you going to renew your passport before September?",
                            "translation": "Bạn có định gia hạn hộ chiếu trước tháng Chín không?",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "a2_g2_ex1",
                        "multiple_choice",
                        "Choose the comparative: 'This hotel room is ___ than the one we stayed in last year.'",
                        "cleaner",
                        "Đúng: 'clean' là tính từ 1 âm tiết nên chuyển thành 'cleaner' trước 'than'. Không dùng 'more clean'.",
                        tier="easy",
                        phase="pre_task",
                        options=["clean", "cleaner", "more clean", "cleanest"],
                        hint="Short one-syllable adjective before 'than'.",
                    ),
                    _ex(
                        "a2_g2_ex2",
                        "true_or_false",
                        "True or False: 'We going to launch the new class next week.' is grammatically complete.",
                        "False",
                        "Sai (False): cấu trúc bắt buộc phải có động từ 'to be' ('We are going to launch...').",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Check if 'to be' is present before 'going to'.",
                    ),
                    _ex(
                        "a2_g2_ex3",
                        "fill_in_the_blank",
                        "Complete with the irregular superlative of 'good': 'July is the {blank} month to visit this island.'",
                        "best",
                        "Đúng: so sánh nhất bất quy tắc của 'good' là 'the best'. Không dùng 'goodest'.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Irregular superlative form of 'good'.",
                    ),
                    _ex(
                        "a2_g2_ex4",
                        "collocation_choice",
                        "Select the natural comparison: 'Public buses are ___ for long commutes.'",
                        "more convenient",
                        "Đúng: 'convenient' có 3 âm tiết nên dùng 'more convenient'. Sai: không thêm '-er' hay ghép 'more ...-er'.",
                        tier="medium",
                        phase="task_cycle",
                        options=[
                            "more convenient",
                            "convenienter",
                            "more convenienter",
                            "most convenient than",
                        ],
                        hint="Count syllables in 'convenient'.",
                    ),
                    _ex(
                        "a2_g2_ex5",
                        "grammar_correction",
                        "Choose the corrected sentence for: 'Her explanation is much more clearer than the old guide.'",
                        "Her explanation is much clearer than the old guide.",
                        "Đúng: 'clear' là tính từ ngắn nên dùng 'clearer'; có thể nhấn mạnh bằng 'much clearer', KHÔNG dùng dạng kép 'more clearer'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "Her explanation is much clearer than the old guide.",
                            "Her explanation is much more clearer than the old guide.",
                            "Her explanation is more clearer than the old guide.",
                            "Her explanation is clearest than the old guide.",
                        ],
                        hint="Remove double comparison ('more' + '-er').",
                    ),
                    _ex(
                        "a2_g2_ex6",
                        "dialogue_completion",
                        "A: Look at the grey sky! B: Yes, I think it {blank} rain soon.",
                        "is going to",
                        "Đúng: dự đoán dựa trên dấu hiệu nhìn thấy ngay lúc nói ('grey sky') dùng 'be going to': 'it is going to rain'.",
                        tier="hard",
                        phase="language_focus",
                        options=["is going to", "going to", "was going", "are going to"],
                        hint="Subject 'it' + evidence-based prediction.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: 'Today's weather is ___ than yesterday's.'",
                        "options": ["worse", "badder", "more bad", "worst"],
                        "answer": "worse",
                        "explanation": "The irregular comparative of 'bad' is 'worse' (superlative: 'worst').",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Which sentence expresses a prior plan correctly?",
                        "options": [
                            "She is going to learn Japanese next semester.",
                            "She going to learn Japanese next semester.",
                            "She is go to learn Japanese next semester.",
                            "She are going to learn Japanese next semester.",
                        ],
                        "answer": "She is going to learn Japanese next semester.",
                        "explanation": "Use 'is going to + base verb' with singular third-person subject 'She'.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Choose the accurate sentence avoiding double comparison:",
                        "options": [
                            "This tablet is far more lighter than my laptop.",
                            "This tablet is far lighter than my laptop.",
                            "This tablet is lightest than my laptop.",
                            "This tablet is the lighter than my laptop.",
                        ],
                        "answer": "This tablet is far lighter than my laptop.",
                        "explanation": "Use 'far + -er' to intensify short adjectives; never combine 'more' with '-er'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    # B1 — Practical Intermediate
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "B1",
        "unit_slug": "unit-b1-grammar",
        "unit_title": "Unit 2: B1 Grammar Control",
        "unit_description": "Connect past to present, express obligations, and frame real conditions.",
        "unit_order_index": 2,
        "background_color": "#059669",
        "lessons": [
            {
                "slug": "b1-grammar-present-perfect",
                "order_index": 1,
                "title": "Grammar 1: Present Perfect (since / for / yet)",
                "description": "Contrast Present Perfect with Past Simple using since, for, already, and yet.",
                "outcome": "You can discuss life experience and unfinished durations cleanly.",
                "estimated_minutes": 12,
                "xp_reward": 45,
                "pass_threshold": 75,
                "grammar": {
                    "slug": "grammar-b1-present-perfect",
                    "title": "Present Perfect vs Past Simple (since / for / already / yet)",
                    "level": "B1",
                    "topic": "perfect_tenses",
                    "summary": "Phân biệt Hiện tại hoàn thành với Quá khứ đơn và dùng chuẩn since, for, already, yet.",
                    "content": (
                        "1. Cấu trúc: have / has + V3/ed.\n\n"
                        "2. Khi nào dùng Present Perfect thay vì Past Simple:\n"
                        "- Hành động bắt đầu trong quá khứ và vẫn tiếp diễn tới hiện tại ('She has lived in Hue for five years.').\n"
                        "- Hành động vừa xảy ra hoặc có kết quả rõ ở hiện tại ('I have already sent the invoice.').\n"
                        "- Trải nghiệm không nêu mốc thời gian cụ thể ('Have you ever visited Hanoi?').\n"
                        "- Nếu có mốc thời gian đã đóng (yesterday, in 2020, last night) -> BẮT BUỘC dùng Past Simple.\n\n"
                        "3. Trạng từ đi kèm:\n"
                        "- 'since' + mốc thời gian (since 2019, since Monday).\n"
                        "- 'for' + khoảng thời gian (for three years, for two hours).\n"
                        "- 'already' trong câu khẳng định; 'yet' cuối câu phủ định hoặc câu hỏi."
                    ),
                    "grammar_points": [
                        "have/has + V3/ed (KHÔNG dùng thì này với 'yesterday' hoặc 'last year')",
                        "since + mốc bắt đầu | for + khoảng thời gian",
                        "already (khẳng định) | yet (phủ định & câu hỏi)",
                    ],
                    "examples": [
                        {
                            "sentence": "Our engineering team has collaborated with this partner since 2021.",
                            "translation": "Đội kỹ thuật của chúng tôi đã hợp tác với đối tác này từ năm 2021.",
                        },
                        {
                            "sentence": "Has the client reviewed the revised contract yet?",
                            "translation": "Khách hàng đã xem xét bản hợp đồng sửa đổi chưa?",
                        },
                        {
                            "sentence": "We discussed the proposal yesterday, and we have already updated the timeline.",
                            "translation": "Chúng tôi đã thảo luận đề xuất hôm qua và hiện đã cập nhật xong tiến độ.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "b1_g1_ex1",
                        "multiple_choice",
                        "Choose the correct time preposition: 'Nam has worked at this hospital ___ six years.'",
                        "for",
                        "Đúng: 'six years' là một khoảng thời gian (duration), nên dùng 'for'. 'Since' chỉ dùng với mốc bắt đầu.",
                        tier="easy",
                        phase="pre_task",
                        options=["since", "for", "during", "from"],
                        hint="'Six years' is a length of time, not a starting date.",
                    ),
                    _ex(
                        "b1_g1_ex2",
                        "true_or_false",
                        "True or False: 'I have finished the report yesterday evening.' is grammatically standard.",
                        "False",
                        "Sai (False): 'yesterday evening' là mốc thời gian quá khứ đã khép kín, nên phải dùng Past Simple ('I finished...'), không dùng Present Perfect.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Check whether 'yesterday evening' is a finished past time.",
                    ),
                    _ex(
                        "b1_g1_ex3",
                        "fill_in_the_blank",
                        "Complete with the past participle of 'write': 'She has {blank} three articles about renewable energy.'",
                        "written",
                        "Đúng: phân từ hai (V3) của 'write' là 'written'. Sai nếu dùng 'wrote' (V2).",
                        tier="medium",
                        phase="task_cycle",
                        hint="Past participle (V3) of 'write'.",
                    ),
                    _ex(
                        "b1_g1_ex4",
                        "dialogue_completion",
                        "A: Would you like to watch that documentary tonight? B: Thanks, but I have {blank} seen it twice.",
                        "already",
                        "Đúng: trong câu khẳng định diễn tả việc đã làm sớm hơn dự kiến, dùng 'already' đặt giữa 'have/has' và V3. Không dùng 'yet' trong câu khẳng định kiểu này.",
                        tier="medium",
                        phase="task_cycle",
                        options=["already", "yet", "since", "ago"],
                        hint="Use the adverb suitable for affirmative statements.",
                    ),
                    _ex(
                        "b1_g1_ex5",
                        "grammar_correction",
                        "Select the accurate correction for: 'How long are you knowing your current manager?'",
                        "How long have you known your current manager?",
                        "Đúng: 'know' là động từ trạng thái (không chia tiếp diễn) và hỏi về khoảng thời gian kéo dài tới hiện tại, nên dùng Hiện tại hoàn thành: 'How long have you known...?'",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "How long have you known your current manager?",
                            "How long did you knew your current manager?",
                            "How long are you known your current manager?",
                            "How long have you been knowing your current manager?",
                        ],
                        hint="'Know' is a stative verb measuring duration up to now.",
                    ),
                    _ex(
                        "b1_g1_ex6",
                        "fill_in_the_blank",
                        "Complete with one word: 'Has the delivery driver arrived {blank}?'",
                        "yet",
                        "Đúng: trong câu hỏi ở thì Hiện tại hoàn thành để hỏi việc mong đợi đã xảy ra chưa, dùng 'yet' ở cuối câu.",
                        tier="hard",
                        phase="language_focus",
                        hint="Common word placed at the end of Present Perfect questions.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: 'We haven't received their reply ___.'",
                        "options": ["already", "yet", "just", "since"],
                        "answer": "yet",
                        "explanation": "Use 'yet' at the end of negative sentences and questions in Present Perfect.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Choose the accurate tense contrast:",
                        "options": [
                            "She has joined the club two years ago.",
                            "She joined the club since 2024.",
                            "She joined the club two years ago and has stayed active since then.",
                            "She has been join the club for two years.",
                        ],
                        "answer": "She joined the club two years ago and has stayed active since then.",
                        "explanation": "'Two years ago' takes Past Simple ('joined'), while 'since then' takes Present Perfect ('has stayed').",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Which question correctly asks about life experience up to now?",
                        "options": [
                            "Did you ever attended an international workshop?",
                            "Have you ever attended an international workshop?",
                            "Are you ever attending an international workshop?",
                            "Have you ever attend an international workshop?",
                        ],
                        "answer": "Have you ever attended an international workshop?",
                        "explanation": "Experience up to the present uses 'Have/Has + S + ever + V3/ed?'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
            {
                "slug": "b1-grammar-first-conditional-and-modals",
                "order_index": 2,
                "title": "Grammar 2: First Conditional & Obligation Modals",
                "description": "Use Conditional Type 1 and contrast must, mustn't, have to, and don't have to.",
                "outcome": "You can state likely future consequences and rules or lack of necessity.",
                "estimated_minutes": 12,
                "xp_reward": 45,
                "pass_threshold": 75,
                "grammar": {
                    "slug": "grammar-b1-conditional-1-modals",
                    "title": "First Conditional & Obligation Modals (must / have to)",
                    "level": "B1",
                    "topic": "conditionals_and_modals",
                    "summary": "Câu điều kiện loại 1 cho tình huống có thật ở tương lai và phân biệt nghĩa giữa mustn't với don't have to.",
                    "content": (
                        "1. Câu điều kiện loại 1 (First Conditional):\n"
                        "- Diễn tả kết quả có khả năng xảy ra ở tương lai nếu điều kiện có thật.\n"
                        "- Cấu trúc: If + Hiện tại đơn, S + will / can / may + V nguyên thể.\n"
                        "- Lưu ý: KHÔNG dùng 'will' trong mệnh đề 'If' ('If it rains...', không viết 'If it will rain...').\n\n"
                        "2. Động từ khuyết thiếu chỉ nghĩa vụ & sự cần thiết:\n"
                        "- must / have to + V: phải làm gì (nghĩa vụ nội tại hoặc quy định bên ngoài).\n"
                        "- mustn't + V: CẤM làm gì ('Visitors mustn't enter the lab without badges.').\n"
                        "- don't / doesn't have to + V: KHÔNG CẦN thiết phải làm gì ('You don't have to print the ticket; digital copies are fine.')."
                    ),
                    "grammar_points": [
                        "If + Present Simple, will + V (không đặt 'will' ngay sau 'if')",
                        "mustn't = bị cấm | don't have to = không bắt buộc (hai nghĩa hoàn toàn khác nhau)",
                        "should + V để khuyên bảo hợp lý",
                    ],
                    "examples": [
                        {
                            "sentence": "If you submit the application before noon, the office will process it today.",
                            "translation": "Nếu bạn nộp đơn trước trưa, văn phòng sẽ xử lý trong hôm nay.",
                        },
                        {
                            "sentence": "You don't have to bring cash because every counter accepts cards.",
                            "translation": "Bạn không cần mang tiền mặt vì quầy nào cũng nhận thẻ.",
                        },
                        {
                            "sentence": "Passengers mustn't leave luggage unattended in the terminal.",
                            "translation": "Hành khách không được phép bỏ hành lý không người trông coi tại nhà ga.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "b1_g2_ex1",
                        "multiple_choice",
                        "Complete the First Conditional: 'If the bus arrives on time, we ___ the 9:00 a.m. session.'",
                        "will catch",
                        "Đúng: mệnh đề 'If' đã chia hiện tại đơn ('arrives'), nên mệnh đề chính dùng 'will + V nguyên thể' ('will catch').",
                        tier="easy",
                        phase="pre_task",
                        options=["catch", "caught", "will catch", "would catch"],
                        hint="Main clause of First Conditional uses 'will + base verb'.",
                    ),
                    _ex(
                        "b1_g2_ex2",
                        "true_or_false",
                        "True or False: 'You mustn't pay for parking' means parking is free and optional.",
                        "False",
                        "Sai (False): 'mustn't' nghĩa là BỊ CẤM làm gì. Để nói đỗ xe miễn phí/không cần trả tiền phải dùng 'don't have to pay'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Compare prohibition ('mustn't') vs lack of necessity ('don't have to').",
                    ),
                    _ex(
                        "b1_g2_ex3",
                        "multiple_choice",
                        "Choose the best modal for free entrance: 'Admission is free on Sunday, so visitors ___ buy a ticket.'",
                        "don't have to",
                        "Đúng: vé miễn phí nghĩa là không cần phải mua -> 'don't have to'. Dùng 'mustn't' sẽ thành cấm mua vé.",
                        tier="medium",
                        phase="task_cycle",
                        options=["mustn't", "don't have to", "shouldn't", "cannot"],
                        hint="Express 'not necessary', not 'forbidden'.",
                    ),
                    _ex(
                        "b1_g2_ex4",
                        "fill_in_the_blank",
                        "Complete with the correct form of 'read': 'If she {blank} the instructions carefully, she won't make that mistake.'",
                        "reads",
                        "Đúng: mệnh đề điều kiện loại 1 sau 'If' dùng thì Hiện tại đơn; chủ ngữ 'she' chia ngôi thứ ba số ít 'reads'.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Present simple form of 'read' with 'she'.",
                    ),
                    _ex(
                        "b1_g2_ex5",
                        "grammar_correction",
                        "Select the corrected sentence for: 'If it will rain tomorrow, the outdoor workshop will move indoors.'",
                        "If it rains tomorrow, the outdoor workshop will move indoors.",
                        "Đúng: không dùng 'will' trong mệnh đề 'If' của câu điều kiện loại 1; phải chia Hiện tại đơn 'rains'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "If it rains tomorrow, the outdoor workshop will move indoors.",
                            "If it will rain tomorrow, the outdoor workshop will move indoors.",
                            "If it rained tomorrow, the outdoor workshop will move indoors.",
                            "If it raining tomorrow, the outdoor workshop moves indoors.",
                        ],
                        hint="Use Present Simple in the 'if' clause even for future time.",
                    ),
                    _ex(
                        "b1_g2_ex6",
                        "fill_in_the_blank",
                        "Complete with one modal contraction (prohibition): 'Staff {blank} share customer passwords under any circumstances.'",
                        "mustn't",
                        "Đúng: đây là quy định nghiêm cấm hoàn toàn ('under any circumstances'), nên dùng 'mustn't'.",
                        tier="hard",
                        phase="language_focus",
                        hint="Strong prohibition modal.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: 'If we ___ now, we will avoid the evening traffic.'",
                        "options": ["leave", "will leave", "left", "leaving"],
                        "answer": "leave",
                        "explanation": "First Conditional uses Present Simple ('leave') in the 'if' clause.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Which sentence means 'It is not necessary to wear a tie'?",
                        "options": [
                            "You mustn't wear a tie.",
                            "You don't have to wear a tie.",
                            "You shouldn't be wearing a tie.",
                            "You haven't to wear a tie.",
                        ],
                        "answer": "You don't have to wear a tie.",
                        "explanation": "'Don't have to' expresses absence of obligation; 'mustn't' expresses prohibition.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Identify the error-free First Conditional sentence:",
                        "options": [
                            "Unless she finishes early, she will miss the last ferry.",
                            "Unless she won't finish early, she misses the last ferry.",
                            "If she doesn't finish early, she won't misses the last ferry.",
                            "Unless she didn't finish early, she will miss the last ferry.",
                        ],
                        "answer": "Unless she finishes early, she will miss the last ferry.",
                        "explanation": "'Unless' (= if not) takes an affirmative Present Simple verb ('finishes') + 'will + base verb'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    # B2 — Professional Fluency
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "B2",
        "unit_slug": "unit-b2-grammar",
        "unit_title": "Unit 2: B2 Grammar Precision",
        "unit_description": "Handle formal passive reports, counterfactual conditionals, and contrast clauses.",
        "unit_order_index": 2,
        "background_color": "#7C3AED",
        "lessons": [
            {
                "slug": "b2-grammar-passive-voice",
                "order_index": 1,
                "title": "Grammar 1: Passive Voice Across Tenses",
                "description": "Form active-to-passive transformations across tenses and modal structures.",
                "outcome": "You can write formal reports and process descriptions using accurate passive forms.",
                "estimated_minutes": 14,
                "xp_reward": 50,
                "pass_threshold": 75,
                "grammar": {
                    "slug": "grammar-b2-passive-voice",
                    "title": "Passive Voice: Tenses, Modals & Professional Register",
                    "level": "B2",
                    "topic": "passive_voice",
                    "summary": "Câu bị động qua các thì (Hiện tại hoàn thành, Quá khứ, Tiếp diễn) và động từ khuyết thiếu trong văn phong học thuật/công việc.",
                    "content": (
                        "1. Công thức cốt lõi: be (chia đúng thì) + V3/ed (past participle).\n"
                        "- Hiện tại đơn / Quá khứ đơn: is/are + V3 | was/were + V3.\n"
                        "- Tiếp diễn: is/are/was/were + being + V3 ('The server is being upgraded now.').\n"
                        "- Hoàn thành: has/have/had + been + V3 ('The security patch has been deployed.').\n"
                        "- Động từ khuyết thiếu: modal + be + V3 ('All expenses must be approved before Friday.').\n\n"
                        "2. Nguyên tắc sử dụng tự nhiên:\n"
                        "- Dùng bị động khi muốn nhấn mạnh kết quả/quy trình hoặc tác nhân không quan trọng.\n"
                        "- Lưu ý nội động từ (happen, occur, arrive, consist of) KHÔNG chia ở dạng bị động ('The error occurred at noon', KHÔNG viết 'was occurred')."
                    ),
                    "grammar_points": [
                        "Hiện tại hoàn thành bị động: has/have + been + V3",
                        "Khuyết thiếu bị động: must/should/can + be + V3",
                        "Nội động từ (occur, happen, arrive) không có dạng bị động",
                    ],
                    "examples": [
                        {
                            "sentence": "Three new safety standards have been introduced across the factory.",
                            "translation": "Ba tiêu chuẩn an toàn mới đã được áp dụng trên toàn nhà máy.",
                        },
                        {
                            "sentence": "Confidential files must not be shared outside the project channel.",
                            "translation": "Các tệp bảo mật không được phép chia sẻ ra ngoài kênh dự án.",
                        },
                        {
                            "sentence": "The main conference hall is being renovated until next Monday.",
                            "translation": "Hội trường chính đang được tu sửa cho đến thứ Hai tuần tới.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "b2_g1_ex1",
                        "multiple_choice",
                        "Choose the passive form: 'Every quarterly budget ___ by the finance committee before approval.'",
                        "is reviewed",
                        "Đúng: 'Every quarterly budget' chịu tác động của hành động 'review' theo quy trình lặp lại, nên dùng Hiện tại đơn bị động 'is reviewed'.",
                        tier="easy",
                        phase="pre_task",
                        options=["reviews", "is reviewed", "is reviewing", "reviewed"],
                        hint="Does a budget review itself or get reviewed?",
                    ),
                    _ex(
                        "b2_g1_ex2",
                        "true_or_false",
                        "True or False: 'The network outage was happened around midnight.' is grammatically correct.",
                        "False",
                        "Sai (False): 'happen' là nội động từ (intransitive verb) không nhận tân ngữ nên không bao giờ chia dạng bị động. Phải viết 'happened'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Check if 'happen' can take a passive form.",
                    ),
                    _ex(
                        "b2_g1_ex3",
                        "fill_in_the_blank",
                        "Complete the modal passive using 'verify': 'All safety certificates must be {blank} before onboarding.'",
                        "verified",
                        "Đúng: bị động với động từ khuyết thiếu có dạng 'must be + V3/ed', phân từ hai của 'verify' là 'verified'.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Past participle of 'verify'.",
                    ),
                    _ex(
                        "b2_g1_ex4",
                        "collocation_choice",
                        "Select the Present Perfect passive: 'Since January, two regional clinics ___ with modern diagnostic tools.'",
                        "have been equipped",
                        "Đúng: 'Since January' yêu cầu Hiện tại hoàn thành; 'two clinics' số nhiều và nhận hành động trang bị -> 'have been equipped'.",
                        tier="medium",
                        phase="task_cycle",
                        options=[
                            "have equipped",
                            "have been equipped",
                            "were equipped",
                            "are being equipped",
                        ],
                        hint="Look at 'Since January' and plural 'two clinics'.",
                    ),
                    _ex(
                        "b2_g1_ex5",
                        "grammar_correction",
                        "Choose the accurate sentence for: 'The bridge is repairing right now, so traffic is diverted.'",
                        "The bridge is being repaired right now, so traffic is diverted.",
                        "Đúng: hành động đang diễn ra tại thời điểm nói ('right now') ở thể bị động cần 'is/are + being + V3' ('is being repaired').",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "The bridge is being repaired right now, so traffic is diverted.",
                            "The bridge is repairing right now, so traffic is diverted.",
                            "The bridge has repaired right now, so traffic is diverted.",
                            "The bridge is been repaired right now, so traffic is diverted.",
                        ],
                        hint="Use Present Continuous Passive ('is being + V3').",
                    ),
                    _ex(
                        "b2_g1_ex6",
                        "fill_in_the_blank",
                        "Complete using the correct form of 'acknowledge': 'It is widely {blank} that early preparation reduces exam anxiety.'",
                        "acknowledged",
                        "Đúng: cấu trúc bị động khách quan 'It is widely acknowledged that...' dùng phân từ hai 'acknowledged'.",
                        tier="hard",
                        phase="language_focus",
                        hint="Past participle of 'acknowledge'.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: 'The updated policy ___ to all employees tomorrow morning.'",
                        "options": ["will send", "will be sent", "is sending", "has sent"],
                        "answer": "will be sent",
                        "explanation": "Future simple passive uses 'will be + past participle'.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Which sentence correctly uses Present Continuous Passive?",
                        "options": [
                            "The solar panels are installing on the roof today.",
                            "The solar panels are being installed on the roof today.",
                            "The solar panels have been installing on the roof today.",
                            "The solar panels are been installed on the roof today.",
                        ],
                        "answer": "The solar panels are being installed on the roof today.",
                        "explanation": "Ongoing passive action requires 'are being + V3/ed'.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Select the grammatically sound sentence:",
                        "options": [
                            "Several unexpected delays were occurred during customs inspection.",
                            "Nobody was arrived before the keynote started.",
                            "Three critical bugs were resolved before the release window closed.",
                            "The package consists of fragile glass was wrapped carefully.",
                        ],
                        "answer": "Three critical bugs were resolved before the release window closed.",
                        "explanation": "'Resolve' is transitive and forms a valid passive; 'occur' and 'arrive' are intransitive.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
            {
                "slug": "b2-grammar-conditionals-2-3-and-contrast",
                "order_index": 2,
                "title": "Grammar 2: Conditionals 2/3 & Contrast Clauses",
                "description": "Express unreal present/past situations and distinguish Despite vs Although.",
                "outcome": "You can discuss hypothetical scenarios and write balanced arguments with contrast connectors.",
                "estimated_minutes": 14,
                "xp_reward": 50,
                "pass_threshold": 75,
                "grammar": {
                    "slug": "grammar-b2-conditionals-2-3-contrast",
                    "title": "Second & Third Conditionals + Contrast Connectors",
                    "level": "B2",
                    "topic": "conditionals_and_discourse",
                    "summary": "Câu điều kiện giả định loại 2, loại 3 và cấu trúc tương phản Although / Even though vs Despite / In spite of.",
                    "content": (
                        "1. Câu điều kiện loại 2 (giả định trái thực tế HIỆN TẠI/TƯƠNG LAI):\n"
                        "- If + Past Simple (dùng 'were' trang trọng cho mọi chủ ngữ), S + would/could + V nguyên thể.\n"
                        "- Ví dụ: 'If we had a larger budget, we would expand the lab.'\n\n"
                        "2. Câu điều kiện loại 3 (giả định trái thực tế QUÁ KHỨ):\n"
                        "- If + had + V3/ed, S + would/could + have + V3/ed.\n"
                        "- Ví dụ: 'If they had checked the backup earlier, they wouldn't have lost any files.'\n\n"
                        "3. Liên từ và giới từ chỉ sự tương phản:\n"
                        "- Although / Even though / Though + MỆNH ĐỀ (S + V).\n"
                        "- Despite / In spite of + CỤM DANH TỪ hoặc V-ing (HOẶC 'the fact that + mệnh đề'). KHÔNG viết 'Despite of' hay 'Although + cụm danh từ'."
                    ),
                    "grammar_points": [
                        "Loại 2: If + S + V2/were, S + would + V",
                        "Loại 3: If + S + had + V3, S + would have + V3",
                        "Although + S + V | Despite / In spite of + NP / V-ing (không có 'Despite of')",
                    ],
                    "examples": [
                        {
                            "sentence": "If I were in charge of scheduling, I would leave buffer time between meetings.",
                            "translation": "Nếu tôi phụ trách xếp lịch, tôi sẽ chừa khoảng đệm giữa các cuộc họp.",
                        },
                        {
                            "sentence": "Despite facing initial delays, the research team met the publication deadline.",
                            "translation": "Mặc dù gặp chậm trễ ban đầu, nhóm nghiên cứu vẫn kịp hạn công bố.",
                        },
                        {
                            "sentence": "If she had backed up the drive before the update, the presentation would have survived.",
                            "translation": "Nếu cô ấy đã sao lưu ổ đĩa trước khi cập nhật, bài thuyết trình đã không bị mất.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "b2_g2_ex1",
                        "multiple_choice",
                        "Choose the best connector: '___ the heavy rain, the outdoor charity run went ahead as planned.'",
                        "Despite",
                        "Đúng: 'the heavy rain' là một cụm danh từ (noun phrase), nên đứng sau giới từ 'Despite'. 'Although' và 'Even though' đòi hỏi mệnh đề S + V.",
                        tier="easy",
                        phase="pre_task",
                        options=["Although", "Despite", "Even though", "Whereas"],
                        hint="Check whether 'the heavy rain' has a conjugated verb.",
                    ),
                    _ex(
                        "b2_g2_ex2",
                        "true_or_false",
                        "True or False: 'Despite of the tight deadline, the team delivered clean code.' is correct.",
                        "False",
                        "Sai (False): tuyệt đối KHÔNG dùng giới từ 'of' sau 'Despite'. Viết đúng là 'Despite the tight deadline...' hoặc 'In spite of the tight deadline...'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Compare 'despite' and 'in spite of'.",
                    ),
                    _ex(
                        "b2_g2_ex3",
                        "fill_in_the_blank",
                        "Complete the formal Second Conditional with 'be': 'If our office {blank} closer to the metro, I would commute by train every day.'",
                        "were",
                        "Đúng: câu điều kiện loại 2 trái với thực tế hiện tại; trong văn phong chuẩn mực, dùng 'were' cho cả chủ ngữ số ít ('our office').",
                        tier="medium",
                        phase="task_cycle",
                        hint="Formal subjunctive past of 'to be' in Type 2 conditionals.",
                    ),
                    _ex(
                        "b2_g2_ex4",
                        "multiple_choice",
                        "Complete the Third Conditional: 'If they had left ten minutes earlier, they ___ the ferry.'",
                        "wouldn't have missed",
                        "Đúng: mệnh đề 'If' chia Quá khứ hoàn thành ('had left') -> mệnh đề chính loại 3 dùng 'would/wouldn't have + V3' ('wouldn't have missed').",
                        tier="medium",
                        phase="task_cycle",
                        options=[
                            "wouldn't miss",
                            "won't miss",
                            "wouldn't have missed",
                            "didn't miss",
                        ],
                        hint="Past counterfactual result takes 'would(n't) have + V3'.",
                    ),
                    _ex(
                        "b2_g2_ex5",
                        "grammar_correction",
                        "Select the accurate sentence for: 'If I would have known about the cancellation, I wouldn't have travelled downtown.'",
                        "If I had known about the cancellation, I wouldn't have travelled downtown.",
                        "Đúng: không đặt 'would have' trong mệnh đề 'If'; điều kiện loại 3 dùng 'If + had + V3'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "If I had known about the cancellation, I wouldn't have travelled downtown.",
                            "If I would have known about the cancellation, I wouldn't have travelled downtown.",
                            "If I knew about the cancellation, I wouldn't have travelled downtown.",
                            "If I had knew about the cancellation, I wouldn't have travelled downtown.",
                        ],
                        hint="Replace 'would have' inside the 'if' clause with Past Perfect.",
                    ),
                    _ex(
                        "b2_g2_ex6",
                        "fill_in_the_blank",
                        "Complete the fixed phrase: 'In {blank} of the limited resources, the prototype performed remarkably well.'",
                        "spite",
                        "Đúng: cụm từ cố định 'In spite of' (= Despite) + cụm danh từ.",
                        tier="hard",
                        phase="language_focus",
                        hint="Collocation: 'In ___ of'.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: '___ she felt exhausted, she finished reviewing every report.'",
                        "options": ["Despite", "In spite of", "Although", "Because of"],
                        "answer": "Although",
                        "explanation": "'She felt exhausted' is a full clause (S + V), so it requires the conjunction 'Although'.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Which sentence uses the Second Conditional accurately?",
                        "options": [
                            "If I have more time today, I would learn Italian.",
                            "If I had more free time, I would practice piano daily.",
                            "If I had more free time, I will practice piano daily.",
                            "If I would have more free time, I practiced piano.",
                        ],
                        "answer": "If I had more free time, I would practice piano daily.",
                        "explanation": "Second Conditional pairs Past Simple ('had') with 'would + base verb'.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Choose the accurate Mixed/Third Conditional sentence:",
                        "options": [
                            "If we hadn't overlooked that clause, we wouldn't face this penalty now.",
                            "If we didn't overlook that clause, we wouldn't have face this penalty.",
                            "If we hadn't overlooked that clause, we wouldn't faced this penalty.",
                            "If we hadn't been overlook that clause, we wouldn't face this penalty.",
                        ],
                        "answer": "If we hadn't overlooked that clause, we wouldn't face this penalty now.",
                        "explanation": "A past unreal condition ('hadn't overlooked') can produce a present unreal result ('wouldn't face ... now').",
                        "difficulty_tier": "hard",
                    },
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    # C1 — Advanced Academic & IELTS
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "C1",
        "unit_slug": "unit-c1-grammar",
        "unit_title": "Unit 2: C1 Academic Syntax",
        "unit_description": "Use negative inversion, participle reduction, and cleft sentences for emphasis.",
        "unit_order_index": 2,
        "background_color": "#D97706",
        "lessons": [
            {
                "slug": "c1-grammar-negative-inversion",
                "order_index": 1,
                "title": "Grammar 1: Negative & Restrictive Inversion",
                "description": "Invert auxiliary verbs after fronted negative or restrictive adverbials.",
                "outcome": "You can create formal emphasis with Seldom, Rarely, Not only, and Under no circumstances.",
                "estimated_minutes": 15,
                "xp_reward": 55,
                "pass_threshold": 80,
                "grammar": {
                    "slug": "grammar-c1-negative-inversion",
                    "title": "Negative & Restrictive Inversion (Seldom / Not only / Little)",
                    "level": "C1",
                    "topic": "advanced_syntax",
                    "summary": "Đảo ngữ trang trọng khi đưa trạng từ/cụm phủ định hoặc giới hạn lên đầu câu.",
                    "content": (
                        "1. Nguyên tắc chung:\n"
                        "Khi đặt cụm mang nghĩa phủ định hoặc giới hạn ở đầu câu để nhấn mạnh, mệnh đề theo sau phải đảo trợ động từ lên trước chủ ngữ (giống trật tự câu hỏi):\n"
                        "Negative/Restrictive Adverbial + Auxiliary/Modal + Subject + Main Verb\n\n"
                        "2. Các cụm điển hình:\n"
                        "- Seldom / Rarely / Never + have/has/do/did + S + V ('Seldom have we observed such consistency.')\n"
                        "- Not only + aux + S + V, but ... also ... ('Not only did she lead the audit, but she also trained new analysts.')\n"
                        "- Under no circumstances / On no account + should/must/can + S + V\n"
                        "- Only after / Only when / Not until + [mệnh đề phụ hoặc cụm thời gian] + [ĐẢO NGỮ Ở MỆNH ĐỀ CHÍNH]:\n"
                        "  'Not until the sensor cooled down did the reading stabilize.' (chú ý: đảo ngữ xảy ra ở mệnh đề chính, KHÔNG đảo ở mệnh đề ngay sau Not until/Only when)."
                    ),
                    "grammar_points": [
                        "Seldom/Rarely/Never + Aux + S + V (động từ chính trở về nguyên thể nếu dùng do/does/did)",
                        "Not only + Aux + S + V, but S + also + V",
                        "Not until / Only when + [chưa đảo], [Aux + S + V ở mệnh đề chính]",
                    ],
                    "examples": [
                        {
                            "sentence": "Rarely has a municipal policy achieved consensus so rapidly.",
                            "translation": "Hiếm khi một chính sách đô thị lại đạt được sự đồng thuận nhanh chóng đến vậy.",
                        },
                        {
                            "sentence": "Under no circumstances should unverified figures appear in the annual brief.",
                            "translation": "Trong bất kỳ hoàn cảnh nào, các số liệu chưa kiểm chứng cũng không được xuất hiện trong báo cáo thường niên.",
                        },
                        {
                            "sentence": "Not until all samples were cross-checked did the researchers publish the dataset.",
                            "translation": "Mãi đến khi toàn bộ mẫu được kiểm tra chéo, các nhà nghiên cứu mới công bố bộ dữ liệu.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "c1_g1_ex1",
                        "multiple_choice",
                        "Choose the inverted clause: 'Never ___ such rapid progress across the whole cohort.'",
                        "have I witnessed",
                        "Đúng: đứng sau trạng từ phủ định đầu câu 'Never', cần đảo trợ động từ 'have' lên trước chủ ngữ 'I': 'have I witnessed'.",
                        tier="easy",
                        phase="pre_task",
                        options=[
                            "I have witnessed",
                            "have I witnessed",
                            "did I witnessed",
                            "witnessed I",
                        ],
                        hint="Fronted 'Never' triggers auxiliary + subject + verb.",
                    ),
                    _ex(
                        "c1_g1_ex2",
                        "true_or_false",
                        "True or False: 'Little did he realized how influential the paper would become.' is grammatically correct.",
                        "False",
                        "Sai (False): đã dùng trợ động từ 'did' trong đảo ngữ quá khứ thì động từ chính phải ở dạng nguyên thể 'realize', không chia '-ed'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Check the main verb form after 'did'.",
                    ),
                    _ex(
                        "c1_g1_ex3",
                        "fill_in_the_blank",
                        "Complete the inversion phrase: 'Under no {blank} should visitors touch the archival manuscripts.'",
                        "circumstances",
                        "Đúng: cụm cố định mở đầu câu đảo ngữ mang nghĩa cấm tuyệt đối là 'Under no circumstances' (trong mọi hoàn cảnh đều không...).",
                        tier="medium",
                        phase="task_cycle",
                        hint="Noun plural used in 'Under no ___'.",
                    ),
                    _ex(
                        "c1_g1_ex4",
                        "multiple_choice",
                        "Select the accurate sentence with 'Only after':",
                        "Only after reviewing the logs did the engineers locate the bottleneck.",
                        "Đúng: đảo ngữ xảy ra ở mệnh đề chính ('did the engineers locate') ngay sau cụm giới từ 'Only after reviewing the logs'.",
                        tier="medium",
                        phase="task_cycle",
                        options=[
                            "Only after reviewing the logs the engineers located the bottleneck.",
                            "Only after reviewing the logs did the engineers locate the bottleneck.",
                            "Only after did reviewing the logs the engineers locate the bottleneck.",
                            "Only after reviewing the logs did the engineers located the bottleneck.",
                        ],
                        hint="Invert the main clause, keeping 'locate' in base form after 'did'.",
                    ),
                    _ex(
                        "c1_g1_ex5",
                        "grammar_correction",
                        "Choose the corrected version of: 'Not until did the rain stop we resumed the excavation.'",
                        "Not until the rain stopped did we resume the excavation.",
                        "Đúng: với 'Not until + mệnh đề thời gian', mệnh đề theo sau 'Not until' giữ trật tự bình thường ('the rain stopped'), còn sự đảo ngữ đặt ở mệnh đề chính ('did we resume').",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "Not until the rain stopped did we resume the excavation.",
                            "Not until did the rain stop we resumed the excavation.",
                            "Not until the rain stopped we did resume the excavation.",
                            "Not until the rain stop did we resumed the excavation.",
                        ],
                        hint="Inversion belongs in the SECOND (main) clause after 'Not until + clause'.",
                    ),
                    _ex(
                        "c1_g1_ex6",
                        "fill_in_the_blank",
                        "Complete the inversion: 'Not only {blank} the proposal cut energy costs, it also reduces packaging waste.'",
                        "does",
                        "Đúng: động từ ở mệnh đề thứ nhất là hiện tại đơn với chủ ngữ số ít 'the proposal' và nguyên thể 'cut' đứng sau -> đảo trợ động từ 'does'.",
                        tier="hard",
                        phase="language_focus",
                        hint="Present simple auxiliary agreeing with singular 'the proposal'.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: 'Seldom ___ encountered such a clear methodological critique.'",
                        "options": ["have I", "I have", "did I", "am I"],
                        "answer": "have I",
                        "explanation": "With past participle 'encountered', invert 'have' before 'I'.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Which sentence applies 'No sooner ... than' accurately?",
                        "options": [
                            "No sooner had the panel adjourned than questions poured in.",
                            "No sooner the panel had adjourned when questions poured in.",
                            "No sooner had the panel adjourned when questions poured in.",
                            "No sooner did the panel adjourned than questions poured in.",
                        ],
                        "answer": "No sooner had the panel adjourned than questions poured in.",
                        "explanation": "'No sooner' pairs with inverted past perfect ('had ... V3') and 'than' (not 'when').",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Identify the well-formed formal warning:",
                        "options": [
                            "On no account employees must disclose client records.",
                            "On no account must employees disclose client records.",
                            "On no account must employees to disclose client records.",
                            "On no account do employees must disclose client records.",
                        ],
                        "answer": "On no account must employees disclose client records.",
                        "explanation": "'On no account' requires modal inversion: 'must + subject + bare infinitive'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
            {
                "slug": "c1-grammar-participle-clauses-and-clefts",
                "order_index": 2,
                "title": "Grammar 2: Participle Clauses & Cleft Sentences",
                "description": "Condense complex ideas with participle clauses without dangling modifiers and use cleft focus.",
                "outcome": "You can write concise, cohesive academic sentences free of dangling participles.",
                "estimated_minutes": 15,
                "xp_reward": 55,
                "pass_threshold": 80,
                "grammar": {
                    "slug": "grammar-c1-participle-cleft",
                    "title": "Participle Clauses & Cleft Sentences (It / What)",
                    "level": "C1",
                    "topic": "cohesion_and_emphasis",
                    "summary": "Rút gọn mệnh đề bằng phân từ (V-ing / V3 / Having V3) tránh lỗi chủ ngữ treo và nhấn mạnh bằng câu chẻ.",
                    "content": (
                        "1. Mệnh đề phân từ (Participle Clauses):\n"
                        "- Chủ động: V-ing ('Analyzing the survey results, the team noticed a clear shift.').\n"
                        "- Bị động: V3/ed ('Located near the port, the warehouse cuts shipping time.').\n"
                        "- Hành động hoàn tất trước: Having + V3/ed ('Having verified the sources, the editor approved the draft.').\n"
                        "- QUY TẮC SỐNG CÒN: Chủ ngữ ngầm hiểu của cụm phân từ PHẢI trùng với chủ ngữ của mệnh đề chính! Nếu không trùng sẽ mắc lỗi 'dangling participle'.\n\n"
                        "2. Câu chẻ (Cleft Sentences) để nhấn mạnh:\n"
                        "- It is/was [X] that/who ... ('It was the lack of longitudinal data that limited the study.')\n"
                        "- What [mệnh đề] is/was [X] ('What differentiates this approach is its transparent rubric.')"
                    ),
                    "grammar_points": [
                        "Chủ ngữ của mệnh đề chính phải chính là chủ thể thực hiện/chịu tác động của cụm phân từ",
                        "Having + V3 diễn tả hành động hoàn thành trước hành động chính",
                        "What-cleft và It-cleft giúp nhấn mạnh trọng tâm thông tin trong văn viết học thuật",
                    ],
                    "examples": [
                        {
                            "sentence": "Having completed the pilot study, the researchers revised the questionnaire.",
                            "translation": "Sau khi hoàn thành nghiên cứu thử nghiệm, các nhà nghiên cứu đã chỉnh sửa bảng câu hỏi.",
                        },
                        {
                            "sentence": "Designed for low-bandwidth regions, the module caches audio locally.",
                            "translation": "Được thiết kế cho các khu vực băng thông thấp, mô-đun lưu âm thanh tại thiết bị.",
                        },
                        {
                            "sentence": "What makes this synthesis persuasive is its reliance on verifiable evidence.",
                            "translation": "Điều khiến bản tổng hợp này thuyết phục là việc dựa vào bằng chứng có thể kiểm chứng.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "c1_g2_ex1",
                        "multiple_choice",
                        "Choose the passive participle opener: '___ in 1998, the institute now trains over 400 linguists annually.'",
                        "Founded",
                        "Đúng: 'the institute' được thành lập (nghĩa bị động) năm 1998, nên rút gọn bằng quá khứ phân từ 'Founded'. Không dùng 'Founding' (chủ động) hay 'Found' (nghĩa tìm thấy).",
                        tier="easy",
                        phase="pre_task",
                        options=["Founding", "Founded", "Found", "To found"],
                        hint="Is the institute doing the founding or being founded?",
                    ),
                    _ex(
                        "c1_g2_ex2",
                        "true_or_false",
                        "True or False: 'Walking down the corridor, the archive room came into view.' has a dangling participle error.",
                        "True",
                        "Đúng (True): 'the archive room' không thể tự đi bộ dọc hành lang ('walking down the corridor'). Chủ ngữ mệnh đề chính lệch với chủ thể hành động ở cụm phân từ.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Ask yourself: who was walking down the corridor?",
                    ),
                    _ex(
                        "c1_g2_ex3",
                        "fill_in_the_blank",
                        "Complete the perfect participle clause: '{blank} checked all citations twice, Maya felt confident submitting the paper.'",
                        "Having",
                        "Đúng: 'Having + V3' ('Having checked') diễn tả việc kiểm tra trích dẫn đã hoàn tất trước khi nộp bài.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Use the perfect participle auxiliary before 'checked'.",
                    ),
                    _ex(
                        "c1_g2_ex4",
                        "multiple_choice",
                        "Choose the valid continuation to avoid a dangling modifier: 'Having analyzed the transcripts thoroughly, ___.'",
                        "the linguists identified three recurring patterns",
                        "Đúng: người phân tích bản ghi âm là 'the linguists', nên chủ ngữ mệnh đề chính bắt buộc phải là 'the linguists'.",
                        tier="medium",
                        phase="task_cycle",
                        options=[
                            "three recurring patterns emerged immediately",
                            "the linguists identified three recurring patterns",
                            "the study's conclusion became obvious",
                            "there were three recurring patterns found",
                        ],
                        hint="The subject right after the comma must be the person who analyzed the transcripts.",
                    ),
                    _ex(
                        "c1_g2_ex5",
                        "grammar_correction",
                        "Choose the well-formed cleft sentence emphasizing the cause:",
                        "It was the sudden drop in temperature that halted the outdoor experiment.",
                        "Đúng: câu chẻ chuẩn xác 'It was [cụm danh từ được nhấn mạnh] that [mệnh đề còn lại]'. Tránh lặp chủ ngữ 'which it' hay dùng 'what' sau danh từ trong cấu trúc It-cleft.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "It was the sudden drop in temperature that halted the outdoor experiment.",
                            "It was the sudden drop in temperature what halted the outdoor experiment.",
                            "It was the sudden drop in temperature that it halted the outdoor experiment.",
                            "What was the sudden drop in temperature that halted the outdoor experiment.",
                        ],
                        hint="Standard It-cleft pattern: 'It is/was X that ...'.",
                    ),
                    _ex(
                        "c1_g2_ex6",
                        "fill_in_the_blank",
                        "Complete the Wh-cleft sentence: '{blank} learners need most at intermediate levels is consistent spoken feedback.'",
                        "What",
                        "Đúng: câu chẻ 'What + S + V + is ...' dùng 'What' (= the thing that) làm chủ ngữ mệnh đề danh từ.",
                        tier="hard",
                        phase="language_focus",
                        hint="Start the Wh-cleft with one relative/nominal word.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: '___ the warning signs, the crew postponed the departure.'",
                        "options": ["Recognize", "Recognizing", "Recognized", "Having recognize"],
                        "answer": "Recognizing",
                        "explanation": "Active participle 'Recognizing' matches the subject 'the crew'.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Which sentence has NO dangling modifier?",
                        "options": [
                            "Published last spring, readers praised the handbook for its clarity.",
                            "Published last spring, the handbook received praise for its clarity.",
                            "Publishing last spring, the handbook received praise for its clarity.",
                            "Having published last spring, the handbook received praise.",
                        ],
                        "answer": "Published last spring, the handbook received praise for its clarity.",
                        "explanation": "'The handbook' was published, so it must be the subject of the main clause.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Select the effective academic cleft sentence:",
                        "options": [
                            "What distinguishes the second cohort is its higher retention rate.",
                            "What distinguishes the second cohort it is its higher retention rate.",
                            "That distinguishes the second cohort is its higher retention rate.",
                            "It is its higher retention rate what distinguishes the second cohort.",
                        ],
                        "answer": "What distinguishes the second cohort is its higher retention rate.",
                        "explanation": "A Wh-cleft does not repeat 'it' before 'is' and uses 'What ... is ...'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════════
    # C2 — Native Mastery & Nuances
    # ══════════════════════════════════════════════════════════════════════════
    {
        "level": "C2",
        "unit_slug": "unit-c2-grammar",
        "unit_title": "Unit 2: C2 Mastery & Register",
        "unit_description": "Command inverted conditionals, mandative subjunctive, and formal concessive syntax.",
        "unit_order_index": 2,
        "background_color": "#DC2626",
        "lessons": [
            {
                "slug": "c2-grammar-inverted-conditionals-subjunctive",
                "order_index": 1,
                "title": "Grammar 1: Inverted Conditionals & Subjunctive",
                "description": "Use Were/Had/Should inversion in conditionals and mandative subjunctive structures.",
                "outcome": "You can formulate formal hypotheticals and policy mandates without 'if' or redundant auxiliaries.",
                "estimated_minutes": 16,
                "xp_reward": 60,
                "pass_threshold": 80,
                "grammar": {
                    "slug": "grammar-c2-inverted-conditionals-subjunctive",
                    "title": "Inverted Conditionals (Were / Had / Should) & Mandative Subjunctive",
                    "level": "C2",
                    "topic": "subjunctive_and_inversion",
                    "summary": "Đảo ngữ điều kiện lược bỏ 'If' (Should / Were / Had) và thức giả định cầu khiến trong văn bản pháp lý, học thuật.",
                    "content": (
                        "1. Đảo ngữ câu điều kiện trang trọng (lược bỏ 'if'):\n"
                        "- Loại 1 (tình huống có thể nhưng ít chắc chắn): Should + S + V nguyên thể ('Should any discrepancy arise, notify the chair.')\n"
                        "- Loại 2 (giả định hiện tại/tương lai): Were + S + to V / danh từ / tính từ ('Were the committee to adopt this clause, costs would drop.')\n"
                        "- Loại 3 (giả định quá khứ): Had + S + V3/ed ('Had the reviewers noticed the flaw, the paper would have been revised.')\n"
                        "- Dạng phủ định: đặt 'not' SAU chủ ngữ ('Had he not intervened...' — KHÔNG gộp thành 'Hadn't he intervened' trong đảo ngữ chuẩn).\n\n"
                        "2. Thức giả định cầu khiến (Mandative Subjunctive):\n"
                        "- Sau động từ/tính từ yêu cầu, đề xuất (insist, recommend, stipulate, essential, imperative) + that + S + [động từ nguyên thể không 'to', không chia -s, phủ định dùng 'not + V']:\n"
                        "  'The board insisted that the treasurer submit an audited statement.' / 'It is imperative that he not be omitted.'"
                    ),
                    "grammar_points": [
                        "Should + S + V | Were + S + to V | Had + S + V3 (không còn từ 'if')",
                        "Phủ định trong đảo ngữ điều kiện: Had/Were/Should + S + not + V (không rút gọn n't ở đầu câu)",
                        "Mandative subjunctive: that + S + V nguyên thể (kể cả với he/she/it và phủ định 'not + V')",
                    ],
                    "examples": [
                        {
                            "sentence": "Should further clarification be required, please consult Appendix B.",
                            "translation": "Nếu cần làm rõ thêm, vui lòng tham khảo Phụ lục B.",
                        },
                        {
                            "sentence": "Were we to overlook minor variances, long-term calibration would drift.",
                            "translation": "Nếu chúng ta bỏ qua những sai lệch nhỏ, việc hiệu chuẩn dài hạn sẽ bị trôi lệch.",
                        },
                        {
                            "sentence": "The charter stipulates that every delegate cast only a single ballot.",
                            "translation": "Điều lệ quy định mỗi đại biểu chỉ bỏ một lá phiếu duy nhất.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "c2_g1_ex1",
                        "multiple_choice",
                        "Choose the inverted Type 3 opener: '___ earlier, the audit would have flagged the missing invoices.'",
                        "Had the team intervened",
                        "Đúng: câu điều kiện loại 3 đảo ngữ lược bỏ 'if' dùng 'Had + S + V3' ('Had the team intervened'). Không giữ 'If' khi đã đảo ngữ.",
                        tier="easy",
                        phase="pre_task",
                        options=[
                            "Had the team intervened",
                            "If had the team intervened",
                            "Did the team intervene",
                            "Were the team intervened",
                        ],
                        hint="Formal Type 3 inversion replaces 'If ... had V3' with 'Had + S + V3'.",
                    ),
                    _ex(
                        "c2_g1_ex2",
                        "true_or_false",
                        "True or False: 'Hadn't the pilot reacted promptly, the landing would have been rough.' uses standard formal negative inversion.",
                        "False",
                        "Sai (False): trong đảo ngữ câu điều kiện trang trọng, KHÔNG viết dạng rút gọn 'Hadn't/Weren't' ở đầu câu; phải tách 'not' sau chủ ngữ: 'Had the pilot not reacted...'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="Check placement of 'not' in formal conditional inversion.",
                    ),
                    _ex(
                        "c2_g1_ex3",
                        "fill_in_the_blank",
                        "Complete with the subjunctive form of 'release': 'The ethics panel recommended that the lead author {blank} the raw dataset publicly.'",
                        "release",
                        "Đúng: sau 'recommended that', thức giả định dùng động từ nguyên thể không chia '-s' ('release') dù chủ ngữ là ngôi thứ ba số ít 'the lead author'.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Base subjunctive form of 'release' (no -s).",
                    ),
                    _ex(
                        "c2_g1_ex4",
                        "multiple_choice",
                        "Select the accurate formal conditional: '___ the proposal, several departments would need retraining.'",
                        "Were the board to approve",
                        "Đúng: điều kiện giả định tương lai ít khả năng dùng cấu trúc 'Were + S + to V' ('Were the board to approve'). Sai nếu dùng bare infinitive sau 'Were'.",
                        tier="medium",
                        phase="task_cycle",
                        options=[
                            "Were the board approve",
                            "Were the board to approve",
                            "Should the board to approve",
                            "Was the board to approve",
                        ],
                        hint="Inverted Type 2 uses 'Were + subject + to-infinitive'.",
                    ),
                    _ex(
                        "c2_g1_ex5",
                        "grammar_correction",
                        "Choose the corrected sentence for: 'It is imperative that the witness does not leave before the hearing adjourns.'",
                        "It is imperative that the witness not leave before the hearing adjourns.",
                        "Đúng: thức giả định phủ định sau 'It is imperative that...' dùng 'S + not + V nguyên thể' ('the witness not leave'), không dùng trợ động từ 'does not'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "It is imperative that the witness not leave before the hearing adjourns.",
                            "It is imperative that the witness does not leave before the hearing adjourns.",
                            "It is imperative that the witness did not leave before the hearing adjourns.",
                            "It is imperative that the witness not to leave before the hearing adjourns.",
                        ],
                        hint="Negative mandative subjunctive omits 'do/does': 'not + base verb'.",
                    ),
                    _ex(
                        "c2_g1_ex6",
                        "fill_in_the_blank",
                        "Use an inverted modal (do not use 'If'): '{blank} any technical difficulties arise during the exam, raise your hand immediately.'",
                        "Should",
                        "Đúng: 'Should + S + V nguyên thể' thay cho 'If any technical difficulties should arise...' để diễn đạt tình huống dự phòng trang trọng.",
                        tier="hard",
                        phase="language_focus",
                        hint="Inverted first-conditional contingency opener.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: '___ you require an extension, submit the request 48 hours prior.'",
                        "options": ["Should", "Were", "Had", "Would"],
                        "answer": "Should",
                        "explanation": "'Should + S + base verb' expresses a formal Type 1 contingency.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Select the grammatically sound negative inversion:",
                        "options": [
                            "Hadn't they secured funding, the clinic would have closed.",
                            "Had they not secured funding, the clinic would have closed.",
                            "Did they not secured funding, the clinic would have closed.",
                            "Were they not secured funding, the clinic would have closed.",
                        ],
                        "answer": "Had they not secured funding, the clinic would have closed.",
                        "explanation": "Formal negative conditional inversion places 'not' after the subject ('Had they not...').",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Choose the accurate mandative subjunctive clause:",
                        "options": [
                            "Regulations demand that every applicant submits original transcripts.",
                            "Regulations demand that every applicant be present for identity verification.",
                            "Regulations demand that every applicant is present for identity verification.",
                            "Regulations demand that every applicant to be present.",
                        ],
                        "answer": "Regulations demand that every applicant be present for identity verification.",
                        "explanation": "Subjunctive passive/copula uses bare 'be' after 'demand that'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
            {
                "slug": "c2-grammar-concessive-cautionary-structures",
                "order_index": 2,
                "title": "Grammar 2: Albeit, Notwithstanding & Lest",
                "description": "Deploy high-register concessive and cautionary clauses accurately in academic prose.",
                "outcome": "You can introduce concise qualifications and formal precautions with C2 precision.",
                "estimated_minutes": 16,
                "xp_reward": 60,
                "pass_threshold": 80,
                "grammar": {
                    "slug": "grammar-c2-albeit-notwithstanding-lest",
                    "title": "Nuanced Concessive & Cautionary Structures (Albeit / Notwithstanding / Lest)",
                    "level": "C2",
                    "topic": "formal_register_and_nuance",
                    "summary": "Sử dụng chính xác các cấu trúc nhượng bộ và phòng ngừa bậc cao: albeit, notwithstanding, lest và mệnh đề nhượng bộ với tính/trạng từ đứng đầu.",
                    "content": (
                        "1. 'Albeit' (= although it be / mặc dù, dẫu vậy):\n"
                        "- KHÔNG kéo theo một mệnh đề đầy đủ S + V! Chỉ đi với cụm tính từ, trạng từ, giới từ hoặc phân từ:\n"
                        "  'The recovery was steady, albeit uneven.' / 'He agreed, albeit reluctantly.'\n\n"
                        "2. 'Notwithstanding' (= despite / mặc cho, bất chấp):\n"
                        "- Có thể đứng trước hoặc sau cụm danh từ trong văn bản pháp lý/học thuật ('Notwithstanding the tight schedule, standards remained high.' / 'The tight schedule notwithstanding, ...').\n\n"
                        "3. 'Lest' (= in order that ... not / kẻo, phòng khi):\n"
                        "- Theo sau là mệnh đề mang nghĩa phòng ngừa (không thêm 'not' vì 'lest' đã mang nghĩa phủ định!).\n"
                        "- Động từ chia thức giả định (base verb) hoặc 'should + V': 'She documented every step lest the rationale be forgotten.'\n\n"
                        "4. Đảo nhượng bộ với tính từ / trạng từ + as / though:\n"
                        "- 'Compelling though the argument may seem, the sample remains small.'"
                    ),
                    "grammar_points": [
                        "albeit + Adj/Adv/PrepPhrase/Participle (KHÔNG dùng albeit + S + V)",
                        "notwithstanding + Noun Phrase (đứng trước hoặc ngay sau danh từ)",
                        "lest + S + (should) + V nguyên thể (không thêm 'not' sau 'lest')",
                    ],
                    "examples": [
                        {
                            "sentence": "The transition proved smooth, albeit slightly costlier than initially projected.",
                            "translation": "Quá trình chuyển đổi diễn ra suôn sẻ, dù tốn kém hơn đôi chút so với dự kiến ban đầu.",
                        },
                        {
                            "sentence": "Notwithstanding repeated warnings, several departments delayed the audit.",
                            "translation": "Bất chấp các cảnh báo lặp lại, nhiều phòng ban vẫn trì hoãn kiểm toán.",
                        },
                        {
                            "sentence": "The archivist sealed the folio carefully lest humidity damage the ink.",
                            "translation": "Người lưu trữ niêm phong tập bản thảo cẩn thận kẻo độ ẩm làm hỏng mực.",
                        },
                    ],
                },
                "exercises": [
                    _ex(
                        "c2_g2_ex1",
                        "multiple_choice",
                        "Choose the concise qualifier: 'The quarterly yield improved, ___ at a slower pace than analysts anticipated.'",
                        "albeit",
                        "Đúng: 'albeit' đi trực tiếp với cụm giới từ 'at a slower pace...' để bổ sung nhượng bộ ngắn gọn. 'Although' ở vị trí này thường cần mệnh đề đầy đủ, còn 'notwithstanding' không kết hợp tự nhiên với cụm giới từ 'at a slower pace' theo nghĩa nhượng bộ bổ ngữ như vậy.",
                        tier="easy",
                        phase="pre_task",
                        options=["albeit", "lest", "whereas", "unless"],
                        hint="Introduces a brief concessive phrase without a finite verb.",
                    ),
                    _ex(
                        "c2_g2_ex2",
                        "true_or_false",
                        "True or False: 'He lowered his voice lest anyone shouldn't overhear the code.' uses 'lest' accurately.",
                        "False",
                        "Sai (False): bản thân 'lest' đã mang nghĩa phủ định ('để không / kẻo'), nên tuyệt đối không đi với 'not' hay 'shouldn't'. Đúng phải là 'lest anyone (should) overhear...'.",
                        tier="easy",
                        phase="pre_task",
                        options=["True", "False"],
                        hint="'Lest' already carries negative purpose meaning.",
                    ),
                    _ex(
                        "c2_g2_ex3",
                        "fill_in_the_blank",
                        "Complete with one formal preposition (not 'Despite'): '{blank} the substantial variance across regions, the aggregate index held steady.'",
                        "Notwithstanding",
                        "Đúng: 'Notwithstanding' đứng đầu câu trước cụm danh từ mang nghĩa 'bất chấp / mặc dù có...'.",
                        tier="medium",
                        phase="task_cycle",
                        hint="Formal single-word equivalent of 'Despite' (starts with N).",
                    ),
                    _ex(
                        "c2_g2_ex4",
                        "multiple_choice",
                        "Select the sentence that uses 'albeit' grammatically:",
                        "Her critique was fair, albeit delivered in blunt language.",
                        "Đúng: 'albeit' đi kèm cụm phân từ/tính từ rút gọn ('delivered in blunt language') chứ không kèm một mệnh đề đầy đủ có chủ ngữ và động từ chia thì.",
                        tier="medium",
                        phase="task_cycle",
                        options=[
                            "Her critique was fair, albeit she used blunt language.",
                            "Her critique was fair, albeit delivered in blunt language.",
                            "Albeit she used blunt language, her critique was fair.",
                            "Her critique was fair, albeit was blunt.",
                        ],
                        hint="Never put a full subject + finite verb clause directly after 'albeit'.",
                    ),
                    _ex(
                        "c2_g2_ex5",
                        "grammar_correction",
                        "Choose the accurate revision of: 'The committee postponed the vote lest premature rumors don't destabilize the talks.'",
                        "The committee postponed the vote lest premature rumors destabilize the talks.",
                        "Đúng: bỏ 'don't' (tránh phủ định kép sau 'lest') và dùng động từ nguyên thể giả định 'destabilize'.",
                        tier="hard",
                        phase="language_focus",
                        options=[
                            "The committee postponed the vote lest premature rumors destabilize the talks.",
                            "The committee postponed the vote lest premature rumors don't destabilize the talks.",
                            "The committee postponed the vote lest premature rumors destabilizing the talks.",
                            "The committee postponed the vote lest for premature rumors destabilize the talks.",
                        ],
                        hint="'Lest + subject + bare subjunctive verb' without 'not'.",
                    ),
                    _ex(
                        "c2_g2_ex6",
                        "collocation_choice",
                        "Complete the fronted concessive structure: 'Plausible ___ the hypothesis appears, longitudinal data contradict it.'",
                        "though",
                        "Đúng: cấu trúc nhượng bộ đảo tính từ lên đầu câu theo mẫu 'Adjective + though/as + S + V'. Các từ 'albeit', 'despite', 'lest' không dùng trong cấu trúc đảo tính từ này.",
                        tier="hard",
                        phase="language_focus",
                        options=["though", "albeit", "despite", "lest"],
                        hint="Concessive linker paired with fronted adjective 'Plausible ___'.",
                    ),
                ],
                "question_bank": [
                    {
                        "prompt": "Complete: 'The expedition reached the ridge, ___ three hours behind schedule.'",
                        "options": ["albeit", "despite", "lest", "whereas"],
                        "answer": "albeit",
                        "explanation": "'Albeit' introduces a reduced qualifying phrase ('three hours behind schedule') without a verb.",
                        "difficulty_tier": "easy",
                    },
                    {
                        "prompt": "Which sentence applies 'lest' correctly?",
                        "options": [
                            "Keep copies of every receipt lest the auditor will request proof.",
                            "Keep copies of every receipt lest the auditor request proof.",
                            "Keep copies of every receipt lest the auditor doesn't request proof.",
                            "Keep copies of every receipt lest requesting proof.",
                        ],
                        "answer": "Keep copies of every receipt lest the auditor request proof.",
                        "explanation": "'Lest' takes the bare subjunctive ('request') or 'should + base verb', never a negative.",
                        "difficulty_tier": "medium",
                    },
                    {
                        "prompt": "Identify the well-formed formal concessive sentence:",
                        "options": [
                            "Notwithstanding of the smaller budget, output rose.",
                            "Ambitious though the target may seem, the timeline remains viable.",
                            "The recovery was tangible, albeit it remained fragile.",
                            "In spite the objection, the motion carried.",
                        ],
                        "answer": "Ambitious though the target may seem, the timeline remains viable.",
                        "explanation": "'Adjective + though + subject + verb' is idiomatic C2 concession; the others misuse 'notwithstanding [of]', 'albeit + clause', or 'in spite [of]'.",
                        "difficulty_tier": "hard",
                    },
                ],
            },
        ],
    },
]


def validate_grammar_course_catalog() -> None:
    """Validate structural integrity, CEFR balance, provenance, and non-duplication."""
    levels_seen = [unit["level"] for unit in GRAMMAR_UNITS_AND_LESSONS]
    if levels_seen != list(CEFR_LEVELS):
        raise ValueError(f"Expected one grammar unit per CEFR level A1-C2, got {levels_seen}")

    seen_grammar_titles: set[str] = set()
    seen_lesson_titles: set[str] = set()
    seen_exercise_ids: set[str] = set()
    seen_questions: set[str] = set()
    seen_qb_prompts: set[str] = set()

    for unit in GRAMMAR_UNITS_AND_LESSONS:
        level = unit["level"]
        lessons = unit["lessons"]
        if len(lessons) < 2:
            raise ValueError(f"Unit {unit['unit_slug']} must have at least 2 lessons")

        order_indices = [lesson["order_index"] for lesson in lessons]
        if order_indices != sorted(range(1, len(lessons) + 1)):
            raise ValueError(f"Non-sequential lesson order_index in {unit['unit_slug']}: {order_indices}")

        for lesson in lessons:
            g = lesson["grammar"]
            if g["level"] != level:
                raise ValueError(f"Grammar level mismatch: {g['slug']}")
            g_title_key = g["title"].strip().casefold()
            if g_title_key in seen_grammar_titles:
                raise ValueError(f"Duplicate grammar title: {g['title']}")
            seen_grammar_titles.add(g_title_key)

            l_title_key = lesson["title"].strip().casefold()
            if l_title_key in seen_lesson_titles:
                raise ValueError(f"Duplicate lesson title: {lesson['title']}")
            seen_lesson_titles.add(l_title_key)

            if not g.get("content", "").strip() or len(g.get("examples", [])) < 3:
                raise ValueError(f"Incomplete grammar theory in {g['slug']}")
            for marker in _MOJIBAKE_MARKERS:
                if marker in g.get("summary", "") or marker in g["content"]:
                    raise ValueError(f"Mojibake detected in grammar theory {g['slug']}")
            for ex_item in g["examples"]:
                for forbidden in ("correct_answer", "answer", "is_correct"):
                    if forbidden in ex_item:
                        raise ValueError(f"Grammar example in {g['slug']} leaks {forbidden}")
                for marker in _MOJIBAKE_MARKERS:
                    if marker in str(ex_item):
                        raise ValueError(f"Mojibake detected in grammar example {g['slug']}")

            exercises = lesson["exercises"]
            if len(exercises) < 6:
                raise ValueError(f"Lesson {lesson['slug']} must have >= 6 exercises")

            tier_counts = {tier: 0 for tier in GRAMMAR_DIFFICULTY_TIERS}
            for ex in exercises:
                ex_id = ex["id"]
                if ex_id in seen_exercise_ids:
                    raise ValueError(f"Duplicate exercise id: {ex_id}")
                seen_exercise_ids.add(ex_id)

                q_norm = ex["question"].strip().casefold()
                if q_norm in seen_questions:
                    raise ValueError(f"Duplicate exercise question: {ex['question']}")
                seen_questions.add(q_norm)

                expected_base = base_type_for(ex["ui_type"])
                if expected_base != ex["type"]:
                    raise ValueError(f"Exercise {ex_id} has type={ex['type']} != {expected_base}")

                if not str(ex.get("correct_answer", "")).strip():
                    raise ValueError(f"Empty correct_answer in {ex_id}")
                if not str(ex.get("explanation", "")).strip():
                    raise ValueError(f"Empty explanation in {ex_id}")

                if ex.get("options"):
                    opt_texts = [option_text(o) for o in ex["options"]]
                    if len(opt_texts) != len(set(opt_texts)):
                        raise ValueError(f"Duplicate options in exercise {ex_id}: {opt_texts}")
                    if ex["correct_answer"] not in opt_texts:
                        raise ValueError(
                            f"Exercise {ex_id} correct_answer {ex['correct_answer']!r} not in options {opt_texts}"
                        )

                tier = ex.get("difficulty_tier")
                if tier not in tier_counts:
                    raise ValueError(f"Invalid difficulty_tier {tier!r} in {ex_id}")
                if ex.get("difficulty") != DIFFICULTY_TIER_TO_NUMERIC[tier]:
                    raise ValueError(f"Difficulty numeric mismatch in {ex_id}")
                if ex.get("points") != TIER_POINTS[tier]:
                    raise ValueError(f"Points mismatch in {ex_id}")
                tier_counts[tier] += 1

                for marker in _MOJIBAKE_MARKERS:
                    if marker in ex["question"] or marker in ex["explanation"]:
                        raise ValueError(f"Mojibake detected in exercise {ex_id}")

            if any(count < 2 for count in tier_counts.values()):
                raise ValueError(
                    f"Lesson {lesson['slug']} must have >=2 exercises per tier, got {tier_counts}"
                )

            qb_items = lesson.get("question_bank", [])
            qb_tiers = {q["difficulty_tier"] for q in qb_items}
            if qb_tiers != set(GRAMMAR_DIFFICULTY_TIERS):
                raise ValueError(f"Question bank in {lesson['slug']} missing tiers: {qb_tiers}")
            for qb in qb_items:
                p_norm = qb["prompt"].strip().casefold()
                if p_norm in seen_qb_prompts:
                    raise ValueError(f"Duplicate question_bank prompt: {qb['prompt']}")
                seen_qb_prompts.add(p_norm)
                if len(qb["options"]) != len(set(qb["options"])):
                    raise ValueError(f"Duplicate options in question_bank: {qb['prompt']}")
                if qb["answer"] not in qb["options"]:
                    raise ValueError(f"Question bank answer not in options: {qb['prompt']}")
                for marker in _MOJIBAKE_MARKERS:
                    if marker in qb["prompt"] or marker in qb["explanation"]:
                        raise ValueError(f"Mojibake detected in question_bank: {qb['prompt']}")


def build_lesson_content_payload(
    lesson_spec: dict[str, Any],
    *,
    level: str,
    grammar_item_id: uuid.UUID,
) -> dict[str, Any]:
    """Build persisted Lesson.content dict linking GrammarItem, exercises, and QA metadata."""
    grammar = lesson_spec["grammar"]
    return {
        "version": 1,
        "cefr_level": level,
        "grammar_item_id": str(grammar_item_id),
        "grammar_points": list(grammar["grammar_points"]),
        "metadata": {
            "provenance_type": PROVENANCE_AI_GENERATED,
            "qa_status": QA_STATUS_NEEDS_REVIEW,
            "publication_state": "DRAFT",
            "is_published": False,
            "source_reference": None,
            "authoring_notes": (
                "Original pedagogical grammar explanation and exercises aligned with CEFR; "
                "pending human editorial review before marking VERIFIED."
            ),
            "difficulty_tiers_present": list(GRAMMAR_DIFFICULTY_TIERS),
        },
        "exercises": [dict(ex) for ex in lesson_spec["exercises"]],
    }
