---
okf_version: "1.0"
entry_id: "dendrite-architecture-diagrams"
entry_name: "Dendrite Architecture Diagrams Skill"
category: "cloudtop_env"
sub_category: "skills"
tier: "Tier 3 - Dev/Tooling"
status: "active"
owner: "Architecture Governance / Academy L200"
dendrite_node_id: "cloudtop_shell"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Cloudtop Env): Dendrite Architecture Diagrams Skill

## 1. Executive Summary & Purpose
- **Primary Function**: Enforces that all software designs, infrastructure topologies, security perimeters, and data flow models utilize Google's canonical internal **Dendrite** diagram platform ([go/dendrite](http://go/dendrite)) and interactive playground ([go/dendrite-playground](http://go/dendrite-playground)), strictly prohibiting ad-hoc ASCII art box drawings.
- **Target Audience / Consumer**: Antigravity AI agents, system architects, and software engineers contributing to repository documentation.
- **Key Outcome**: Guarantees a declarative, machine-parseable, and visually interactive architecture specification that remains perfectly synchronized with deployed cloud infrastructure and codebase modules.

## 2. Cloudtop Environment Context
- **Sub-Category**: `skills`
- **File / Directory Path**:
  - Skill specification: [`.agents/skills/dendrite-architecture-diagrams/SKILL.md`](../../../.agents/skills/dendrite-architecture-diagrams/SKILL.md)
  - Reference patterns: [`.agents/skills/dendrite-architecture-diagrams/references/diagram_patterns.md`](../../../.agents/skills/dendrite-architecture-diagrams/references/diagram_patterns.md)
- **Invocation Command / Syntax**:
  - Automatically activated by agent prompts matching architecture, topology, or infrastructure planning keywords.
  - Validated on `git push` by `.agents/scripts/check-architecture-docs.sh`.
- **Runtime Environment & Dependencies**: Antigravity Agent Skill Engine, Python 3.12, YAML/JSON parsers.
- **Isolation Scope**: Workspace local agent instructions; affects authoring style and documentation standards within `./docs/`.

## 3. Technical Specifications & Configuration
- **Dendrite Standard Format**:
  Every diagram must contain the top-level `dendrite_diagram:` declaration and authoritative links:
  ```yaml
  dendrite_diagram:
    title: "System Topology"
    version: "1.0.0"
    dendrite_url: "http://go/dendrite"
    playground_url: "http://go/dendrite-playground"
    last_updated: "YYYY-MM-DD"
    boundaries: [...]
    connections: [...]
  ```
- **Diagram Design Rules**:
  1. **Hierarchical Containment**: Use boundary frames (`workstation`, `vcs_cicd`, `security_perimeter`, `gcp_project`).
  2. **Standard Components**: Declare `id`, `label`, `type`, and `role`.
  3. **Directional Flows**: Connections must define `from`, `to`, `protocol`, `auth`, `label`, and `type` (`control`, `data`, `auth`, `provisioning`, `event`).
  4. **Strict ASCII Ban**: Markdown box drawing characters (`+---+`, `|   |`) are prohibited and will trigger pre-push hook denial.

## 4. Operational Runbook & Lifecycle
- **Step 1: Usage / Authoring Workflow**:
  1. Define or update the system model in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml).
  2. Synchronize the embedded code block in [`docs/architecture.md`](../../architecture.md).
  3. Ensure every diagram node has a matching component entry in `docs/knowledge_base/components/<node_id>.md`.
- **Step 2: Verification & Validation**:
  ```bash
  # Run the pre-push gate locally to verify Dendrite compliance
  python3 .agents/scripts/check_architecture_docs.py
  ```
- **Step 3: Troubleshooting & Failure Modes**:
  - *Symptom*: Pre-push gate rejects push with `contains markdown/ASCII box drawing`.
    - *Remediation*: Search `docs/` for `+---` and replace with valid Dendrite YAML specification.

## 5. References & Cross-Links
- **Authoritative Platform**: [go/dendrite](http://go/dendrite) | [go/dendrite-playground](http://go/dendrite-playground)
- **Repository Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Declarative Architecture Model**: [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Pre-Push Validation Gate**: [`cloudtop_env/scripts/check-architecture-docs.md`](../scripts/check-architecture-docs.md)
- **Subagent Automation**: `.agents/skills/update-architecture-docs/SKILL.md`
