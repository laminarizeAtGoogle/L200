"""Active PII and secret redaction pipeline for logs and persistent memory.

Integrates Google Cloud Data Loss Prevention (Cloud DLP API:
`google.cloud.dlp_v2.DlpServiceClient`) with deterministic local scrubbing rules
so sensitive data (emails, phone numbers, SSNs, credit cards, API keys, JWTs,
and bearer tokens) is always redacted prior to storage.
"""

from __future__ import annotations

import re
from typing import Any

try:
    from google.cloud import dlp_v2
except ImportError:  # pragma: no cover
    dlp_v2 = None  # type: ignore[assignment]


class PiiRedactionScrubber:
    """Scrubs PII and credentials from text and structured payloads before storage."""

    # Deterministic scrubbing patterns applied before/after Cloud DLP
    _PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
        (
            "API_KEY",
            re.compile(
                r"\b(AIza[0-9A-Za-z\-_]{20,50}|ghp_[0-9A-Za-z]{20,50}|sk-[0-9A-Za-z\-_]{20,}|AKIA[0-9A-Z]{16})\b"
            ),
            "[REDACTED_API_KEY]",
        ),
        (
            "JWT_TOKEN",
            re.compile(
                r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"
            ),
            "[REDACTED_JWT]",
        ),
        (
            "BEARER_TOKEN",
            re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]+=*"),
            "Bearer [REDACTED_TOKEN]",
        ),
        (
            "US_SSN",
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "[REDACTED_SSN]",
        ),
        (
            "CREDIT_CARD",
            re.compile(
                r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[ -]?\d{4}[ -]?\d{4}[ -]?\d{1,4}\b"
            ),
            "[REDACTED_CARD]",
        ),
        (
            "PHONE_NUMBER",
            re.compile(
                r"(?<!\d)(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)"
            ),
            "[REDACTED_PHONE]",
        ),
        (
            "EMAIL_ADDRESS",
            # Preserve official service account identifiers (*.iam.gserviceaccount.com)
            # while redacting personal/human email addresses.
            re.compile(
                r"\b[A-Za-z0-9._%+-]+@(?!([A-Za-z0-9-]+\.)?iam\.gserviceaccount\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ),
            "[REDACTED_EMAIL]",
        ),
    ]

    _SENSITIVE_DICT_KEYS = frozenset(
        {
            "password",
            "secret",
            "api_key",
            "apikey",
            "access_token",
            "refresh_token",
            "private_key",
            "authorization",
            "cookie",
            "ssn",
            "credit_card",
        }
    )

    def __init__(
        self,
        project_id: str | None = None,
        enable_cloud_dlp: bool = False,
    ) -> None:
        self.project_id = project_id
        self.enable_cloud_dlp = enable_cloud_dlp
        self._dlp_client: Any | None = None
        if enable_cloud_dlp and dlp_v2 is not None and project_id:
            try:
                self._dlp_client = dlp_v2.DlpServiceClient()
            except Exception:
                self._dlp_client = None

    def scrub_text(self, text: str) -> str:
        """Redacts PII and secrets from a string using Cloud DLP and regex patterns."""
        if not text:
            return text

        scrubbed = text
        for _, pattern, replacement in self._PATTERNS:
            scrubbed = pattern.sub(replacement, scrubbed)

        if self._dlp_client is not None and self.project_id:
            try:
                parent = f"projects/{self.project_id}/locations/global"
                inspect_config = {
                    "info_types": [
                        {"name": "EMAIL_ADDRESS"},
                        {"name": "PHONE_NUMBER"},
                        {"name": "US_SOCIAL_SECURITY_NUMBER"},
                        {"name": "CREDIT_CARD_NUMBER"},
                        {"name": "GCP_API_KEY"},
                    ]
                }
                deidentify_config = {
                    "info_type_transformations": {
                        "transformations": [
                            {
                                "primitive_transformation": {
                                    "replace_with_info_type_config": {}
                                }
                            }
                        ]
                    }
                }
                response = self._dlp_client.deidentify_content(
                    request={
                        "parent": parent,
                        "inspect_config": inspect_config,
                        "deidentify_config": deidentify_config,
                        "item": {"value": scrubbed},
                    },
                    timeout=3.0,
                )
                if response and response.item and response.item.value:
                    scrubbed = response.item.value
            except Exception:
                # Deterministic regex scrubbing already applied above
                pass

        return scrubbed

    def scrub_payload(self, value: Any) -> Any:
        """Recursively scrubs strings, dicts, and lists prior to logging or storage."""
        if isinstance(value, str):
            return self.scrub_text(value)
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for k, v in value.items():
                key_lower = str(k).lower()
                if key_lower in self._SENSITIVE_DICT_KEYS:
                    cleaned[k] = "[REDACTED_SECRET]"
                else:
                    cleaned[k] = self.scrub_payload(v)
            return cleaned
        if isinstance(value, list):
            return [self.scrub_payload(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.scrub_payload(item) for item in value)
        return value


DEFAULT_SCRUBBER = PiiRedactionScrubber()
