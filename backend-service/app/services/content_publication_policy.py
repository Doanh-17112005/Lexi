"""Shared content publication & quarantine policy across Learner and Admin APIs.

Distinguishes three content states cleanly without auto-promoting unverified rows:
- ``PUBLISHED``: Verified / explicitly published items (or legacy pre-QA rows
  that carry no draft/review/conflict/blocked metadata).
- ``DRAFT``: Items flagged ``NEEDS_REVIEW``, ``DRAFT``, or ``is_published=False``.
  Visible in Admin QA tools, hidden from Learner discovery & learning sessions.
- ``QUARANTINED``: Items flagged ``CONFLICT`` or ``BLOCKED`` during source QA.
  Hidden from Learners and blocked from ``VERIFIED`` promotion until resolved.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.vocabulary_catalog_policy import normalize_all_tags

PUBLICATION_PUBLISHED = "PUBLISHED"
PUBLICATION_DRAFT = "DRAFT"
PUBLICATION_QUARANTINED = "QUARANTINED"

_DRAFT_QA_STATES = {"NEEDS_REVIEW", "DRAFT"}
_QUARANTINE_AUDIT_STATES = {"CONFLICT", "BLOCKED"}
_QUARANTINE_TOKENS = {"conflict", "blocked", "audit_status:conflict", "audit_status:blocked"}
_DRAFT_TOKENS = {"needs_review", "draft", "qa_status:needs_review", "qa_status:draft"}


def _normalized_upper(value: Any) -> str:
    return str(value or "").strip().upper()


def classify_vocabulary_publication(raw_tags: Any) -> str:
    """Return ``PUBLISHED``, ``DRAFT``, or ``QUARANTINED`` for a VocabularyItem."""
    if raw_tags is None:
        return PUBLICATION_PUBLISHED

    tokens = set(normalize_all_tags(raw_tags))

    if isinstance(raw_tags, Mapping):
        audit_status = _normalized_upper(raw_tags.get("audit_status"))
        qa_status = _normalized_upper(raw_tags.get("qa_status"))
        pub_flag = raw_tags.get("is_published")

        if audit_status in _QUARANTINE_AUDIT_STATES or (tokens & _QUARANTINE_TOKENS):
            return PUBLICATION_QUARANTINED
        if qa_status in _QUARANTINE_AUDIT_STATES:
            return PUBLICATION_QUARANTINED
        if pub_flag is False or qa_status in _DRAFT_QA_STATES:
            return PUBLICATION_DRAFT
        if tokens & _DRAFT_TOKENS:
            return PUBLICATION_DRAFT
        if qa_status == "VERIFIED" or pub_flag is True:
            return PUBLICATION_PUBLISHED
        return PUBLICATION_PUBLISHED

    if tokens & _QUARANTINE_TOKENS:
        return PUBLICATION_QUARANTINED
    if tokens & _DRAFT_TOKENS:
        return PUBLICATION_DRAFT
    return PUBLICATION_PUBLISHED


def is_vocabulary_learner_visible(raw_tags: Any) -> bool:
    """Return True only when a VocabularyItem may be served to learners."""
    return classify_vocabulary_publication(raw_tags) == PUBLICATION_PUBLISHED


def classify_lesson_publication(lesson: Any) -> str:
    """Return ``PUBLISHED``, ``DRAFT``, or ``QUARANTINED`` for a Lesson ORM/model."""
    raw_content = getattr(lesson, "content", None)
    if not isinstance(raw_content, Mapping):
        return PUBLICATION_PUBLISHED

    metadata = raw_content.get("metadata")
    if not isinstance(metadata, Mapping):
        return PUBLICATION_PUBLISHED

    audit_status = _normalized_upper(metadata.get("audit_status"))
    qa_status = _normalized_upper(metadata.get("qa_status"))
    pub_state = _normalized_upper(metadata.get("publication_state"))
    is_published = metadata.get("is_published")

    if audit_status in _QUARANTINE_AUDIT_STATES or qa_status in _QUARANTINE_AUDIT_STATES:
        return PUBLICATION_QUARANTINED
    if is_published is False or pub_state == PUBLICATION_DRAFT or qa_status in _DRAFT_QA_STATES:
        return PUBLICATION_DRAFT
    return PUBLICATION_PUBLISHED


def is_lesson_learner_visible(lesson: Any) -> bool:
    """Return True only when a Lesson may appear in Learner course/roadmap APIs."""
    return classify_lesson_publication(lesson) == PUBLICATION_PUBLISHED
