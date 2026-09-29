"""Agent-to-Agent (A2A) Protocol Mesh & RemoteA2aAgent Wiring.

Exposes the Focal Coordinator and each specialist ADK agent as standard A2A
protocol endpoints (`/.well-known/agent.json` + JSON-RPC via `to_a2a`) and
provides `RemoteA2aAgent` client connectors for distributed multi-agent
communication.
"""

from __future__ import annotations

from typing import Any

from google.adk.a2a._compat import a2a_to_dict
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..config import DEFAULT_CONFIG, FactoryConfig
from ..orchestration import DEFAULT_MODEL_ROUTER
from ..prompts import FOCAL_COORDINATOR_CONSTITUTION
from .focal_agent import build_focal_coordinator_agent
from .subagents import (
    build_gcloud_readonly_probe_agent,
    build_software_builder_agent,
    build_wif_git_delivery_agent,
    build_workspace_architect_agent,
)


A2A_AGENT_ROUTES: dict[str, str] = {
    "focal_coordinator_agent": "/a2a/focal",
    "workspace_architect_agent": "/a2a/architect",
    "software_builder_agent": "/a2a/builder",
    "wif_git_delivery_agent": "/a2a/wif_delivery",
    "gcloud_readonly_probe_agent": "/a2a/gcloud_probe",
}


def _attach_legacy_well_known_route(
    app: Starlette,
    agent_instance: LlmAgent,
    rpc_url: str,
) -> Starlette:
    """Ensures both `/.well-known/agent.json` and `/.well-known/agent-card.json` work."""

    async def _serve_agent_json(_request: Request) -> JSONResponse:
        builder = AgentCardBuilder(agent=agent_instance, rpc_url=rpc_url)
        card = await builder.build()
        return JSONResponse(a2a_to_dict(card))

    app.routes.append(
        Route("/.well-known/agent.json", endpoint=_serve_agent_json, methods=["GET"])
    )
    return app


def create_a2a_subapps(
    config: FactoryConfig = DEFAULT_CONFIG,
) -> dict[str, Starlette]:
    """Creates Starlette A2A applications for the Focal Agent and all 4 specialist agents."""
    host = "localhost" if config.host == "0.0.0.0" else config.host
    port = config.port
    base_url = f"http://{host}:{port}"

    specs = {
        "/a2a/focal": build_focal_coordinator_agent(
            name="a2a_focal_coordinator_agent"
        ),
        "/a2a/architect": build_workspace_architect_agent(
            name="a2a_workspace_architect_agent"
        ),
        "/a2a/builder": build_software_builder_agent(
            name="a2a_software_builder_agent"
        ),
        "/a2a/wif_delivery": build_wif_git_delivery_agent(
            name="a2a_wif_git_delivery_agent"
        ),
        "/a2a/gcloud_probe": build_gcloud_readonly_probe_agent(
            name="a2a_gcloud_readonly_probe_agent"
        ),
    }

    subapps: dict[str, Starlette] = {}
    for route_prefix, agent_obj in specs.items():
        subapp = to_a2a(
            agent_obj,
            host=host,
            port=port,
            protocol="http",
        )
        subapps[route_prefix] = _attach_legacy_well_known_route(
            subapp,
            agent_obj,
            f"{base_url}{route_prefix}/",
        )
    return subapps


async def build_all_agent_cards(
    base_url: str = "http://localhost:8080",
) -> dict[str, dict[str, Any]]:
    """Builds and serializes A2A AgentCards for every agent in the Software Factory."""
    agents_map = {
        "focal_coordinator_agent": (
            build_focal_coordinator_agent(name="card_focal_coordinator_agent"),
            f"{base_url}/a2a/focal/",
        ),
        "workspace_architect_agent": (
            build_workspace_architect_agent(
                name="card_workspace_architect_agent"
            ),
            f"{base_url}/a2a/architect/",
        ),
        "software_builder_agent": (
            build_software_builder_agent(name="card_software_builder_agent"),
            f"{base_url}/a2a/builder/",
        ),
        "wif_git_delivery_agent": (
            build_wif_git_delivery_agent(name="card_wif_git_delivery_agent"),
            f"{base_url}/a2a/wif_delivery/",
        ),
        "gcloud_readonly_probe_agent": (
            build_gcloud_readonly_probe_agent(
                name="card_gcloud_readonly_probe_agent"
            ),
            f"{base_url}/a2a/gcloud_probe/",
        ),
    }

    cards: dict[str, dict[str, Any]] = {}
    for key, (agent_instance, rpc_url) in agents_map.items():
        builder = AgentCardBuilder(agent=agent_instance, rpc_url=rpc_url)
        card = await builder.build()
        cards[key] = a2a_to_dict(card)
    return cards


def build_remote_a2a_coordinator_graph(
    base_url: str = "http://localhost:8080",
) -> LlmAgent:
    """Constructs a distributed Coordinator Agent wired to `RemoteA2aAgent` sub-agents."""
    routing = DEFAULT_MODEL_ROUTER.select_model_for_agent(
        "remote_a2a_focal_coordinator"
    )
    remote_subagents = [
        RemoteA2aAgent(
            name="remote_workspace_architect",
            agent_card=f"{base_url}/a2a/architect/.well-known/agent.json",
            description="Remote A2A Workspace Architect & Spec Specialist.",
        ),
        RemoteA2aAgent(
            name="remote_software_builder",
            agent_card=f"{base_url}/a2a/builder/.well-known/agent.json",
            description="Remote A2A Software & Cross-Project Terraform Builder.",
        ),
        RemoteA2aAgent(
            name="remote_wif_git_delivery",
            agent_card=f"{base_url}/a2a/wif_delivery/.well-known/agent.json",
            description="Remote A2A WIF Onboarding, Branch & PR Delivery Agent.",
        ),
        RemoteA2aAgent(
            name="remote_gcloud_readonly_probe",
            agent_card=f"{base_url}/a2a/gcloud_probe/.well-known/agent.json",
            description="Remote A2A Read-Only gcloud Resource & Log Verifier.",
        ),
    ]
    return LlmAgent(
        name="remote_a2a_focal_coordinator",
        model=routing.selected_model,
        description=(
            "Distributed A2A Coordinator delegating over HTTP JSON-RPC to "
            "RemoteA2aAgent specialists."
        ),
        instruction=FOCAL_COORDINATOR_CONSTITUTION,
        sub_agents=remote_subagents,
    )
