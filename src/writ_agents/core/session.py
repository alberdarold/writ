"""Interview session state — a single object holding a conversation's progress."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from writ_agents.core.schema import PartialSpec, Spec

SessionStatus = Literal["not_started", "in_progress", "ready", "error"]


class InterviewSession(BaseModel):
    """Mutable state of an ongoing interview. Holds everything needed to step."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    conversation: list[dict[str, str]] = Field(default_factory=list)
    accumulated: PartialSpec = Field(default_factory=PartialSpec)
    confidence: int = 0
    status: SessionStatus = "not_started"
    spec: Spec | None = None
    error: str | None = None

    def turns(self) -> int:
        """Count of completed exchanges (user + assistant pairs)."""
        return sum(1 for m in self.conversation if m["role"] == "assistant")
