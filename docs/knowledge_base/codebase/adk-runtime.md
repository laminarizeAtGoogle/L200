---
okf_version: "1.0"
entry_id: "adk-runtime"
entry_name: "Google ADK Agent Runtime & Python Toolchain"
category: "codebase"
sub_category: "agent_runtime"
tier: "Tier 2 - Operational"
status: "active"
owner: "AI Agent Engineering / Academy L200"
dendrite_node_id: "adk_runtime"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Codebase): Google ADK Agent Runtime & Python Toolchain

## 1. Executive Summary & Purpose
The Google ADK Agent Runtime provides the Python 3.12 execution framework for Google Agent Development Kit (ADK) agents, tools, orchestration, and evaluation pipelines within the L200 workspace. It provides hermetic package management via `uv` routed through the internal Corp Airlock proxy.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `developer_workstation`
- **Inbound Connections**:
  - `cloudtop_shell`: Developer CLI commands and Antigravity subagent orchestration.
- **Outbound Connections**:
  - Vertex AI Model APIs: Gemini 1.5 Pro / Flash inference endpoints.
  - Airlock Proxy (`http://airlock-proxy.uplink.goog:999`): Internal dependency resolution.
- **Trust Boundary & Security Classification**: Isolated virtualenv (`.venv`) on Cloudtop; no direct public internet egress for Python packages.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Runtime definition: [`pyproject.toml`](../../../pyproject.toml)
  - Lockfile: [`uv.lock`](../../../uv.lock)
  - Package proxy config: [`uv.toml`](../../../uv.toml)
  - Verification script: [`main.py`](../../../main.py)
- **Protocols & Interfaces**: HTTP/1.1 (Airlock proxy), HTTPS / gRPC (Vertex AI endpoints).
- **Configuration & Environment Variables**:
  - `VIRTUAL_ENV`: Path to `./.venv`
  - `PYTHONPATH`: Workspace root
- **Dependencies**:
  - `google-adk[gcp] >= 2.9.1`
  - `pandas`, `ipykernel`

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  ./bin/uv sync
  ./bin/uv run python main.py
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/uv run adk --version
  ./bin/uv run python -c "import google.adk; print(google.adk.__version__)"
  ```
- **Failure Modes & Blast Radius**:
  - Dependency drift or broken virtualenv prevents local agent execution. Does not impact remote GCP infrastructure.
- **Recovery & Troubleshooting**:
  - Recreate venv: `rm -rf .venv && ./bin/uv sync`

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `adk_runtime` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **ADK Documentation**: `https://google.github.io/adk-docs/`
- **Related OKF Entries**:
  - Workstation Shell: [`cloudtop_env/workstation/cloudtop-shell.md`](../cloudtop_env/workstation/cloudtop-shell.md)
  - Package Manager: [`cloudtop_env/package_managers/uv-package-manager.md`](../cloudtop_env/package_managers/uv-package-manager.md)
  - Standalone Binaries: [`cloudtop_env/package_managers/isolated-binaries.md`](../cloudtop_env/package_managers/isolated-binaries.md)
