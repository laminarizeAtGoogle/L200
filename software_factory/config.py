"""Configuration and runtime settings for the GE Cloud Chat Agent & Software Factory."""

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
    """Immutable configuration for the GE Cloud Chat Agent runtime."""

    app_name: str = "ge_cloud_chat_agent"
    project_id: str = field(
        default_factory=lambda: os.environ.get("GCP_PROJECT_ID", "l200-509515")
    )
    region: str = field(
        default_factory=lambda: os.environ.get("GCP_REGION", "us-central1")
    )
    zone: str = field(
        default_factory=lambda: os.environ.get("GCP_ZONE", "us-central1-a")
    )

    # Gemini Models (Gemini 3.8 primary for Cloud Chat with 2.5 foundation tiers)
    primary_chat_model: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_CHAT_MODEL", "gemini-3.8-flash"
        )
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

    # Text-to-Speech (TTS) Voice Configuration
    tts_voice_name: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_TTS_VOICE", "en-US-Journey-F"
        )
    )
    tts_language_code: str = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_TTS_LANGUAGE", "en-US"
        )
    )
    tts_speaking_rate: float = field(
        default_factory=lambda: float(
            os.environ.get("FACTORY_TTS_SPEAKING_RATE", "1.05")
        )
    )
    enable_tts_default: bool = field(
        default_factory=lambda: os.environ.get(
            "FACTORY_ENABLE_TTS", "true"
        ).lower()
        in ("true", "1", "yes")
    )

    # Security: Identity-Aware Proxy (IAP) Verification
    iap_enforce: bool = field(
        default_factory=lambda: os.environ.get(
            "IAP_ENFORCE", "false"
        ).lower()
        in ("true", "1", "yes")
    )
    iap_expected_audience: str = field(
        default_factory=lambda: os.environ.get(
            "IAP_EXPECTED_AUDIENCE", ""
        )
    )
    authorized_users: list[str] = field(
        default_factory=lambda: [
            u.strip()
            for u in os.environ.get(
                "AUTHORIZED_USERS", "joshholtz@google.com,*@google.com"
            ).split(",")
            if u.strip()
        ]
    )

    # Read-Only Service Account for Cloud Resource Probing
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

    # Database Access Security Policy (Strictly Prohibited)
    allow_database_queries: bool = False

    # Memory & Persistence
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
    compaction_overlap: int = field(
        default_factory=lambda: int(
            os.environ.get("FACTORY_COMPACTION_OVERLAP", "2")
        )
    )

    # Server Networking
    host: str = field(
        default_factory=lambda: os.environ.get("FACTORY_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("FACTORY_PORT", "8080"))
    )


DEFAULT_CONFIG = FactoryConfig()
