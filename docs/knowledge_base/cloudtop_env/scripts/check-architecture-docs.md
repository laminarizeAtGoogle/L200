---
okf_version: "1.0"
component_id: "check-architecture-docs"
name: "Architecture Documentation Pre-Push Gate"
category: "cloudtop_env"
subcategory: "scripts"
status: "active"
owner: "cloudtop-admin"
last_updated: "2026-09-28"
tags:
  - "git-hook"
  - "dendrite"
  - "pre-tool-use"
  - "okf"
---

# Architecture Documentation Pre-Push Gate (`check-architecture-docs.sh`)

## 1. Overview & Purpose
This script enforces that all outgoing commits pushed to GitHub contain up-to-date **Google Dendrite** architecture diagrams and synchronized **Google OKF** Knowledge Base entries. It acts as an automated gatekeeper invoked prior to `git push`.

## 2. Technical Specification
- **Script Location**: `.agents/scripts/check-architecture-docs.sh` & `.agents/scripts/check_architecture_docs.py`
- **Execution Hook**: `PreToolUse` on `run_command` in `.agents/hooks.json`
- **Configuration**: `.agents/scripts/check-architecture-docs-config.json`
- **Subagent Command**: `/update-architecture-docs`

## 3. Operational Workflow
1. Intercepts `git push` tool calls.
2. Identifies changed project files in `@{u}..HEAD`.
3. If project code changed without architecture documentation updates, invokes `/update-architecture-docs` subagent via `agy` CLI.
4. Audits compliance: verifies Dendrite format (`dendrite_diagram:`), strictly rejects ASCII box drawings, and verifies that docs are committed.

## 4. Verification & Testing
- Unit test suite: `.agents/scripts/test_check_architecture_docs.py` (16 passing tests).
