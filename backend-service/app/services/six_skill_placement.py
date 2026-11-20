"""Six-Skill Placement Test bank, sanitization, and deterministic rubric scoring (T23-T29).

Covers all 6 CEFR-aligned skills:
  - vocabulary (objective MCQ)
  - grammar (objective MCQ)
  - reading (passage + comprehension MCQ)
  - listening (audio script/TTS + comprehension MCQ)
  - speaking (spoken prompt + deterministic rubric evaluation)
  - writing (short response + deterministic rubric evaluation)

Note: When no AI grader is enabled, speaking and writing use an explicit,
transparent deterministic rubric rather than fabricating AI scores, and
placement results carry an explicit non-official CEFR disclaimer.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

PLACEMENT_DISCLAIMER = (
    "Internal LexiLingo placement estimate for personalized study recommendations "
    "— not an official CEFR certification."
)

SIX_SKILL_NAMES: tuple[str, ...] = (
    "listening",
    "speaking",
    "reading",
    "writing",
    "grammar",
    "vocabulary",
)

PLACEMENT_LEVEL_THRESHOLDS: list[tuple[float, str]] = [
    (82.0, "C2"),
    (68.0, "C1"),
    (52.0, "B2"),
    (36.0, "B1"),
    (20.0, "A2"),
    (0.0, "A1"),
]

SIX_SKILL_PLACEMENT_TASKS: List[Dict[str, Any]] = [
    # 1. Vocabulary (MCQ)
    {
        "id": "p6-vocab-1",
        "skill": "vocabulary",
        "task_type": "mcq",
        "level": "A2",
        "points": 10,
        "question": "A place where travelers check in and board planes is an ___.",
        "options": ["airport", "library", "bakery", "garage"],
        "correct": 0,
    },
    {
        "id": "p6-vocab-2",
        "skill": "vocabulary",
        "task_type": "mcq",
        "level": "B2",
        "points": 15,
        "question": "Because the evidence was ___, the committee requested another audit.",
        "options": ["inconclusive", "abundant", "transparent", "impeccable"],
        "correct": 0,
    },
    # 2. Grammar (MCQ)
    {
        "id": "p6-grammar-1",
        "skill": "grammar",
        "task_type": "mcq",
        "level": "A2",
        "points": 10,
        "question": "She ___ in Ho Chi Minh City since 2022.",
        "options": ["has lived", "is living", "lived", "live"],
        "correct": 0,
    },
    {
        "id": "p6-grammar-2",
        "skill": "grammar",
        "task_type": "mcq",
        "level": "B2",
        "points": 15,
        "question": "Hardly ___ the announcement when passengers began boarding.",
        "options": [
            "had the agent finished",
            "the agent had finished",
            "did the agent finished",
            "finished the agent",
        ],
        "correct": 0,
    },
    # 3. Reading (MCQ with passage)
    {
        "id": "p6-reading-1",
        "skill": "reading",
        "task_type": "mcq",
        "level": "B1",
        "points": 10,
        "passage": (
            "Remote teams save commuting hours each week, yet managers note that "
            "spontaneous mentoring drops unless short daily check-ins are scheduled."
        ),
        "question": "What trade-off of remote work does the passage emphasize?",
        "options": [
            "Less commuting time, but fewer informal mentoring moments without check-ins",
            "Higher office rent and slower internet",
            "Elimination of all team meetings",
            "Employees prefer longer commutes",
        ],
        "correct": 0,
    },
    {
        "id": "p6-reading-2",
        "skill": "reading",
        "task_type": "mcq",
        "level": "C1",
        "points": 15,
        "passage": (
            "While pilot results were promising, longitudinal follow-up showed "
            "retention gains tapered off whenever spaced practice ceased."
        ),
        "question": "What caused retention gains to decline over time?",
        "options": [
            "Stopping spaced practice sessions",
            "The pilot study was too short",
            "Learners changed languages mid-course",
            "Audio quality was too low",
        ],
        "correct": 0,
    },
    # 4. Listening (Audio/TTS script + MCQ)
    {
        "id": "p6-listening-1",
        "skill": "listening",
        "task_type": "listening_mcq",
        "level": "A2",
        "points": 10,
        "listening_script": (
            "Attention passengers on Train 4B to Da Nang: departure is delayed by "
            "fifteen minutes and the train will now leave from Platform 6 instead of Platform 3."
        ),
        "question": "Listen to the station announcement. Which platform should passengers go to?",
        "options": ["Platform 6", "Platform 3", "Platform 4", "Platform 15"],
        "correct": 0,
    },
    {
        "id": "p6-listening-2",
        "skill": "listening",
        "task_type": "listening_mcq",
        "level": "B1",
        "points": 15,
        "listening_script": (
            "Hi Minh, I checked the supplier quote and they offered a ten percent "
            "discount if we confirm the order before Thursday afternoon."
        ),
        "question": "Listen to the voicemail. Why should Minh reply before Thursday afternoon?",
        "options": [
            "To receive a 10% supplier discount",
            "To cancel the shipment",
            "To change the office address",
            "To schedule a Friday interview",
        ],
        "correct": 0,
    },
    # 5. Speaking (Rubric-evaluated prompt)
    {
        "id": "p6-speaking-1",
        "skill": "speaking",
        "task_type": "speaking_rubric",
        "level": "B1",
        "points": 20,
        "question": (
            "Speak or read aloud your answer (2-3 sentences): "
            "Describe a daily habit you do to improve your English and why it helps."
        ),
        "prompt_hint": "Aim for at least 15 words mentioning your habit, schedule, and reason.",
        "min_words": 15,
        "rubric_criteria": [
            "Length & fluency (min 15 words)",
            "Relevant habit/learning vocabulary",
            "Complete grammatical sentence structure",
        ],
        "rubric_keywords": [
            "english",
            "practice",
            "read",
            "listen",
            "speak",
            "every",
            "daily",
            "morning",
            "because",
            "help",
            "improve",
            "vocabulary",
            "study",
        ],
    },
    # 6. Writing (Rubric-evaluated prompt)
    {
        "id": "p6-writing-1",
        "skill": "writing",
        "task_type": "writing_rubric",
        "level": "B1",
        "points": 20,
        "question": (
            "Write a short paragraph (30+ words): Explain one learning goal you want "
            "to achieve in the next three months and the steps you will take."
        ),
        "prompt_hint": "Include your goal, timeline, and at least one concrete step or reason.",
        "min_words": 25,
        "rubric_criteria": [
            "Word count & completeness (min 25 words)",
            "Lexical diversity & goal keywords",
            "Multi-sentence organization & punctuation",
        ],
        "rubric_keywords": [
            "goal",
            "improve",
            "english",
            "practice",
            "week",
            "month",
            "because",
            "therefore",
            "however",
            "study",
            "read",
            "speak",
            "write",
            "listen",
            "will",
        ],
    },
]

MAX_SIX_SKILL_SCORE = sum(t["points"] for t in SIX_SKILL_PLACEMENT_TASKS)


def sanitize_placement_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Return learner-safe task payload with answer keys and rubric solutions stripped."""
    payload: Dict[str, Any] = {
        "id": task["id"],
        "skill": task["skill"],
        "task_type": task["task_type"],
        "level": task["level"],
        "points": task["points"],
        "question": task["question"],
    }
    if "options" in task:
        payload["options"] = list(task["options"])
    if "passage" in task:
        payload["passage"] = task["passage"]
    if "listening_script" in task:
        payload["listening_script"] = task["listening_script"]
    if "prompt_hint" in task:
        payload["prompt_hint"] = task["prompt_hint"]
    if "min_words" in task:
        payload["min_words"] = task["min_words"]
    if "rubric_criteria" in task:
        payload["rubric_criteria"] = list(task["rubric_criteria"])
    return payload


