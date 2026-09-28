---
okf_version: "1.0"
entry_id: "cloudtop-shell"
entry_name: "Cloudtop Terminal & Antigravity Shell"
category: "cloudtop_env"
sub_category: "workstation"
tier: "Tier 3 - Development"
status: "active"
owner: "Developer Productivity / Cloudtop Engineering"
dendrite_node_id: "cloudtop_shell"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Cloudtop Env): Cloudtop Terminal & Antigravity Shell

## 1. Executive Summary & Purpose
The Cloudtop Terminal & Antigravity Shell provides the interactive, authenticated development workstation environment on Google Cloudtop (`/usr/local/google/home/joshholtz/Documents/L200`). It serves as the primary developer and AI pairing interface for writing code, running terraform plans, executing agent workflows, and initiating git operations.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `developer_workstation`
- **Inbound Connections**:
  - Direct engineer CLI interactions, Antigravity IDE agent commands.
- **Outbound Connections**:
  - `github_repo`: Git commands (`git commit`, `git push`) gated by pre-tool-use hooks.
  - `reader_sa`: Impersonates `cloudtop-agent-reader` Service Account via Google ADC.
  - `adk_runtime`: Spawns and supervises ADK Python execution.
- **Trust Boundary & Security Classification**: Internal Google Corp Network / Cloudtop workstation boundary. Zero static credentials stored on disk.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Workstation environment configuration: [`.env`](../../../../.env)
  - Pre-command hook definitions: [`.agents/hooks.json`](../../../../.agents/hooks.json)
  - Helper scripts: [`relocate.sh`](../../../../relocate.sh)
- **Protocols & Interfaces**: Bash 5.2, POSIX shell, SSH over corp proxy.
- **Configuration & Environment Variables**:
  - `CLOUDSDK_CONFIG`: Isolates gcloud settings to `./.gcloud`
  - `PATH`: Prefixes `./bin` to prioritize hermetic binaries
  - `GOOGLE_APPLICATION_CREDENTIALS`: Ephemeral ADC tokens
- **IAM Roles & Permissions**:
  - Bound to developer's corporate identity (`@google.com`).
  - Permitted to impersonate `cloudtop-agent-reader` for read-only inspection.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  source .env
  source .venv/bin/activate
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/argolis status
  git status
  ```
- **Failure Modes & Blast Radius**:
  - Shell misconfiguration impacts local agent commands. Blast radius is strictly confined to local workspace without affecting remote Argolis infrastructure or GitHub.
- **Recovery & Troubleshooting**:
  - Run `./relocate.sh` to refresh absolute workspace paths and reset environment exports.

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `cloudtop_shell` in [`docs/architecture_diagram.dendrite.yaml`](../../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../../architecture.md)
- **Related OKF Entries**:
  - Agent Runtime: [`codebase/adk-runtime.md`](../../codebase/adk-runtime.md)
  - Standalone Binaries: [`cloudtop_env/package_managers/isolated-binaries.md`](../package_managers/isolated-binaries.md)
  - Pre-Push Gate: [`cloudtop_env/scripts/check-architecture-docs.md`](../scripts/check-architecture-docs.md)
