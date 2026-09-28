---
okf_version: "1.0"
entry_id: "agent-eval-pipeline"
entry_name: "Golden Dataset Evaluation Harness & CI Pipeline"
category: "codebase"
sub_category: "cicd"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "AI Agent Engineering / Academy L200"
dendrite_node_id: "agent_eval_pipeline"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Codebase): Golden Dataset Evaluation Harness & CI Pipeline

## 1. Executive Summary & Purpose
- **Primary Function**: Statically and dynamically evaluates the A2A Software Factory against a golden benchmark dataset (`evals/golden_dataset.evalset.json`) and executes unit/integration tests on every Pull Request.
- **Target Audience / Consumer**: GitHub Actions CI runners and local developers verifying agent trajectories, model routing, and guardrail compliance.
- **Key Outcome**: Prevents regressions across tool selection, protected-branch enforcement, WIF onboarding, read-only `gcloud` probing, and PII scrubbing.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `github_platform`
- **Inbound Connections**:
  - `github_repo`: Triggered on Pull Requests targeting `main` and pushes to `factory/**` or `feat/**`.
- **Outbound Connections**:
  - `a2a_software_factory_api`: Exercises the Focal Coordinator and A2A endpoints in-memory.
- **Trust Boundary & Security Classification**: Runs hermetically in CI without requiring static cloud credentials.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Golden dataset: [`evals/golden_dataset.evalset.json`](../../../evals/golden_dataset.evalset.json)
  - Evaluation config: [`evals/test_config.json`](../../../evals/test_config.json)
  - Evaluation runner: [`evals/run_evaluation_suite.py`](../../../evals/run_evaluation_suite.py)
  - Pytest suite: [`tests/test_software_factory_suite.py`](../../../tests/test_software_factory_suite.py)
  - GitHub Actions workflow: [`.github/workflows/agent-eval-and-test.yml`](../../../.github/workflows/agent-eval-and-test.yml)
- **Protocols & Interfaces**: `pytest`, `asyncio`, FastAPI `TestClient`.
- **Configuration & Environment Variables**: Configured via `[tool.pytest.ini_options]` in [`pyproject.toml`](../../../pyproject.toml). On public GitHub Actions runners (`ubuntu-latest`), `uv sync --no-config` bypasses the internal Corp Airlock proxy (`uv.toml`) to resolve packages from public PyPI while preserving a clean git working tree.
- **IAM Roles & Permissions**: None required for unit/golden evaluation runs.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  ./bin/uv run python evals/run_evaluation_suite.py
  ```
- **Verification & Health Checks**:
  ```bash
  ./bin/uv run pytest -v
  ```
- **Failure Modes & Blast Radius**:
  - Non-zero exit code blocks PR merge if any golden trajectory or guardrail check regresses below `1.0`.
- **Recovery & Troubleshooting**:
  - Inspect failed `eval_id` entry in the JSON output of `evals/run_evaluation_suite.py`.

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `agent_eval_pipeline` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Focal API: [`codebase/a2a-software-factory-api.md`](a2a-software-factory-api.md)
  - Terraform Plan CI: [`codebase/gha-plan.md`](gha-plan.md)
