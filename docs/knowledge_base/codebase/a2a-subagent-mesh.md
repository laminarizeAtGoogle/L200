---
okf_version: "1.0"
entry_id: "a2a-subagent-mesh"
entry_name: "A2A Multi-Agent Specialist Mesh & Tool Suite"
category: "codebase"
sub_category: "agent_runtime"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "AI Agent Engineering / Academy L200"
dendrite_node_id: "a2a_subagent_mesh"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Codebase): A2A Multi-Agent Specialist Mesh & Tool Suite

## 1. Executive Summary & Purpose
- **Primary Function**: Implements the specialist ADK sub-agents (`workspace_architect_agent`, `software_builder_agent`, `wif_git_delivery_agent`, `gcloud_readonly_probe_agent`), workflow orchestrators (`SequentialAgent`, `ParallelAgent`), `RemoteA2aAgent` connectors, and 11 schema-validated tools.
- **Target Audience / Consumer**: Invoked by `focal_coordinator_agent` or external A2A clients via `/a2a/{architect,builder,wif_delivery,gcloud_probe}`.
- **Key Outcome**: Enables autonomous software generation, cross-project WIF onboarding, isolated feature-branch Pull Request creation, and read-only `gcloud` verification.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `developer_workstation`
- **Inbound Connections**:
  - `a2a_software_factory_api`: Receives delegated sub-tasks via ADK `sub_agents` and A2A JSON-RPC.
- **Outbound Connections**:
  - `github_repo`: Creates feature branches (`create_isolated_feature_branch_from_main`), commits with context, and opens PRs (`open_pull_request_for_terraform_apply`).
  - `reader_sa`: Impersonates `cloudtop-agent-reader` to probe GCP resources (`probe_gcp_resources_readonly`) and read Cloud Logging (`query_cloud_logging_entries_readonly`).
- **Trust Boundary & Security Classification**: Governed by `SoftwareFactoryGuardrailsPlugin` and `HumanInTheLoopGate`.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Sub-agents & workflows: [`software_factory/agents/subagents.py`](../../../software_factory/agents/subagents.py)
  - A2A mesh & AgentCards: [`software_factory/agents/a2a_mesh.py`](../../../software_factory/agents/a2a_mesh.py)
  - Tools: [`software_factory/tools/workspace_tools.py`](../../../software_factory/tools/workspace_tools.py), [`software_factory/tools/git_wif_tools.py`](../../../software_factory/tools/git_wif_tools.py), [`software_factory/tools/gcloud_probe_tools.py`](../../../software_factory/tools/gcloud_probe_tools.py)
  - Guardrails & Routing: [`software_factory/orchestration/guardrails_plugin.py`](../../../software_factory/orchestration/guardrails_plugin.py), [`software_factory/orchestration/model_router.py`](../../../software_factory/orchestration/model_router.py)
- **Protocols & Interfaces**: A2A Protocol (`to_a2a`, `RemoteA2aAgent`), Git CLI, Terraform CLI, `gcloud` CLI.
- **Configuration & Environment Variables**:
  - `FACTORY_READONLY_SA`: Read-only service account email.
  - `FACTORY_DEPLOYER_SA`: WIF deployment service account email.
- **IAM Roles & Permissions**: Read-only local probes (`roles/viewer`); privileged mutations deferred to GitHub Actions WIF.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  ./bin/uv run python -c "import asyncio; from software_factory.agents import build_all_agent_cards; print(list(asyncio.run(build_all_agent_cards()).keys()))"
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/uv run pytest tests/test_software_factory_suite.py -k "multi_agent_patterns" -v
  ```
- **Failure Modes & Blast Radius**:
  - Policy violations return `status="blocked_by_guardrail"` with step-by-step `remediation_steps`.
- **Recovery & Troubleshooting**:
  - Review tool schemas in [`software_factory/schemas/models.py`](../../../software_factory/schemas/models.py).

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `a2a_subagent_mesh` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Focal API: [`codebase/a2a-software-factory-api.md`](a2a-software-factory-api.md)
  - Read-Only SA: [`deployed_gcp_assets/reader-sa.md`](../deployed_gcp_assets/reader-sa.md)
