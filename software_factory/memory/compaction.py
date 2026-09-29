"""Context bloat management, sliding-window truncation, and ADK history compaction.

Integrates Google ADK's `EventsCompactionConfig` and `ContextCacheConfig` with a
deterministic token-budget sliding window compactor to prevent context bloat
during multi-turn software factory builds.
"""

from __future__ import annotations

from typing import Any

from google.adk.apps.app import ContextCacheConfig, EventsCompactionConfig

from ..config import DEFAULT_CONFIG, FactoryConfig
from ..observability import DEFAULT_LOGGER, DEFAULT_SCRUBBER


def build_adk_events_compaction_config(
    config: FactoryConfig = DEFAULT_CONFIG,
) -> EventsCompactionConfig:
    """Creates an ADK EventsCompactionConfig for automatic turn summarization."""
    return EventsCompactionConfig(
        compaction_interval=config.compaction_interval,
        overlap_size=config.overlap_size,
        token_threshold=config.max_context_tokens,
        event_retention_size=config.overlap_size * 2,
    )


def build_adk_context_cache_config(
    ttl_seconds: int = 1800,
    min_tokens: int = 2048,
    cache_intervals: int = 5,
) -> ContextCacheConfig:
    """Creates an ADK ContextCacheConfig for Vertex AI / Gemini context caching."""
    return ContextCacheConfig(
        cache_intervals=cache_intervals,
        ttl_seconds=ttl_seconds,
        min_tokens=min_tokens,
    )


class ConversationHistoryCompactor:
    """Manages token budgets, sliding windows, and history compaction."""

    def __init__(
        self,
        max_tokens: int = DEFAULT_CONFIG.max_context_tokens,
        sliding_window_turns: int = 6,
    ) -> None:
        self.max_tokens = max_tokens
        self.sliding_window_turns = sliding_window_turns

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimates token count using standard ~4 chars/token heuristic."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def compact_turns(
        self,
        turns: list[dict[str, Any]],
        *,
        session_id: str = "default-session",
    ) -> dict[str, Any]:
        """Compacts conversational turns when token budget or window is exceeded.

        Preserves the most recent `sliding_window_turns` verbatim while
        condensing older turns into a scrubbed executive summary block.
        """
        total_tokens = sum(
            self.estimate_tokens(str(t.get("content", ""))) for t in turns
        )

        if (
            len(turns) <= self.sliding_window_turns
            and total_tokens <= self.max_tokens
        ):
            return {
                "compacted": False,
                "original_turn_count": len(turns),
                "retained_turn_count": len(turns),
                "total_tokens_before": total_tokens,
                "total_tokens_after": total_tokens,
                "summary": None,
                "active_turns": turns,
            }

        older_turns = turns[: -self.sliding_window_turns]
        recent_turns = turns[-self.sliding_window_turns :]

        summary_bullets: list[str] = []
        for turn in older_turns:
            role = turn.get("role", "user")
            raw_content = DEFAULT_SCRUBBER.scrub_text(
                str(turn.get("content", "")).strip()
            )
            snippet = (
                raw_content[:160] + "..."
                if len(raw_content) > 160
                else raw_content
            )
            summary_bullets.append(f"- [{role}]: {snippet}")

        compacted_summary = (
            "Compacted Historical Context Summary:\n"
            + "\n".join(summary_bullets)
        )
        summary_turn = {
            "role": "system",
            "content": compacted_summary,
            "is_compacted_summary": True,
        }
        active_turns = [summary_turn, *recent_turns]
        tokens_after = sum(
            self.estimate_tokens(str(t.get("content", "")))
            for t in active_turns
        )

        DEFAULT_LOGGER.log_event(
            event_type="HISTORY_COMPACTION_EXECUTED",
            message=(
                f"Compacted {len(older_turns)} historical turns for session "
                f"'{session_id}' ({total_tokens} -> {tokens_after} tokens)"
            ),
            session_id=session_id,
            metadata={
                "original_turn_count": len(turns),
                "retained_turn_count": len(active_turns),
                "total_tokens_before": total_tokens,
                "total_tokens_after": tokens_after,
            },
        )

        return {
            "compacted": True,
            "original_turn_count": len(turns),
            "retained_turn_count": len(active_turns),
            "total_tokens_before": total_tokens,
            "total_tokens_after": tokens_after,
            "summary": compacted_summary,
            "active_turns": active_turns,
        }


DEFAULT_COMPACTOR = ConversationHistoryCompactor()
