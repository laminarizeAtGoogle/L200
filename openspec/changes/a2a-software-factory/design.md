# Design: A2A Agent Graph Software Factory

## System Architecture Diagram
> **Canonical Architecture Diagram**: Authored in **Mermaid** (`docs/architecture.md`)  
> **Authoritative Source**: [`docs/architecture_diagram.mmd`](../../../docs/architecture_diagram.mmd)

## Architectural Decisions

1. **Unified FastAPI + A2A Server Topology**:
   - The Focal Conversational Coordinator is exposed at `POST /api/v1/chat` to provide a stateful single point of interaction for the user while each specialist agent (`focal`, `architect`, `builder`, `wif_delivery`, `gcloud_probe`) is mounted via `google.adk.a2a.utils.agent_to_a2a.to_a2a` under `/a2a/<agent>` with standard A2A `/.well-known/agent.json` discovery.

2. **Strict Branch & WIF Delivery Model**:
   - `SoftwareFactoryGuardrailsPlugin` intercepts tool invocations prior to execution and blocks any commit, push, or PR head branch targeting `main` or `master` (`PROTECTED_BRANCH_VIOLATION`).
   - All changes are written to an isolated feature branch (`feat/*` or `factory/*`) created from `main` via `create_isolated_feature_branch_from_main`, committed with `Why`/`What`/`Verification` sections, and delivered via Pull Request to trigger GitHub Actions (`terraform-plan.yml` and `terraform-apply.yml`) authenticated via Workload Identity Federation.

3. **Zero-Privilege Read-Only Verification**:
   - `gcloud_readonly_probe_agent` is routed to `gemini-2.5-flash` for low-latency resource and log inspection and strictly impersonates `cloudtop-agent-reader@<PROJECT_ID>.iam.gserviceaccount.com`.
   - Any mutating `gcloud` verb is rejected by `SoftwareFactoryGuardrailsPlugin` (`ZERO_PRIVILEGE_READONLY_VIOLATION`).
