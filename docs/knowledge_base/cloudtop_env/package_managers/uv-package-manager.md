---
okf_version: "1.0"
entry_id: "uv-package-manager"
entry_name: "uv Python Package & Project Manager"
category: "cloudtop_env"
sub_category: "package_managers"
tier: "Tier 3 - Dev/Tooling"
status: "active"
owner: "Developer Productivity / Cloudtop Engineering"
dendrite_node_id: "isolated_binaries"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Cloudtop Env): uv Python Package & Project Manager

## 1. Executive Summary & Purpose
- **Primary Function**: Ultra-fast, hermetic Python package installer, dependency resolver, and virtual environment manager providing sub-second environment synchronizations without polluting the host workstation's system Python.
- **Target Audience / Consumer**: Cloudtop developers, Antigravity AI agents, and Google Agent Development Kit (ADK) execution pipelines.
- **Key Outcome**: Guarantees deterministic, reproducible Python 3.12 environments across developer workstations while proxying package traffic securely through Google corporate network infrastructure.

## 2. Cloudtop Environment Context
- **Sub-Category**: `package_managers`
- **File / Directory Path**:
  - Binary executable: `./bin/uv` (standalone v0.12.16)
  - Proxy configuration: [`uv.toml`](../../../uv.toml)
  - Dependency manifest: [`pyproject.toml`](../../../pyproject.toml)
  - Lockfile: [`uv.lock`](../../../uv.lock)
  - Virtual environment: `./.venv/`
- **Invocation Command / Syntax**:
  ```bash
  # Synchronize virtual environment with lockfile
  ./bin/uv sync

  # Run Python script inside hermetic virtual environment
  ./bin/uv run python main.py

  # Inspect installed packages
  ./bin/uv pip list
  ```
- **Runtime Environment & Dependencies**: Standalone Rust binary compiled for Linux x86_64, Python 3.12, routes upstream HTTP/1.1 traffic via internal Corp Airlock Proxy (`http://airlock-proxy.uplink.goog:999`).
- **Isolation Scope**: Local Cloudtop workstation sandbox; strictly manages `./.venv/` without modifying system libraries or global user Python directories (`~/.local/`).

## 3. Technical Specifications & Configuration
- **Configuration Files**:
  - `uv.toml`:
    ```toml
    allow-insecure-host = ["airlock-proxy.uplink.goog"]

    [[index]]
    url = "http://airlock-proxy.uplink.goog:999/python/artifact-foundry-prod/ah-3p-staging-python/simple/"
    default = true
    ```
  - `pyproject.toml`: Declares `l200-agent-development` project metadata, target Python version (`>=3.12`), and core dependencies (`google-adk[gcp]>=2.9.1`, `pandas`, `ipykernel`).
  - `uv.lock`: Complete pinned SHA256 dependency manifest.
- **Common Commands & Flags**:
  | Command | Purpose | Typical Arguments |
  |---|---|---|
  | `sync` | Reconciles `.venv` against `uv.lock` | `--frozen`, `--no-install-project` |
  | `run` | Executes tools/scripts in virtualenv | `python <script>`, `pytest`, `adk` |
  | `pip list` | Reports installed package versions | `--format=columns` |
  | `venv` | Generates a new isolated virtualenv | `.venv --python 3.12` |
- **Security & Permissions**:
  - Execution mode: User space (`primarygroup`), no `sudo` or host elevation required.
  - Proxy routing: Strictly confined to internal corporate Airlock proxy index, blocking unvetted public PyPI network egress.

## 4. Operational Runbook & Lifecycle
- **Step 1: Usage / Initial Environment Setup**:
  ```bash
  # Ensure local bin is on path or use direct invocation
  ./bin/uv sync
  ```
- **Step 2: Verification & Output Validation**:
  ```bash
  ./bin/uv --version
  ./bin/uv run python -c "import google.adk; print('ADK Version:', google.adk.__version__)"
  ```
- **Step 3: Troubleshooting & Failure Modes**:
  - *Symptom*: `Failed to fetch wheel from index / connection refused`.
    - *Remediation*: Confirm the internal Airlock proxy is reachable (`curl -I http://airlock-proxy.uplink.goog:999`). Ensure `uv.toml` is present in workspace root.
  - *Symptom*: `Interpreter mismatch or corrupted virtualenv`.
    - *Remediation*: Rebuild the virtualenv from scratch:
      ```bash
      rm -rf .venv
      ./bin/uv sync
      ```

## 5. References & Cross-Links
- **Dendrite Diagram Node**: `isolated_binaries` and `adk_runtime` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Canonical Component: [`components/isolated-binaries.md`](../../components/isolated-binaries.md)
  - Runtime Component: [`components/adk-runtime.md`](../../components/adk-runtime.md)
