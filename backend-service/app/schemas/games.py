"""Request and response schemas for persisted game sessions."""

from typing import Any

from pydantic import BaseModel, Field


class GameAnswerSubmission(BaseModel):
    id: str = Field(..., min_length=1, max_length=100)
    answer: str = Field(default="", max_length=500)


class GameAnswerProgressRequest(BaseModel):
    answer: str = Field(default="", max_length=500)


class GameAnswerProgressResponse(BaseModel):
    session_id: str
    item_id: str
    answer: str
    is_correct: bool
    correct_answer: str
    explanation: dict[str, Any] = Field(default_factory=dict)
    already_submitted: bool = False


class GameSessionProgressResponse(BaseModel):
    session_id: str
    game_type: str
    cefr_level: str | None = None
    status: str
    content: dict[str, Any] = Field(default_factory=dict)
    answers: list[GameAnswerProgressResponse] = Field(default_factory=list)


class GameSessionCompleteRequest(BaseModel):
    answers: list[GameAnswerSubmission] = Field(default_factory=list)
    client_duration_seconds: int | None = Field(default=None, ge=0, le=86400)
    hints_used: int = Field(default=0, ge=0, le=20)


class GameSessionCompleteResponse(BaseModel):
    session_id: str
    game_type: str
    correct_count: int
    total_count: int
    raw_xp: int
    penalties: int
    base_xp: int
    xp_awarded: int
    award_status: str
    duration_seconds: int
    xp_result: dict[str, Any] | None = None
