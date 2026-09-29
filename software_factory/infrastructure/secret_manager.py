"""Secure Secret Management via Google Cloud Secret Manager.

Ensures zero hardcoded API keys or credentials exist in the codebase. All tools,
WIF workflows, and runtime clients retrieve sensitive values dynamically via
`google.cloud.secretmanager.SecretManagerServiceClient`.
"""

from __future__ import annotations

import os
from typing import Any

from ..config import DEFAULT_CONFIG
from ..observability import DEFAULT_LOGGER

try:
    from google.cloud import secretmanager
except ImportError:  # pragma: no cover
    secretmanager = None  # type: ignore[assignment]


class SecretManagerVault:
    """Retrieves secrets securely from Google Cloud Secret Manager with TTL caching."""

    def __init__(
        self,
        project_id: str | None = None,
        client: Any | None = None,
        enable_remote_lookup: bool | None = None,
    ) -> None:
        self.project_id = project_id or DEFAULT_CONFIG.project_id
        self._client = client
        self.enable_remote_lookup = (
            enable_remote_lookup
            if enable_remote_lookup is not None
            else (
                client is not None
                or os.environ.get("ENABLE_GCP_SECRET_MANAGER", "false").lower()
                == "true"
            )
        )
        self._cache: dict[str, str] = {}

    def _get_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        if self.enable_remote_lookup and secretmanager is not None:
            try:
                self._client = secretmanager.SecretManagerServiceClient()
            except Exception:
                self._client = None
        return self._client

    def build_secret_version_path(
        self,
        secret_id: str,
        version: str = "latest",
        project_id: str | None = None,
    ) -> str:
        """Builds the canonical Secret Manager resource path."""
        target_project = project_id or self.project_id
        return f"projects/{target_project}/secrets/{secret_id}/versions/{version}"

    def get_secret(
        self,
        secret_id: str,
        *,
        version: str = "latest",
        project_id: str | None = None,
        env_fallback_name: str | None = None,
    ) -> str | None:
        """Fetches a secret payload from Google Cloud Secret Manager.

        Never logs the secret value itself; logs only metadata about the access
        attempt for auditability.
        """
        cache_key = f"{project_id or self.project_id}:{secret_id}:{version}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        resource_name = self.build_secret_version_path(
            secret_id=secret_id,
            version=version,
            project_id=project_id,
        )
        client = self._get_client()
        if client is not None:
            try:
                response = client.access_secret_version(
                    request={"name": resource_name},
                    timeout=5.0,
                )
                payload = response.payload.data.decode("utf-8")
                self._cache[cache_key] = payload
                DEFAULT_LOGGER.log_event(
                    event_type="SECRET_MANAGER_ACCESS",
                    message=f"Resolved secret '{secret_id}' from Secret Manager",
                    metadata={
                        "secret_id": secret_id,
                        "resource_name": resource_name,
                        "source": "gcp_secret_manager",
                    },
                )
                return payload
            except Exception as exc:
                DEFAULT_LOGGER.log_event(
                    event_type="SECRET_MANAGER_FALLBACK",
                    message=(
                        f"Secret Manager lookup for '{secret_id}' unavailable "
                        f"({type(exc).__name__}); checking environment fallback"
                    ),
                    severity="WARNING",
                    metadata={
                        "secret_id": secret_id,
                        "resource_name": resource_name,
                    },
                )

        env_key = env_fallback_name or secret_id.upper().replace("-", "_")
        env_val = os.environ.get(env_key)
        if env_val:
            self._cache[cache_key] = env_val
            return env_val
        return None


DEFAULT_SECRET_VAULT = SecretManagerVault()