def score_rubric_response(task: Dict[str, Any], text: Optional[str]) -> Dict[str, Any]:
    """Deterministically score speaking/writing text without fabricating AI evaluation."""
    cleaned = (text or "").strip()
    words = re.findall(r"[A-Za-z']+", cleaned.lower())
    word_count = len(words)
    min_words = max(1, int(task.get("min_words", 15)))
    keywords = [kw.lower() for kw in task.get("rubric_keywords", [])]

    if word_count == 0:
        return {
            "score_0_100": 0.0,
            "points_earned": 0.0,
            "max_points": float(task["points"]),
            "scoring_mode": "deterministic_rubric",
            "ai_graded": False,
            "evaluation_note": "No response provided; scored 0 via deterministic rubric.",
            "rubric_breakdown": {
                "word_count": 0,
                "min_words": min_words,
                "keyword_hits": [],
                "length_points": 0.0,
                "keyword_points": 0.0,
                "structure_points": 0.0,
            },
        }

    # 1. Length score (max 40)
    length_ratio = min(1.0, word_count / min_words)
    length_pts = round(length_ratio * 40.0, 1)

    # 2. Keyword relevance score (max 35)
    word_set = set(words)
    hits = sorted([kw for kw in keywords if kw in word_set])
    target_hits = min(4, max(1, len(keywords)))
    keyword_pts = round(min(1.0, len(hits) / target_hits) * 35.0, 1)

    # 3. Lexical diversity & sentence structure (max 25)
    unique_ratio = len(word_set) / word_count
    sentences = [s.strip() for s in re.split(r"[.!?]+", cleaned) if len(s.strip()) >= 3]
    diversity_pts = min(15.0, round(unique_ratio * 20.0, 1))
    sentence_pts = min(10.0, len(sentences) * 5.0)
    structure_pts = round(diversity_pts + sentence_pts, 1)

    total_pct = round(min(100.0, length_pts + keyword_pts + structure_pts), 1)
    points_earned = round((total_pct / 100.0) * float(task["points"]), 2)

    return {
        "score_0_100": total_pct,
        "points_earned": points_earned,
        "max_points": float(task["points"]),
        "scoring_mode": "deterministic_rubric",
        "ai_graded": False,
        "evaluation_note": (
            "Evaluated using LexiLingo's deterministic rubric (word count, "
            "target vocabulary coverage, and sentence structure; no LLM grader required)."
        ),
        "rubric_breakdown": {
            "word_count": word_count,
            "min_words": min_words,
            "keyword_hits": hits,
            "length_points": length_pts,
            "keyword_points": keyword_pts,
            "structure_points": structure_pts,
        },
    }


