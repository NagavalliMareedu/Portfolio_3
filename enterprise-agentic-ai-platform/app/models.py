from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    COMPLETED = "completed"
    PENDING_APPROVAL = "pending_approval"
    REJECTED = "rejected"


class RunRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2_000)
    user_id: str = Field(min_length=1, max_length=100)
    roles: set[str] = Field(default_factory=lambda: {"employee"})


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    score: float


class TraceEvent(BaseModel):
    step: str
    detail: str


class RunResponse(BaseModel):
    run_id: str
    status: RunStatus
    answer: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    approval_id: str | None = None


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer_id: str = Field(min_length=1, max_length=100)


class ApprovalRecord(BaseModel):
    approval_id: str
    run_id: str
    user_id: str
    tool_name: str
    arguments: dict[str, Any]
    query: str
    roles: set[str]
    decided: bool = False
    approved: bool | None = None
    reviewer_id: str | None = None
