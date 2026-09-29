# Specification: A2A Agent Graph Software Factory

## Requirement 1: Single Conversational Focal Point & A2A Protocol Mesh
The system SHALL expose a single conversational endpoint (`POST /api/v1/chat`) backed by `focal_coordinator_agent` and mount standard A2A protocol endpoints (`/a2a/<agent>/.well-known/agent.json`) for all specialist agents.

## Requirement 2: Cross-Workspace & Cross-Project WIF Onboarding
The system SHALL be capable of inspecting, generating software and Terraform modules for, and configuring keyless OIDC Workload Identity Federation (`configure_cross_project_wif_federation`) in workspaces and GCP projects outside its own host project.

## Requirement 3: Protected Main Branch & PR-Driven Terraform Apply
The system MUST NOT commit or push directly to `main`. All changes MUST occur on an isolated feature branch created from `main` and be delivered via Pull Request (`open_pull_request_for_terraform_apply`) with Human-in-the-Loop confirmation (`request_human_approval_for_high_stakes_action`) for high-stakes actions.

## Requirement 4: Read-Only gcloud Resource & Log Verification
The system SHALL provide a read-only `gcloud` agent (`gcloud_readonly_probe_agent`) impersonating `cloudtop-agent-reader` to probe GCP resources, query Cloud Logging, and verify deployed infrastructure.

## Requirement 5: Full 95-Point AgentOps Rubric Compliance
The codebase SHALL implement:
- Strict Pydantic v2 tool schemas and `GuidedToolResponse` error remediation;
- System constitutions, ADK `EventsCompactionConfig`, `ContextCacheConfig`, persistent SQLite/vector memory store, and async background memory consolidation;
- Coordinator, Sequential, and Parallel ADK multi-agent patterns, strategic Pro/Flash model routing, ADK `BasePlugin` guardrails, and HITL hooks;
- Structured JSON logging, pre/post Intent-vs-Outcome capture, OpenTelemetry tracing, and Cloud DLP + regex PII redaction;
- Secret Manager integration, validated Terraform modules, and a golden dataset evaluation harness (`evals/run_evaluation_suite.py`).