def evaluate_six_skill_submission(
    answers_by_task_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Score a full 6-skill placement test submission and build recommendations."""
    skill_earned: Dict[str, float] = {s: 0.0 for s in SIX_SKILL_NAMES}
    skill_max: Dict[str, float] = {s: 0.0 for s in SIX_SKILL_NAMES}
    details: List[Dict[str, Any]] = []

    total_earned = 0.0
    objective_correct = 0
    objective_total = 0

    for task in SIX_SKILL_PLACEMENT_TASKS:
        tid = task["id"]
        skill = task["skill"]
        max_pts = float(task["points"])
        skill_max[skill] += max_pts

        ans = answers_by_task_id.get(tid, {})
        task_type = task["task_type"]

        if task_type in ("mcq", "listening_mcq"):
            objective_total += 1
            selected = ans.get("selected_option")
            is_correct = selected is not None and selected == task["correct"]
            earned = max_pts if is_correct else 0.0
            if is_correct:
                objective_correct += 1
            skill_earned[skill] += earned
            total_earned += earned
            details.append(
                {
                    "task_id": tid,
                    "skill": skill,
                    "task_type": task_type,
                    "scoring_mode": "objective_exact",
                    "is_correct": is_correct,
                    "selected_option": selected,
                    "points_earned": earned,
                    "max_points": max_pts,
                }
            )
        else:
            rubric = score_rubric_response(task, ans.get("text_response"))
            earned = rubric["points_earned"]
            skill_earned[skill] += earned
            total_earned += earned
            details.append(
                {
                    "task_id": tid,
                    "skill": skill,
                    "task_type": task_type,
                    "scoring_mode": rubric["scoring_mode"],
                    "ai_graded": False,
                    "score_0_100": rubric["score_0_100"],
                    "points_earned": earned,
                    "max_points": max_pts,
                    "evaluation_note": rubric["evaluation_note"],
                    "rubric_breakdown": rubric["rubric_breakdown"],
                }
            )

    overall_pct = round(
        (total_earned / MAX_SIX_SKILL_SCORE) * 100.0 if MAX_SIX_SKILL_SCORE else 0.0,
        1,
    )
    assessed_level = "A1"
    for threshold, level in PLACEMENT_LEVEL_THRESHOLDS:
        if overall_pct >= threshold:
            assessed_level = level
            break

    skill_scores: Dict[str, float] = {}
    for s in SIX_SKILL_NAMES:
        s_max = skill_max[s]
        skill_scores[s] = round((skill_earned[s] / s_max) * 100.0, 1) if s_max > 0 else 0.0

    sorted_skills = sorted(skill_scores.items(), key=lambda kv: kv[1])
    weakest_skills = [k for k, _ in sorted_skills[:2]]

    skill_tips = {
        "listening": "Practice short daily listening clips and train platform/number recognition.",
        "speaking": "Record 2-3 complete spoken sentences daily using target connectors.",
        "reading": "Focus on skimming main contrast ideas and cause-effect relationships.",
        "writing": "Draft structured 3-sentence paragraphs pairing clear reasons with examples.",
        "grammar": "Review tense consistency and inversion structures matched to your CEFR tier.",
        "vocabulary": "Use active spaced-repetition flashcards with example sentences.",
    }
    recommendations = [
        {
            "skill": s,
            "score": skill_scores[s],
            "advice": skill_tips.get(s, "Keep practicing daily."),
        }
        for s in weakest_skills
    ]

    return {
        "assessed_level": assessed_level,
        "total_score": round(total_earned, 2),
        "max_score": float(MAX_SIX_SKILL_SCORE),
        "score_percentage": overall_pct,
        "objective_correct": objective_correct,
        "objective_total": objective_total,
        "skill_scores": skill_scores,
        "weakest_skills": weakest_skills,
        "recommendations": recommendations,
        "details": details,
        "disclaimer": PLACEMENT_DISCLAIMER,
    }
