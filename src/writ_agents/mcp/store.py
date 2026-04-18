"""In-memory session store for the MCP server.

Sessions are keyed by session_id. The MCP server typically runs per-client
(stdio), so an in-memory dict is sufficient. For HTTP deployments with
multiple clients, a single process still works since each connection gets
its own session_id.

Each session owns an asyncio.Lock so that concurrent calls to
`writ_interview_answer` on the same session_id serialize instead of
interleaving writes on the shared conversation list.
"""

from __future__ import annotations

import asyncio

from writ_agents.core.session import InterviewSession


class SessionStore:
    """Keeps InterviewSessions alive across MCP tool calls."""

    def __init__(self) -> None:
        self._sessions: dict[str, InterviewSession] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def create(self) -> InterviewSession:
        session = InterviewSession()
        self._sessions[session.session_id] = session
        self._locks[session.session_id] = asyncio.Lock()
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

    def lock_for(self, session_id: str) -> asyncio.Lock:
        """Per-session lock. Created on demand so external sessions work too."""
        lock = self._locks.get(session_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[session_id] = lock
        return lock

    def delete(self, session_id: str) -> bool:
        self._locks.pop(session_id, None)
        return self._sessions.pop(session_id, None) is not None

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())
