# Proposal: A2A Agent Graph Software Factory & API

## Why
Engineers working across local and external workspaces need an automated, policy-governed Agent-to-Agent (A2A) Software Factory behind a single conversational API focal point. This factory must be able to:
1. Receive conversational intent from a user and report unified multi-agent state back to the user.
2. Operate on both the local workspace and external workspaces/projects by onboarding them via keyless Workload Identity Federation (WIF).
3. Enforce a hard git governance boundary: never push directly to `main`; always create isolated feature branches from `main`, commit with full `Why`/`What`/`Verification` context, and open Pull Requests so GitHub Actions executes `terraform apply` against Argolis.
4. Continuously probe live GCP resources, read Cloud Logging entries, and verify deployed infrastructure via a strictly read-only `gcloud` agent (`cloudtop-agent-reader`).
5. Fulfill all 19 engineering criteria (95/95 points) of the **AI in 5 Days Assessment Agent** code review rubric.

## What Changes
- **Unified FastAPI + A2A Server (`software_factory/api/server.py`, `main.py`)**:
  - Single conversational focal endpoint (`POST /api/v1/chat`) plus structured endpoints (`/api/v1/workspaces/build`, `/api/v1/workspaces/onboard`, `/api/v1/probe`, `/api/v1/approvals/{approval_id}`, `/api/v1/observability/*`).
  - Mounted A2A Starlette sub-apps (`/a2a/focal`, `/a2a/architect`, `/a2a/builder`, `/a2a/wif_delivery`, `/a2a/gcloud_probe`) exposing `/.well-known/agent.json` AgentCards and JSON-RPC endpoints.
- **Multi-Agent ADK Graph (`software_factory/agents/`)**:
  - `focal_coordinator_agent` (`LlmAgent` on `gemini-2.5-pro`)
  - `workspace_architect_agent` (`LlmAgent` on `gemini-2.5-pro`)
  - `software_builder_agent` (`LlmAgent` on `gemini-2.5-pro`)
  - `wif_git_delivery_agent` (`LlmAgent` on `gemini-2.5-pro`)
  - `gcloud_readonly_probe_agent` (`LlmAgent` on `gemini-2.5-flash`)
  - `software_delivery_pipeline` (`SequentialAgent`) and `parallel_verification_agent` (`ParallelAgent`)
  - `RemoteA2aAgent` distributed mesh connectors.
- **AgentOps Engineering Rubric Pillars**:
  - **Tools & Schemas (`software_factory/tools/`, `software_factory/schemas/`)**: 11 domain-specific tools with comprehensive docstrings, strict Pydantic v2 schemas, and `GuidedToolResponse` recovery steps.
  - **Context & Memory (`software_factory/memory/`)**: System constitutions, ADK `EventsCompactionConfig` + `ContextCacheConfig` + sliding-window `ConversationHistoryCompactor`, persistent SQLite/Vertex session & vector memory store, and non-blocking `AsyncMemoryConsolidator`.
  - **Orchestration & Guardrails (`software_factory/orchestration/`)**: `StrategicModelRouter` (Pro vs. Flash), `SoftwareFactoryGuardrailsPlugin` (`BasePlugin` + Model Armor + branch/read-only enforcement), and `HumanInTheLoopGate`.
  - **Observability & Tracing (`software_factory/observability/`)**: `StructuredJsonLogger`, `IntentOutcomeRecorder` (before/after callbacks), `TelemetryManager` (OpenTelemetry + Cloud Trace), and `PiiRedactionScrubber` (Cloud DLP + regex).
  - **Infrastructure & Evaluation (`terraform/`, `software_factory/infrastructure/`, `evals/`, `tests/`)**: Secret Manager vault, complete Argolis Terraform configuration, golden evaluation dataset (`evals/golden_dataset.evalset.json`), and automated CI test workflow.

## Non-Goals
- Direct execution of `terraform apply` from the local Cloudtop workstation (all applies must run via GitHub Actions WIF on merge to `main`).
- Direct commits or pushes to `main`.
