"""Configuration and runtime settings for the A2A Software Factory."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


WORKSPACE_ROOT = Path(
    os.environ.get(
        "SOFTWARE_FACTORY_WORKSPACE_ROOT",
        str(Path(__file__).resolve().parent.parent),
    )
).resolve()


@dataclass(frozen=True)
class FactoryConfig:
    """Immutable configuration for the A2A Software Factory runtime."""

    app_name: str = "a2a_software_factory"
    project_id: str = field(
        default_factory=lambda: os.environ.get("GCP_PROJECT_ID", "l200-509515")
    )
    region: str = field(
        default_factory=lambda: os.environ.get("GCP_REGION", "us-central1")
    )
    zone: str = field(
        default_factory=lambda: os.environ.get("GCP_ZONE", "us-central1-a")
    )
    planning_model: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_PLANNING_MODEL", "gemini-2.5-pro"
        )
    )
    fast_model: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_FAST_MODEL", "gemini-2.5-flash"
        )
    )
    readonly_service_account: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_READONLY_SA",
            f"cloudtop-agent-reader@{os.environ.get('GCP_PROJECT_ID', 'l200-509515')}.iam.gserviceaccount.com",
        )
    )
    deployer_service_account: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_DEPLOYER_SA",
            f"github-terraform-deployer@{os.environ.get('GCP_PROJECT_ID', 'l200-509515')}.iam.gserviceaccount.com",
        )
    )
    session_db_path: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_SESSION_DB_PATH",
            str(WORKSPACE_ROOT / ".factory_state" / "sessions.db"),
        )
    )
    memory_db_path: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_MEMORY_DB_PATH",
            str(WORKSPACE_ROOT / ".factory_state" / "memory_bank.db"),
        )
    )
    max_context_tokens: int = field(
        default_factory=lambda: int(
            os.environ.get("FACTORY_MAX_CONTEXT_TOKENS", "16000")
        )
    )
    compaction_interval: int = field(
        default_factory=lambda: int(
            os.environ.get("FACTORY_COMPACTION_INTERVAL", "6")
        )
    )
    overlap_size: int = field(
        default_factory=lambda: int(
            os.environ.get("FACTORY_COMPACTION_OVERLAP", "2")
        )
    )
    host: str = field(
        default_factory=lambda: os.environ.get("FACTORY_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("FACTORY_PORT", "8080"))
    )


DEFAULT_CONFIG = FactoryConfig()
