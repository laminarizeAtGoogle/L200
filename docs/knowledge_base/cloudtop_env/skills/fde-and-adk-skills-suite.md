---
okf_version: "1.0"
component_id: "fde-and-adk-skills-suite"
name: "FDE & Official ADK-Python Agent Skills Catalog"
category: "cloudtop_env"
subcategory: "skills"
status: "active"
owner: "cloudtop-admin"
last_updated: "2026-10-01"
tags:
  - "agent-skills"
  - "adk-python"
  - "fde-harness"
  - "okf"
---

# FDE & Official ADK-Python Agent Skills Catalog (`.agents/skills/` & `.agents/skill-library/`)

## 1. Overview & Purpose
Mounted via the [`cloud-ai-fde/fde-agent-factory`](https://github.com/cloud-ai-fde/fde-agent-factory) Git submodule at [`.agents/`](../../../../.agents/) (configured via [`.gitmodules`](../../../../.gitmodules) and [`./.agents/install.sh --link`](../../../../.agents/install.sh)), providing a reusable two-tier AI engineering customization architecture documented in [`.agents/README.md`](../../../../.agents/README.md):
1. **Pre-Loaded Core Skills (`.agents/skills/` — 25 Skills)**: Always-active YAML frontmatter in the `<skills>` system prompt, kept within the 15–25 routing sweet spot:
   - **11 Official Google ADK-Python Skills** from [`google/adk-python`](https://github.com/google/adk-python/tree/main) (`.agents/skills/adk-*`).
   - **6 Core Production FDE Skills** (`fde-genai-sdk`, `fde-mcp-server-builder`, `fde-a2ui-skills`, `fde-gcp-architect`, `fde-cloud-run-builder`, `fde-cross-compliance`).
   - **8 OpenSpec & Governance Skills** (`openspec-*`, `git-push-sanitization-check`, `update-architecture-docs`).
2. **On-Demand Skill Library (`.agents/skill-library/` — 13 Skills)**: Deliverable, audit, domain, and meta-tooling FDE skills stored off the auto-discovery path so they consume zero system-prompt tokens on normal turns, invoked ad-hoc by the user via `/fde-*` workflows in [`.agents/workflows/`](../../../../.agents/workflows/) and [`.gemini/commands/fde/`](../../../../.gemini/commands/fde/).
3. **Symlinked Governance & OKF Templates**: [`AGENTS.md`](../../../../AGENTS.md), [`.gitmessage.txt`](../../../../.gitmessage.txt), [`docs/knowledge_base/OKF_SPEC.md`](../../OKF_SPEC.md), [`docs/knowledge_base/TEMPLATE.md`](../../TEMPLATE.md), and [`docs/knowledge_base/templates`](../../templates) are symlinked directly into `.agents/` so local edits propagate to the shared plugin repository.

## 2. Installed Skills Breakdown

### A. Official ADK-Python Skills (`.agents/skills/adk-*` — Pre-Loaded)
- `adk-agent-builder`: Builds ADK Python LLM agents, function/agent graph workflows, conditional routing, fan-out/JoinNode, task-mode delegation, HITL `RequestInput`, and `pytest` tests.
- `adk-architecture`: Explains ADK runtime internals (`BaseNode`, `Workflow`, `Runner`, `Agent`, `Context`, `Event`, checkpoint/resume, tracing).
- `adk-debug`: Diagnoses ADK agent sessions, events, tool calls, `adk run` CLI, and `adk web` debug endpoints.
- `adk-git`: Conventional Commits and PR conventions for ADK repositories.
- `adk-review`: Reviews local ADK changes for correctness, public API stability, tests, and docs.
- `adk-sample-creator`: Scaffolds standardized ADK sample agents.
- `adk-setup`: Bootstraps ADK Python development environments.
- `adk-style`: Enforces ADK Python style conventions (Pydantic v2, typing, async I/O, visibility, docstrings).
- `adk-unit-design`: Authors as-built architecture design docs for ADK code units.
- `adk-unit-guide`: Authors hands-on developer usage guides for ADK code units.
- `adk-verify-snippets`: Extracts and executes Python code blocks in Markdown files to verify runnable documentation.

### B. Core Production Cloud AI FDE Skills (`.agents/skills/fde-*` — Pre-Loaded)
- `fde-genai-sdk`: Unified `google-genai` SDK patterns (`genai.Client`, multimodal, Pydantic structured outputs, grounding, thinking).
- `fde-mcp-server-builder`: Production `FastMCP` server design, Pydantic validation, pagination, and self-healing errors.
- `fde-a2ui-skills` (from `feat/a2ui-skills` `ce655cd`): Gemini Enterprise A2UI v0.9 component builder and validator.
- `fde-gcp-architect`: Cloud Run, Vertex AI Agent Engine, IAM least-privilege, and Secret Manager architecture.
- `fde-cloud-run-builder` (from `4526bd5`): Cloud Run source deployment via Buildpacks (`deploy.sh`).
- `fde-cross-compliance` (from `feat/fde-cross-compliance` `4526bd5`, PR #23): OSPO & client delivery sanitization toolkit (`sanitize_repo.sh`).

### C. On-Demand FDE Skill Library (`.agents/skill-library/fde-*` — Manual `/fde-*` Triggers)
- Deliverable & Diagramming: `fde-mermaid-chart` (`/fde-mermaid`), `fde-presentation-skill` (`/fde-slides`), `fde-google-docs` (`/fde-gdocs`), `fde-project-manager` (`/fde-pm`).
- Domain & Audits: `fde-catalog-enhancement` (`/fde-catalog`), `fde-agentic-code-audit` (`/fde-audit`), `fde-model-migration-audit` (`/fde-migrate`).
- Meta & Git Tooling: `fde-git-push` (`/fde-git-push`), `fde-skill-creator` (`/fde-skill-create`), `fde-skill-auditor` (`/fde-skill-audit`), `fde-skill-manager` (`/fde-skill-manage`), `fde-subagent-creator` (`/fde-subagent-create`), `fde-intelligent-sync` (`/fde-sync`).
- Note: Non-OpenSpec SDD skills (`fde-scope-creator`, `fde-spec-creator`, `fde-impl-spec`, `fde-init-setup`, `fde-code-reviewer`, `fde-code-tester`) and `autonomous-improver` are excluded in favor of the workspace's standardized OpenSpec (`openspec-*`) workflow.
