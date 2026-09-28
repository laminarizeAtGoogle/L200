---
okf_version: "1.0"
component_id: "isolated-binaries"
component_name: "Hermetic Standalone Toolchain (./bin)"
category: "Dev Tooling"
tier: "Tier 3 - Development"
status: "active"
owner: "DevOps / Workspace Infrastructure"
dendrite_node_id: "isolated_binaries"
last_verified: "2026-09-28"
---

# OKF: Hermetic Standalone Toolchain (./bin)

## 1. Executive Summary & Purpose
The Hermetic Standalone Toolchain contains dedicated, architecture-specific binaries compiled for Linux x86_64 and committed/symlinked directly under `./bin`. This eliminates host-level package dependencies, version conflicts, or need for root access on Cloudtop.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `developer_workstation`
- **Inbound Connections**:
  - `cloudtop_shell`: Commands executed by engineers and Antigravity agents.
- **Outbound Connections**:
  - `github_repo`: Interacted with via `./bin/gh` and `./bin/openspec`.
  - `argolis_project`: Managed via `./bin/terraform` and `./bin/argolis`.
- **Trust Boundary & Security Classification**: Local filesystem binaries with execute permissions (`0750`).

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - `./bin/terraform`: Terraform v1.16.4 standalone executable
  - `./bin/gh`: GitHub CLI v2.101.0
  - `./bin/uv`: Python package manager v0.12.16
  - `./bin/argolis`: Compute Engine management wrapper
  - `./bin/openspec`: OpenSpec CLI v1.13.1
  - `./bin/gcloud`: Isolated Google Cloud SDK wrapper
- **Protocols & Interfaces**: Local Linux POSIX system calls.
- **Configuration & Environment Variables**:
  - Prepend `./bin` to `PATH` in `.env`.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Relocation script updates symlinks: `./relocate.sh`
- **Verification & Health Checks**:
  ```bash
  ./bin/terraform -version
  ./bin/gh --version
  ./bin/uv --version
  ./bin/openspec --version
  ```
- **Failure Modes & Blast Radius**:
  - Missing executable permissions or missing shared library dependencies prevent local tool calls.
- **Recovery & Troubleshooting**:
  - Check file permissions: `chmod +x ./bin/*`

## 5. References & Linked Assets
- Dendrite Diagram Node: `isolated_binaries` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Related OKF Entries: [`cloudtop-shell`](cloudtop-shell.md), [`adk-runtime`](adk-runtime.md)
