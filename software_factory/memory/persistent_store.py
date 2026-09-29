"""Persistent session state and episodic vector memory store.

Provides:
1. ADK `SqliteSessionService` and optional `VertexAiSessionService` for
   multi-turn session persistence across restarts.
2. `PersistentEpisodicMemoryStore` backed by SQLite + deterministic vector
   embeddings (and optional `VertexAiMemoryBankService` integration) to store
   and retrieve workspace state, architectural decisions, and conversational
   history across turns.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from typing import Any

from google.adk.memory.vertex_ai_memory_bank_service import (
    VertexAiMemoryBankService,
)
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.adk.sessions.vertex_ai_session_service import (
    VertexAiSessionService,
)

from ..config import DEFAULT_CONFIG, FactoryConfig
from ..observability import DEFAULT_LOGGER, DEFAULT_SCRUBBER


def create_persistent_session_service(
    config: FactoryConfig = DEFAULT_CONFIG,
    *,
    use_vertex_ai_session: bool = False,
    agent_engine_id: str | None = None,
) -> BaseSessionService:
    """Creates a persistent ADK session service (SQLite or Vertex AI)."""
    if use_vertex_ai_session and agent_engine_id:
        return VertexAiSessionService(
            project=config.project_id,
            location=config.region,
            agent_engine_id=agent_engine_id,
        )

    db_file = Path(config.session_db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSessionService(db_path=str(db_file))


class PersistentEpisodicMemoryStore:
    """Persistent database + vector similarity store for conversational & workspace memory."""

    def __init__(
        self,
        db_path: str = DEFAULT_CONFIG.memory_db_path,
        project_id: str = DEFAULT_CONFIG.project_id,
        location: str = DEFAULT_CONFIG.region,
        agent_engine_id: str | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.project_id = project_id
        self.location = location
        self.vertex_memory_bank: VertexAiMemoryBankService | None = None
        if agent_engine_id:
            try:
                self.vertex_memory_bank = VertexAiMemoryBankService(
                    project=project_id,
                    location=location,
                    agent_engine_id=agent_engine_id,
                )
            except Exception:
                self.vertex_memory_bank = None

        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodic_memories (
                    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    workspace_path TEXT,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_workspace_state (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    workspace_path TEXT NOT NULL,
                    active_branch TEXT,
                    target_gcp_project TEXT NOT NULL,
                    target_github_repo TEXT,
                    state_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def compute_embedding(text: str, dims: int = 32) -> list[float]:
        """Computes a normalized deterministic feature-hashing vector embedding."""
        vec = [0.0] * dims
        tokens = [
            tok.lower()
            for tok in text.replace("/", " ").replace("_", " ").split()
            if tok.strip()
        ]
        if not tokens:
            return vec
        for tok in tokens:
            digest = hashlib.sha256(tok.encode("utf-8")).digest()
            idx = digest[0] % dims
            sign = 1.0 if (digest[1] % 2 == 0) else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [round(v / norm, 6) for v in vec]
        return vec

    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Computes cosine similarity between two embedding vectors."""
        if len(vec_a) != len(vec_b) or not vec_a:
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def store_memory(
        self,
        *,
        session_id: str,
        user_id: str,
        content: str,
        memory_type: str = "episodic_fact",
        workspace_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Scrubs PII and persists a memory entry with its vector embedding."""
        scrubbed_content = DEFAULT_SCRUBBER.scrub_text(content)
        scrubbed_metadata = DEFAULT_SCRUBBER.scrub_payload(metadata or {})
        embedding = self.compute_embedding(scrubbed_content)
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodic_memories (
                    session_id, user_id, workspace_path, memory_type,
                    content, embedding_json, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    workspace_path,
                    memory_type,
                    scrubbed_content,
                    json.dumps(embedding),
                    json.dumps(scrubbed_metadata),
                    now_iso,
                ),
            )
            conn.commit()
            memory_id = int(cursor.lastrowid or 0)

        DEFAULT_LOGGER.log_event(
            event_type="PERSISTENT_MEMORY_STORED",
            message=f"Stored persistent memory #{memory_id} ({memory_type})",
            session_id=session_id,
            workspace_path=workspace_path,
            metadata={"memory_id": memory_id, "memory_type": memory_type},
        )
        return memory_id

    def search_memories(
        self,
        query: str,
        *,
        session_id: str | None = None,
        workspace_path: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieves the top_k most relevant memories via vector similarity."""
        query_vec = self.compute_embedding(query)
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if workspace_path:
            clauses.append("workspace_path = ?")
            params.append(workspace_path)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM episodic_memories {where_sql} ORDER BY memory_id DESC LIMIT 200"

        scored: list[dict[str, Any]] = []
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            for row in rows:
                emb = json.loads(row["embedding_json"])
                score = self.cosine_similarity(query_vec, emb)
                scored.append(
                    {
                        "memory_id": row["memory_id"],
                        "session_id": row["session_id"],
                        "user_id": row["user_id"],
                        "workspace_path": row["workspace_path"],
                        "memory_type": row["memory_type"],
                        "content": row["content"],
                        "metadata": json.loads(row["metadata_json"]),
                        "similarity_score": round(score, 4),
                        "created_at": row["created_at"],
                    }
                )

        scored.sort(key=lambda item: item["similarity_score"], reverse=True)
        return scored[:top_k]

    def upsert_session_workspace_state(
        self,
        *,
        session_id: str,
        user_id: str,
        workspace_path: str,
        target_gcp_project: str,
        active_branch: str | None = None,
        target_github_repo: str | None = None,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persists session-level workspace and target project state across turns."""
        scrubbed_state = DEFAULT_SCRUBBER.scrub_payload(state or {})
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO session_workspace_state (
                    session_id, user_id, workspace_path, active_branch,
                    target_gcp_project, target_github_repo, state_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    workspace_path = excluded.workspace_path,
                    active_branch = COALESCE(excluded.active_branch, session_workspace_state.active_branch),
                    target_gcp_project = excluded.target_gcp_project,
                    target_github_repo = COALESCE(excluded.target_github_repo, session_workspace_state.target_github_repo),
                    state_json = excluded.state_json,
                    updated_at = excluded.updated_at
                """,
                (
                    session_id,
                    user_id,
                    workspace_path,
                    active_branch,
                    target_gcp_project,
                    target_github_repo,
                    json.dumps(scrubbed_state),
                    now_iso,
                ),
            )
            conn.commit()
        return self.get_session_workspace_state(session_id) or {}

    def get_session_workspace_state(
        self, session_id: str
    ) -> dict[str, Any] | None:
        """Fetches persisted session workspace state."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM session_workspace_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "workspace_path": row["workspace_path"],
                "active_branch": row["active_branch"],
                "target_gcp_project": row["target_gcp_project"],
                "target_github_repo": row["target_github_repo"],
                "state": json.loads(row["state_json"]),
                "updated_at": row["updated_at"],
            }


DEFAULT_MEMORY_STORE = PersistentEpisodicMemoryStore()
