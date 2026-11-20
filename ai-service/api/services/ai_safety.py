"""AI input/output safety helpers shared by Lexi Chat, Topic Chat, and TraceCAG."""

from __future__ import annotations

import re

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_INJECTED_SECTION_RE = re.compile(
    r"---\s*(?:Knowledge Graph Context|TraceCAG Turn Guidance|Errors Found|Native-Language Hint|System)\b[^-\n]*---",
    re.IGNORECASE,
)
_PROMPT_INJECTION_RE = re.compile(
    r"(?:"
    r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions?"
    r"|reveal\s+(?:your\s+)?(?:system\s+prompt|instructions|internal\s+prompt|api\s+keys?)"
    r"|print\s+(?:your\s+)?(?:env|environment\s+variables?|secrets?|api\s+keys?)"
    r"|show\s+(?:me\s+)?(?:other\s+users?|another\s+user|all\s+sessions)"
    r")",
    re.IGNORECASE,
)
_SECRET_LEAK_RE = re.compile(
    r"(?:"
    r"AIza[0-9A-Za-z_-]{20,}"
    r"|gsk_[0-9A-Za-z]{16,}"
    r"|sk-[0-9A-Za-z_-]{16,}"
    r"|Bearer\s+[A-Za-z0-9._-]{20,}"
    r")",
)
_INTERNAL_PROMPT_LEAK_RE = re.compile(
    r"(?:"
    r"---\s*(?:Knowledge Graph Context|TraceCAG Turn Guidance|Errors Found|Native-Language Hint)[^-\n]*---"
    r"|You are Lexi 🦜, a cheerful, witty parrot who is an expert English tutor\."
    r"|Strategy:\s*(?:SOCRATIC|praise|feedback|scaffold)\."
    r")",
    re.IGNORECASE,
)
_VI_DIACRITIC_RE = re.compile(
    r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]",
    re.IGNORECASE,
)


def sanitize_learner_input(text: str, max_chars: int = 4000) -> tuple[str, bool]:
    """Normalize learner message, strip control chars/delimiters, and flag prompt injection."""
    cleaned = _CONTROL_CHARS_RE.sub("", str(text or "")).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip()
    cleaned = re.sub(r"</?think\b[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = _INJECTED_SECTION_RE.sub("[filtered-header]", cleaned)
    injection_suspected = bool(_PROMPT_INJECTION_RE.search(cleaned))
    return cleaned, injection_suspected


def needs_vietnamese_support(
    *,
    user_input: str,
    native_language: str | None,
    native_explanation_requested: bool = False,
) -> bool:
    """Return True when Lexi/Topic Tutor should include clear Vietnamese support."""
    if native_explanation_requested:
        return True
    lang = str(native_language or "").strip().lower()
    is_vi_profile = lang in {"vi", "vietnamese"}
    lower = (user_input or "").lower()
    if _VI_DIACRITIC_RE.search(user_input or ""):
        return True
    if any(
        token in lower
        for token in ("tieng viet", "tiếng việt", "vietnamese", "dich sang", "dịch")
    ):
        return True
    return is_vi_profile and any(
        token in lower for token in ("explain", "why", "meaning", "difference", "grammar")
    )


def scrub_sensitive_output(text: str, *, fallback: str) -> str:
    """Prevent accidental output of secrets or internal prompt/KG markers."""
    candidate = str(text or "").strip()
    if not candidate:
        return candidate
    if _SECRET_LEAK_RE.search(candidate) or _INTERNAL_PROMPT_LEAK_RE.search(candidate):
        return fallback
    return candidate
