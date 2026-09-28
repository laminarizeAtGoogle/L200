# Google Operational Knowledge Framework (OKF) Specification

This specification defines the standard structure, schema, and quality criteria for component entries within the `./docs/knowledge_base/` catalog.

---

## Purpose & Scope

The **Operational Knowledge Framework (OKF)** standardizes architectural and operational knowledge for enterprise and Google Cloud systems. In this repository, every architectural component represented in the [Dendrite Architecture Diagram](../architecture_diagram.dendrite.yaml) must have a corresponding OKF entry.

---

## OKF Component Schema

Every OKF component file must be stored as a Markdown document under `docs/knowledge_base/components/<component-id>.md` and start with standard YAML frontmatter:

```yaml
---
okf_version: "1.0"
component_id: "string (kebab-case unique identifier matching Dendrite node id)"
component_name: "string (human-readable title)"
category: "string (IAM & Security | Compute & Runtime | Storage & Data | Networking | CI/CD | Dev Tooling)"
tier: "string (Tier 1 - Critical Path | Tier 2 - Operational | Tier 3 - Development)"
status: "string (active | stable | experimental | deprecated)"
owner: "string (responsible team or role)"
dendrite_node_id: "string (exact component ID in docs/architecture_diagram.dendrite.yaml)"
last_verified: "YYYY-MM-DD"
---
```

---

## Required Document Structure

Each OKF entry must include the following five standard sections:

### 1. Executive Summary & Purpose
- High-level overview of the component.
- The specific problem it solves and its primary responsibility within the system.

### 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: The enclosing boundary (e.g., Argolis GCP Project, Cloudtop Workstation, GitHub).
- **Inbound Connections**: Upstream callers, data sources, and triggering events.
- **Outbound Connections**: Downstream dependencies, sinks, and targets.
- **Trust Boundary & Security Classification**: Network isolation level, zero-trust classification.

### 3. Technical Specifications & Configuration
- **Implementation Path(s)**: Concrete file paths in the workspace implementing or configuring this component (e.g., `terraform/`, `scripts/`, `bin/`).
- **Protocols & Interfaces**: Communication protocols (HTTPS, gRPC, STS, SSH) and ports.
- **Configuration & Environment Variables**: Key environment variables, Terraform variables, or flags.
- **IAM Roles & Permissions**: Minimum required IAM roles and service account bindings.

### 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**: How the component is created, initialized, or updated.
- **Verification & Health Checks**: Commands to inspect and verify healthy operation.
- **Failure Modes & Blast Radius**: Impact on the wider system if this component fails or becomes unreachable.
- **Recovery & Troubleshooting**: Step-by-step diagnostic and remediation instructions.

### 5. References & Linked Assets
- Link to corresponding node in `docs/architecture_diagram.dendrite.yaml` and `docs/architecture.md`.
- Cross-references to upstream and downstream OKF component entries.
- Official Google Cloud documentation or internal `go/` links.

---

## Quality Criteria & Validation Rules

1. **Completeness**: Every component declared in `docs/architecture_diagram.dendrite.yaml` must have a matching OKF document in `docs/knowledge_base/components/`.
2. **Determinism**: Component IDs in frontmatter must match file basenames (`<component-id>.md`) and Dendrite diagram IDs.
3. **Actionable Runbooks**: Operational verification and troubleshooting sections must contain executable commands or exact paths.
