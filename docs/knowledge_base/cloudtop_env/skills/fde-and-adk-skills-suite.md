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

# FDE & Official ADK-Python Agent Skills Catalog (`.agents/skills/`)

## 1. Overview & Purpose
Provides a comprehensive suite of workspace-scoped AI engineering skills combining:
1. **Official Google ADK-Python Skills** from [`google/adk-python`](https://github.com/google/adk-python/tree/main) (`.agents/skills/adk-*`) for building, debugging, styling, reviewing, and testing ADK 2.0 agents and graph workflows.
2. **Consolidated Cloud AI FDE Skills** harvested from the latest feature branches and commits of [`cloud-ai-fde/agent-driven-dev`](https://github.com/cloud-ai-fde/agent-driven-dev) (`.agents/skills/fde-*` and `.agents/agents/autonomous-improver.md`).

## 2. Installed Skills Breakdown

### A. Official ADK-Python Skills (`google/adk-python`)
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

### B. Cloud AI FDE Skills (`cloud-ai-fde/agent-driven-dev`)
- `fde-a2ui-skills` (from `feat/a2ui-skills` `ce655cd`): Gemini Enterprise A2UI v0.9 component builder and validator.
- `fde-cross-compliance` (from `feat/fde-cross-compliance` `4526bd5`, PR #23): OSPO & client delivery sanitization toolkit (`sanitize_repo.sh`).
- `fde-cloud-run-builder` (from `4526bd5`): Cloud Run deployment via Buildpacks.
- `fde-git-push` (from `4526bd5` & `fix/yaml-parsing` `935fb78`): Pre-commit security audit, README alignment, and Conventional Commits governance.
- `fde-agentic-code-audit`, `fde-catalog-enhancement`, `fde-code-reviewer`, `fde-code-tester`, `fde-gcp-architect`, `fde-genai-sdk`, `fde-google-docs`, `fde-impl-spec`, `fde-init-setup`, `fde-intelligent-sync`, `fde-mcp-server-builder`, `fde-mermaid-chart`, `fde-model-migration-audit`, `fde-presentation-skill`, `fde-project-manager`, `fde-scope-creator`, `fde-skill-auditor`, `fde-skill-creator`, `fde-skill-manager`, `fde-spec-creator`, `fde-subagent-creator` (from `pre-fde-skills-migration` `01d3c97`).
- Subagent: `.agents/agents/autonomous-improver.md`.
