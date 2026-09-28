---
name: update-architecture-docs
description: >-
  Instructs a subagent to update the Google OKF Knowledge Base and Dendrite architecture
  diagram with all changes comprised in outgoing git commits prior to pushing.
---

# update-architecture-docs Subagent

This subagent is executed automatically by the pre-tool-use hook on `git push` or manually via the `/update-architecture-docs` slash command.
Its mission is to ensure that `./docs/` is always completely synchronized with outgoing code and infrastructure updates, utilizing the **Google Dendrite format** (`go/dendrite`) for diagrams and **Google OKF** (Operational Knowledge Framework) for the Knowledge Base.

---

## Subagent Procedure

When invoked, execute the following steps in sequence:

### Step 1: Inspect Outgoing Changes & Diffs

1. Determine the outgoing commit range:
   ```bash
   git rev-parse --abbrev-ref @{u} 2>/dev/null && RANGE="@{u}..HEAD" || RANGE="origin/main..HEAD"
   git log $RANGE --oneline
   git diff --name-only $RANGE
   ```
2. Inspect the detailed code/infrastructure diff:
   ```bash
   git diff $RANGE
   ```
3. Classify all modified files across the 3 OKF categories:
   - **Cloudtop Environment** (`docs/knowledge_base/cloudtop_env/`):
     - Scripts in `.agents/scripts/`, `scripts/`, or root.
     - Skills in `.agents/skills/`, `.gemini/skills/`.
     - Slash commands in `.gemini/commands/`.
     - Toolchains & package managers (`bin/`, `uv`, `terraform`, `gcloud`, `gh`).
   - **Deployed GCP Assets** (`docs/knowledge_base/deployed_gcp_assets/`):
     - Terraform infrastructure definitions (`terraform/*.tf`).
     - GCP resources: WIF pools, service accounts, IAM roles, GCS buckets, VPCs, firewall rules, compute instances.
   - **Codebase** (`docs/knowledge_base/codebase/`):
     - Application modules, Python ADK agent implementations.
     - CI/CD workflows (`.github/workflows/*.yml`).
     - Architectural subsystems and interfaces.

---

### Step 2: Update the Canonical Dendrite Architecture Diagram

1. **Strict Dendrite Standard**:
   - The architecture diagram **MUST** utilize the official **Google Dendrite format** (`dendrite_diagram:` declarative YAML/DSL specification pointing to `http://go/dendrite` and interactive playground at `http://go/dendrite-playground`).
   - **NEVER** use ASCII text box art (`+---+` / `|   |`) or generic markdown diagrams.
2. **Update Diagram Model**:
   - Inspect [`docs/architecture_diagram.dendrite.yaml`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/architecture_diagram.dendrite.yaml).
   - If new components or systems were introduced, add them under the corresponding boundary (`developer_workstation`, `github_platform`, `gcp_iam_boundary`, or `argolis_project`).
   - If new inter-component flows or security controls were added, register the directional `connections` (with `protocol`, `auth`, `label`, and `type`).
   - Ensure `playground_url: "http://go/dendrite-playground"` is present.
   - Update `last_updated: "<YYYY-MM-DD>"`.
3. **Synchronize `docs/architecture.md`**:
   - Update the embedded ````yaml` code block in [`docs/architecture.md`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/architecture.md) to reflect the refreshed Dendrite model.
   - Update the `Last Synchronized` date and ensure it clearly points to `[http://go/dendrite](http://go/dendrite)` as authoritative and provides the interactive viewer link `[http://go/dendrite-playground](http://go/dendrite-playground)`.

---

### Step 3: Update the Google OKF Knowledge Base

1. **Follow OKF Specifications**:
   - Follow the standards defined in [`docs/knowledge_base/OKF_SPEC.md`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/knowledge_base/OKF_SPEC.md) and [`docs/knowledge_base/TEMPLATE.md`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/knowledge_base/TEMPLATE.md).
2. **Create or Update Subcategory Entries**:
   - For **Cloudtop Environment**: use [`templates/cloudtop_env_template.md`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/knowledge_base/templates/cloudtop_env_template.md) in `docs/knowledge_base/cloudtop_env/{scripts,skills,slash_commands,package_managers}/`.
   - For **Deployed GCP Assets**: use [`templates/deployed_gcp_asset_template.md`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/knowledge_base/templates/deployed_gcp_asset_template.md) in `docs/knowledge_base/deployed_gcp_assets/`.
   - For **Codebase**: use [`templates/codebase_template.md`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/knowledge_base/templates/codebase_template.md) in `docs/knowledge_base/codebase/`.
3. **Component Reference Entries**:
   - Every architectural component in the Dendrite diagram must have a matching OKF reference file in `docs/knowledge_base/components/<component-id>.md`.
4. **Update Catalog Index**:
   - Ensure [`docs/knowledge_base/README.md`](file:///usr/local/google/home/joshholtz/Documents/L200/docs/knowledge_base/README.md) lists the new or modified components in the catalog table.

---

### Step 4: Stage & Commit Architecture Documentation

1. Stage all documentation updates:
   ```bash
   git add docs/
   ```
2. Commit the changes:
   ```bash
   git commit -m "docs: update architecture diagram (Dendrite) and OKF knowledge base"
   ```

---

### Step 5: Verification & Status Output

1. Verify that `docs/architecture.md` and `docs/architecture_diagram.dendrite.yaml` are clean, well-formed, and free of ASCII box drawings.
2. Verify that all OKF files pass basic structure checks.
3. Emit final status line:
   - On success:
     ```text
     ARCHITECTURE_DOCS_UPDATE: SUCCESS: Updated <list-of-updated-components> in Dendrite diagram and OKF Knowledge Base.
     ```
   - On failure:
     ```text
     ARCHITECTURE_DOCS_UPDATE: FAILED: <reason-for-failure>
     ```
