"""OpenTelemetry distributed tracing setup for the A2A Software Factory.

Configures TracerProvider, span processors, and optional Google Cloud Trace
export so every request is traced end-to-end across the API gateway, Focal
Coordinator, A2A sub-agents, and tools.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

try:
    from opentelemetry.exporter.gcp_trace import CloudTraceSpanExporter
except ImportError:  # pragma: no cover
    CloudTraceSpanExporter = None  # type: ignore[assignment]


class TelemetryManager:
    """Manages OpenTelemetry distributed tracing spans across the agent graph."""

    def __init__(
        self,
        service_name: str = "a2a-software-factory",
        project_id: str | None = None,
        enable_cloud_trace: bool = False,
    ) -> None:
        self.service_name = service_name
        self.project_id = project_id
        self.memory_exporter = InMemorySpanExporter()

        resource = Resource.create(
            {
                "service.name": service_name,
                "cloud.platform": "gcp",
                "gcp.project_id": project_id or "l200-509515",
            }
        )
        self.provider = TracerProvider(resource=resource)
        self.provider.add_span_processor(
            SimpleSpanProcessor(self.memory_exporter)
        )

        if (
            enable_cloud_trace
            and CloudTraceSpanExporter is not None
            and project_id
        ):
            try:
                cloud_exporter = CloudTraceSpanExporter(project_id=project_id)
                self.provider.add_span_processor(
                    BatchSpanProcessor(cloud_exporter)
                )
            except Exception:
                pass

        try:
            trace.set_tracer_provider(self.provider)
        except Exception:
            pass

        self.tracer = self.provider.get_tracer(service_name)

    @contextmanager
    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Starts a linked OpenTelemetry span with structured attributes."""
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, val in attributes.items():
                    if val is not None:
                        span.set_attribute(
                            key,
                            val
                            if isinstance(val, (bool, int, float, str))
                            else str(val),
                        )
            yield span

    def get_current_trace_context(self) -> tuple[str, str]:
        """Returns the current (trace_id_hex, span_id_hex) tuple."""
        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        if ctx and ctx.is_valid:
            return f"{ctx.trace_id:032x}", f"{ctx.span_id:016x}"
        return "0" * 32, "0" * 16

    def get_exported_spans(self) -> list[dict[str, Any]]:
        """Returns serialized spans captured by the in-memory exporter."""
        spans = self.memory_exporter.get_finished_spans()
        results: list[dict[str, Any]] = []
        for s in spans:
            results.append(
                {
                    "name": s.name,
                    "trace_id": f"{s.context.trace_id:032x}",
                    "span_id": f"{s.context.span_id:016x}",
                    "parent_span_id": (
                        f"{s.parent.span_id:016x}" if s.parent else None
                    ),
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "attributes": dict(s.attributes or {}),
                    "status": s.status.status_code.name,
                }
            )
        return results


DEFAULT_TELEMETRY = TelemetryManager()
