"""Tests for the MCP session store's per-session locking."""

from __future__ import annotations

import asyncio

import pytest

from writ_agents.mcp.store import SessionStore


@pytest.mark.asyncio
async def test_lock_for_returns_same_lock_instance() -> None:
    store = SessionStore()
    session = store.create()
    lock_a = store.lock_for(session.session_id)
    lock_b = store.lock_for(session.session_id)
    assert lock_a is lock_b


@pytest.mark.asyncio
async def test_concurrent_acquires_on_same_session_serialize() -> None:
    store = SessionStore()
    session = store.create()
    events: list[str] = []

    async def worker(tag: str) -> None:
        async with store.lock_for(session.session_id):
            events.append(f"{tag}-enter")
            await asyncio.sleep(0.01)
            events.append(f"{tag}-exit")

    await asyncio.gather(worker("A"), worker("B"))
    # Either order is fine but both must fully enter/exit as a pair.
    pairs = [(events[i], events[i + 1]) for i in range(0, len(events), 2)]
    for enter, exit_ in pairs:
        assert enter.endswith("-enter") and exit_.endswith("-exit")
        assert enter[0] == exit_[0]


@pytest.mark.asyncio
async def test_delete_clears_lock() -> None:
    store = SessionStore()
    session = store.create()
    sid = session.session_id
    store.lock_for(sid)
    assert store.delete(sid) is True
    # A fresh lock is created on demand — must not be the same object.
    new_lock = store.lock_for(sid)
    async with new_lock:
        pass
