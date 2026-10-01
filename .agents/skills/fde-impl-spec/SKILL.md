---
name: fde-impl-spec
description: Generates a technical execution and implementation plan aligned with SCOPE.md and SPEC.md.
---

# Technical Execution Plan Skill (`fde-impl-spec`)

This skill generates a detailed technical execution plan aligned with the project's specifications.

## Process

1. **Spec Retrieval**: Find and read `SPEC.md` and `SCOPE.md` in workspace root.
   - If missing, inform the user to run `fde-spec-creator` / `/build-spec` first.
2. **Framework Alignment**: Verify technical approach against ADK standards and `AGENTS.md`.
3. **Generate Technical Execution Plan**:
   - **Understand & Deconstruct**: Restate core problem and success criteria.
   - **Proposed Approach**: Strategy and tech stack justification.
   - **Detailed Steps**: File-by-file changes, code snippets, dependencies, security considerations.
   - **Verification Plan**: Automated tests, manual steps, observability.
   - **Deployment & Rollback Strategy**: Step-by-step rollout and rollback procedure.
   - **AGENTS.md Compliance**: Explicit adherence check.
