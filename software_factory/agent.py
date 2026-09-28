"""Google ADK Agent Entrypoint (`software_factory/agent.py`).

Exposes `root_agent` and `app` so that `adk web`, `adk run`, and `adk eval`
can discover and run the A2A Software Factory agent graph directly.
"""

from __future__ import annotations

from .agents import (
    build_focal_coordinator_agent,
    build_software_factory_adk_app,
)

root_agent = build_focal_coordinator_agent()
app = build_software_factory_adk_app()

__all__ = ["app", "root_agent"]
