"""Asynchronous background memory consolidation worker.

Executes expensive memory generation, summarization, and vector consolidation
as non-blocking background `asyncio.Task` operations so conversational API
responses return immediately without UI blocking.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ..observability import DEFAULT_LOGGER, DEFAULT_SCRUBBER
from .compaction import DEFAULT_COMPACTOR, ConversationHistoryCompactor
from .persistent_store import (
    DEFAULT_MEMORY_STORE,
    PersistentEpisodicMemoryStore,
)


class AsyncMemoryConsolidator:
    """Schedules and executes non-blocking background memory consolidation jobs."""

    def __init__(
        self,
        memory_store: PersistentEpisodicMemoryStore = DEFAULT_MEMORY_STORE,
        compactor: ConversationHistoryCompactor = DEFAULT_COMPACTOR,
    ) -> None:
        self.memory_store = memory_store
        self.compactor = compactor
        self._background_tasks: set[asyncio.Task[Any]] = set()
        self.completed_jobs: int = 0

    def schedule_turn_consolidation(
        self,
        *,
        session_id: str,
        user_id: str,
        user_message: str,
        agent_reply: str,
        workspace_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> asyncio.Task[dict[str, Any]]:
        """Schedules an async background task to consolidate turn memory without blocking."""
        task = asyncio.create_task(
            self._consolidate_turn_async(
                session_id=session_id,
                user_id=user_id,
                user_message=user_message,
                agent_reply=agent_reply,
                workspace_path=workspace_path,
                metadata=metadata,
            )
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    async def _consolidate_turn_async(
        self,
        *,
        session_id: str,
        user_id: str,
        user_message: str,
        agent_reply: str,
        workspace_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Background coroutine performing PII scrubbing, embedding, and DB persistence."""
        await asyncio.sleep(0)  # Yield control immediately so caller never blocks

        scrubbed_user = DEFAULT_SCRUBBER.scrub_text(user_message)
        scrubbed_reply = DEFAULT_SCRUBBER.scrub_text(agent_reply)
        consolidated_fact = (
            f"User Intent: {scrubbed_user[:300]} | "
            f"Factory Outcome: {scrubbed_reply[:400]}"
        )

        memory_id = await asyncio.to_thread(
            self.memory_store.store_memory,
            session_id=session_id,
            user_id=user_id,
            content=consolidated_fact,
            memory_type="consolidated_turn",
            workspace_path=workspace_path,
            metadata=metadata or {},
        )
        self.completed_jobs += 1

        DEFAULT_LOGGER.log_event(
            event_type="ASYNC_MEMORY_CONSOLIDATION_COMPLETED",
            message=f"Async memory consolidation completed for session '{session_id}' (memory_id={memory_id})",
            session_id=session_id,
            workspace_path=workspace_path,
            metadata={
                "memory_id": memory_id,
                "completed_jobs": self.completed_jobs,
            },
        )
        return {"memory_id": memory_id, "session_id": session_id}

    async def flush_pending_tasks(self) -> list[ dict[str, Any]]:
        """Awaits all currently scheduled background memory tasks (useful in tests/shutdown)."""
        if not self._background_tasks:
            return []
        tasks = list(self._background_tasks)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]


DEFAULT_ASYNC_CONSOLIDATOR = AsyncMemoryConsolidator()
