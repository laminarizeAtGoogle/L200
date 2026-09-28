---
okf_version: "1.0"
component_id: "github-repo"
component_name: "GitHub Repository (L200)"
category: "CI/CD"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Platform Engineering / Core Workspace"
dendrite_node_id: "github_repo"
last_verified: "2026-09-28"
---

# OKF: GitHub Repository (L200)

## 1. Executive Summary & Purpose
The GitHub Repository represents the authoritative version control repository for the L200 project. It stores Terraform manifests, deployment workflows, agent configuration, OpenSpec change specs, and architecture documentation. All updates pushed to this repository trigger automated CI/CD and are gated by client-side pre-push hooks.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `github_platform`
- **Inbound Connections**:
  - `cloudtop_shell`: Receives commits and pushes via HTTPS/SSH.
- **Outbound Connections**:
  - `gha_plan`: Webhook event on PR creation/sync targeting `main`.
  - `gha_apply`: Webhook event on pull request merge to `main`.
- **Trust Boundary & Security Classification**: GitHub Enterprise Cloud. Strict `.gitignore` rules prevent secret leakage.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Repository root: `/usr/local/google/home/joshholtz/Documents/L200`
  - Ignore rules: [`.gitignore`](../../.gitignore)
  - Workflows: [`.github/workflows/`](../../.github/workflows/)
  - Client-side Pre-push gates: [`.agents/hooks.json`](../../.agents/hooks.json)
- **Protocols & Interfaces**: Git over SSH (`git@github.com:...`) and HTTPS (`https://github.com/...`).
- **Branch Protection Rules**:
  - Target branch: `main`
  - Required checks: `Terraform Plan` (`terraform-plan.yml`)

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Configured via git remote:
    ```bash
    git remote add origin https://github.com/<OWNER>/<REPO>.git
    ```
- **Verification & Health Checks**:
  ```bash
  git status
  git remote -v
  ```
- **Failure Modes & Blast Radius**:
  - Git push rejection if sanitization checks or architecture docs gate fail. Prevents unauthorized or undocumented code from entering production branches.
- **Recovery & Troubleshooting**:
  - Review rejection reason emitted by `git-push-architecture-docs-gate` or `git-push-sanitization-gate`.

## 5. References & Linked Assets
- Dendrite Diagram Node: `github_repo` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Related OKF Entries: [`gha-plan`](gha-plan.md), [`gha-apply`](gha-apply.md)
