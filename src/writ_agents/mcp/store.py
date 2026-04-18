"""In-memory session store for the MCP server.

Sessions are keyed by session_id. The MCP server typically runs per-client
(stdio), so an in-memory dict is sufficient. For HTTP deployments with
multiple clients, a single process still works since each connection gets
its own session_id.
"""

from __future__ import annotations

from writ_agents.core.session import InterviewSession


class SessionStore:
    """Keeps InterviewSessions alive across MCP tool calls."""

    def __init__(self) -> None:
        self._sessions: dict[str, InterviewSession] = {}

    def create(self) -> InterviewSession:
        session = InterviewSession()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> InterviewSession | None:
        return self._sessions.get(session_id)

    def require(self, session_id: str) -> InterviewSession:
        session = self.get(session_id)
        if session is None:
            raise KeyError(
                f"No session '{session_id}'. Call writ_interview_start first."
            )
        return session

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())
