---
okf_version: "1.0"
entry_id: "a2a-software-factory-api"
entry_name: "Unified FastAPI + A2A Focal Coordinator Server"
category: "codebase"
sub_category: "agent_runtime"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "AI Agent Engineering / Academy L200"
dendrite_node_id: "a2a_software_factory_api"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Codebase): Unified FastAPI + A2A Focal Coordinator Server

## 1. Executive Summary & Purpose
- **Primary Function**: Exposes the single conversational focal point API (`POST /api/v1/chat`) and mounts the Agent-to-Agent (A2A) protocol sub-applications (`/a2a/*`) for the Software Factory.
- **Target Audience / Consumer**: Engineers, external workspaces, and A2A client agents requesting automated software builds, cross-project WIF onboarding, feature-branch Pull Requests, and read-only GCP verification.
- **Key Outcome**: Translates user conversational intent into multi-agent actions across target workspaces and synthesizes agent execution state, trace IDs, and pending Human-in-the-Loop approvals back to the user.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `developer_workstation` (local execution) and `argolis_project` (when deployed to Cloud Run v2).
- **Inbound Connections**:
  - `cloudtop_shell`: REST/JSON requests (`POST /api/v1/chat`, `POST /api/v1/workspaces/build`, `POST /api/v1/workspaces/onboard`) and A2A JSON-RPC calls.
- **Outbound Connections**:
  - `a2a_subagent_mesh`: Delegates tasks to `workspace_architect_agent`, `software_builder_agent`, `wif_git_delivery_agent`, and `gcloud_readonly_probe_agent`.
  - `secret_manager_vault`: Retrieves credentials dynamically via Secret Manager and scrubs PII via Cloud DLP.
- **Trust Boundary & Security Classification**: Enforces `SoftwareFactoryGuardrailsPlugin` (`BasePlugin`), `HumanInTheLoopGate`, and OpenTelemetry distributed tracing on every request.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Server factory: [`software_factory/api/server.py`](../../../software_factory/api/server.py)
  - Focal coordinator & ADK App: [`software_factory/agents/focal_agent.py`](../../../software_factory/agents/focal_agent.py)
  - Entrypoints: [`main.py`](../../../main.py), [`software_factory/agent.py`](../../../software_factory/agent.py)
  - Schemas: [`software_factory/schemas/models.py`](../../../software_factory/schemas/models.py)
- **Protocols & Interfaces**: HTTP/1.1 & JSON-RPC 2.0 (`/.well-known/agent.json`), OpenTelemetry (`CloudTraceSpanExporter`), SQLite / Vertex AI Session & Memory stores.
- **Configuration & Environment Variables**:
  - `FACTORY_PLANNING_MODEL` (default `gemini-2.5-pro`)
  - `FACTORY_FAST_MODEL` (default `gemini-2.5-flash`)
  - `FACTORY_PORT` (default `8080`)
- **IAM Roles & Permissions**: Runs under zero-privilege local boundary (`cloudtop-agent-reader`) or `a2a-software-factory-sa` on Cloud Run.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  ./bin/uv run --env-file .env python main.py --serve --port 8080
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/uv run --env-file .env python main.py
  ./bin/uv run pytest tests/test_software_factory_suite.py -v
  ```
- **Failure Modes & Blast Radius**:
  - Unhandled tool errors are intercepted and converted into `GuidedToolResponse` payloads with `remediation_steps`.
  - Protected branch policy blocks any direct commit or push to `main`.
- **Recovery & Troubleshooting**:
  - Inspect Intent vs. Outcome audit trail at `GET /api/v1/observability/audit` and OpenTelemetry spans at `GET /api/v1/observability/spans`.

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `a2a_software_factory_api` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Specialist Mesh: [`codebase/a2a-subagent-mesh.md`](a2a-subagent-mesh.md)
  - ADK Runtime: [`codebase/adk-runtime.md`](adk-runtime.md)
  - Cloud Run Service: [`deployed_gcp_assets/cloud-run-factory-service.md`](../deployed_gcp_assets/cloud-run-factory-service.md)
