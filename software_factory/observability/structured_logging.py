"""Structured JSON logging integrated with Google Cloud Logging and PII redaction.

Replaces raw print statements with structured JSON log records enriched with
OpenTelemetry trace/span IDs, session context, and automatic PII scrubbing.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any

from .pii_redaction import DEFAULT_SCRUBBER, PiiRedactionScrubber
from .telemetry import DEFAULT_TELEMETRY, TelemetryManager

try:
    from google.cloud import logging as cloud_logging
except ImportError:  # pragma: no cover
    cloud_logging = None  # type: ignore[assignment]


class JsonLogFormatter(logging.Formatter):
    """Formats Python LogRecords as single-line Google Cloud Logging JSON objects."""

    def __init__(
        self,
        scrubber: PiiRedactionScrubber = DEFAULT_SCRUBBER,
        telemetry: TelemetryManager = DEFAULT_TELEMETRY,
    ) -> None:
        super().__init__()
        self.scrubber = scrubber
        self.telemetry = telemetry

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = self.telemetry.get_current_trace_context()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": self.scrubber.scrub_text(record.getMessage()),
            "logging.googleapis.com/trace": trace_id,
            "logging.googleapis.com/spanId": span_id,
        }
        extra_metadata = getattr(record, "structured_data", None)
        if isinstance(extra_metadata, dict):
            payload.update(self.scrubber.scrub_payload(extra_metadata))
        return json.dumps(payload, default=str)


class StructuredJsonLogger:
    """Structured JSON logger with automatic PII scrubbing and in-memory audit buffer."""

    def __init__(
        self,
        name: str = "software_factory",
        scrubber: PiiRedactionScrubber = DEFAULT_SCRUBBER,
        telemetry: TelemetryManager = DEFAULT_TELEMETRY,
        enable_cloud_logging: bool = False,
        project_id: str | None = None,
    ) -> None:
        self.scrubber = scrubber
        self.telemetry = telemetry
        self.records: list[dict[str, Any]] = []

        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        if not self._logger.handlers:
            stream_handler = logging.StreamHandler(sys.stderr)
            stream_handler.setFormatter(
                JsonLogFormatter(scrubber=scrubber, telemetry=telemetry)
            )
            self._logger.addHandler(stream_handler)

        if enable_cloud_logging and cloud_logging is not None and project_id:
            try:
                client = cloud_logging.Client(project=project_id)
                cloud_handler = client.get_default_handler()
                self._logger.addHandler(cloud_handler)
            except Exception:
                pass

    def log_event(
        self,
        event_type: str,
        message: str,
        *,
        severity: str = "INFO",
        agent_name: str | None = None,
        session_id: str | None = None,
        workspace_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Emits a structured JSON log entry after scrubbing PII and secrets."""
        trace_id, span_id = self.telemetry.get_current_trace_context()
        scrubbed_message = self.scrubber.scrub_text(message)
        scrubbed_metadata = self.scrubber.scrub_payload(metadata or {})

        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity.upper(),
            "event_type": event_type,
            "message": scrubbed_message,
            "agent_name": agent_name or "focal_coordinator_agent",
            "session_id": session_id or "default-session",
            "workspace_path": workspace_path,
            "trace_id": trace_id,
            "span_id": span_id,
            "metadata": scrubbed_metadata,
        }
        self.records.append(entry)

        level = getattr(logging, severity.upper(), logging.INFO)
        self._logger.log(
            level,
            scrubbed_message,
            extra={"structured_data": entry},
        )
        return entry


DEFAULT_LOGGER = StructuredJsonLogger()
