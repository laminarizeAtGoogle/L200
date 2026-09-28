"""Strategic Model Routing for the A2A Software Factory.

Dynamically selects the optimal Gemini foundation model based on task
complexity, latency requirements, and reasoning depth:
- `gemini-2.5-pro`: Complex multi-agent coordination, architectural planning,
  OpenSpec/Dendrite synthesis, and Terraform/code generation.
- `gemini-2.5-flash`: Fast, low-latency read-only `gcloud` probes, Cloud
  Logging inspection, and status summarization.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

from ..config import DEFAULT_CONFIG, FactoryConfig
from ..observability import DEFAULT_LOGGER


TaskComplexityTier = Literal["deep_planning", "code_synthesis", "fast_execution"]


@dataclass(frozen=True)
class ModelRoutingDecision:
    """Represents the selected model and routing rationale."""

    selected_model: str
    complexity_tier: TaskComplexityTier
    agent_role: str
    rationale: str


class StrategicModelRouter:
    """Routes agent roles and user intents to Pro (planning) or Flash (fast tasks)."""

    _FAST_KEYWORDS = frozenset(
        {
            "probe",
            "status",
            "list",
            "logs",
            "check",
            "verify",
            "ping",
            "health",
            "describe",
            "inspect",
        }
    )

    _PLANNING_KEYWORDS = frozenset(
        {
            "architect",
            "design",
            "build",
            "terraform",
            "wif",
            "refactor",
            "implement",
            "create",
            "onboard",
            "pipeline",
            "multi-agent",
            "pr",
            "pull request",
        }
    )

    def __init__(self, config: FactoryConfig = DEFAULT_CONFIG) -> None:
        self.planning_model = config.planning_model
        self.fast_model = config.fast_model

    def select_model_for_agent(self, agent_name: str) -> ModelRoutingDecision:
        """Selects the foundation model assigned to a specific ADK agent node."""
        lower = agent_name.lower()
        if any(
            token in lower
            for token in (
                "probe",
                "readonly",
                "auditor",
                "inspector",
                "fast",
                "verifier",
            )
        ):
            decision = ModelRoutingDecision(
                selected_model=self.fast_model,
                complexity_tier="fast_execution",
                agent_role=agent_name,
                rationale=(
                    "High-throughput, low-latency read-only GCP resource probing "
                    "and log querying routed to Gemini Flash."
                ),
            )
        elif any(
            token in lower for token in ("builder", "wif", "delivery")
        ):
            decision = ModelRoutingDecision(
                selected_model=self.planning_model,
                complexity_tier="code_synthesis",
                agent_role=agent_name,
                rationale=(
                    "Multi-file code synthesis, Terraform HCL generation, and WIF "
                    "security configuration routed to Gemini Pro."
                ),
            )
        else:
            decision = ModelRoutingDecision(
                selected_model=self.planning_model,
                complexity_tier="deep_planning",
                agent_role=agent_name,
                rationale=(
                    "Architectural planning, A2A graph orchestration, and intent "
                    "decomposition routed to Gemini Pro."
                ),
            )

        DEFAULT_LOGGER.log_event(
            event_type="MODEL_ROUTING_DECISION",
            message=(
                f"Routed agent '{agent_name}' to model '{decision.selected_model}' "
                f"({decision.complexity_tier})"
            ),
            agent_name=agent_name,
            metadata={
                "selected_model": decision.selected_model,
                "complexity_tier": decision.complexity_tier,
                "rationale": decision.rationale,
            },
        )
        return decision

    def route_user_intent(self, prompt: str) -> ModelRoutingDecision:
        """Classifies an incoming user prompt to determine the execution tier."""
        lower = prompt.lower()
        has_planning = any(
            re.search(rf"\b{re.escape(kw)}\b", lower)
            for kw in self._PLANNING_KEYWORDS
        )
        has_fast = any(
            re.search(rf"\b{re.escape(kw)}\b", lower)
            for kw in self._FAST_KEYWORDS
        )

        if has_fast and not has_planning and len(prompt.split()) < 30:
            return ModelRoutingDecision(
                selected_model=self.fast_model,
                complexity_tier="fast_execution",
                agent_role="focal_coordinator_agent",
                rationale=(
                    "Short read-only query/inspection request routed to fast model tier."
                ),
            )

        return ModelRoutingDecision(
            selected_model=self.planning_model,
            complexity_tier="deep_planning",
            agent_role="focal_coordinator_agent",
            rationale=(
                "Software factory build, architectural design, or WIF/PR orchestration "
                "request routed to planning model tier."
            ),
        )


DEFAULT_MODEL_ROUTER = StrategicModelRouter()
