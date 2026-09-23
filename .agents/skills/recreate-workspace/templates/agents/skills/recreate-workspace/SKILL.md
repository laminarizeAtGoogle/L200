---
name: recreate-workspace
description: >-
  Recreates an isolated, self-contained L200 Google Academy / Argolis / ADK development
  workspace in another working directory by downloading and configuring the latest toolchains
  directly from Airlock and official sources. Use this skill whenever a user or agent
  wants to bootstrap, replicate, setup, or recreate an L200 development environment in a new directory.
---

# L200 Workspace Recreation Skill & Implementation Guide

This skill serves as the **architectural blueprint and automated bootstrapper** for creating an isolated L200 Google Academy / Argolis development workspace in any target working directory.

It provisions completely independent toolchains and environments downloaded directly from corporate Airlock proxies and official upstream distributions—ensuring zero hard-links, shared inodes, or cross-workspace coupling.

---

## Architectural Blueprint (The 9 Core Pillars)

When replicating or understanding this workspace, ensure all 9 architectural pillars are in place:

### 1. Python / ADK Toolchain (`.python/`, `bin/uv`, `.venv/`)
* **Purpose**: Provides a dedicated, isolated Python 3.12 runtime and Google Agent Development Kit (`google-adk[gcp]>=2.9.1`, `pandas`, `ipykernel`).
* **Isolation Mechanism**: Standalone `uv` binary in `./bin/uv` installs Python into `./.python/` (configured via `UV_PYTHON_INSTALL_DIR`) and dependencies into `./.venv/`.
* **Airlock Integration**: Package resolution configured via `uv.toml` and `.env` pointing to the internal Airlock PyPI mirror (`http://airlock-proxy.uplink.goog:999/python/artifact-foundry-prod/ah-3p-staging-python/simple/`).

### 2. Standalone Google Cloud SDK & Argolis CLI (`google-cloud-sdk/`, `bin/gcloud`, `bin/argolis`)
* **Purpose**: Manages Argolis GCP instances and cloud resources without polluting the host's global `~/.config/gcloud`.
* **Isolation Mechanism**: Custom wrapper script in `./bin/gcloud` sets `CLOUDSDK_CONFIG` and `GOOGLE_APPLICATION_CREDENTIALS` to point exclusively to `./.gcloud/`.
* **Argolis Helper**: `./bin/argolis` wraps gcloud compute commands (`status`, `auth`, `set-project`, `list`, `ssh`, `start`, `stop`).

### 3. Terraform GCP Infrastructure (`terraform/`, `bin/terraform`)
* **Purpose**: Infrastructure as Code (IaC) defining Argolis Compute Engine instances, service accounts, and networking.
* **Isolation Mechanism**: Standalone Linux x86_64 Terraform binary (v1.16.4) in `./bin/terraform`. Local provider plugin cache in `terraform/.terraform/`.
* **Manifests**: `main.tf`, `variables.tf`, `outputs.tf`, `provider.tf`, `versions.tf`, `terraform.tfvars.example`.

### 4. GitHub Tracking & Secure Git Hygiene (`.gitignore`, `bin/gh`)
* **Purpose**: Version control and GitHub interaction with strict safeguards against credential leaks.
* **Isolation Mechanism**: Standalone GitHub CLI in `./bin/gh`. Comprehensive `.gitignore` excluding all local credentials (`.env`, `.gcloud/`), toolchains (`.python/`, `.nodejs/`, `bin/`), virtualenvs (`.venv/`), and Terraform state (`*.tfstate`).

### 5. Node.js & OpenSpec Spec-Driven Development (`.nodejs/`, `bin/openspec`, `openspec/`)
* **Purpose**: Manages formal specifications, proposals, and change tracking using OpenSpec (SDD).
* **Isolation Mechanism**: Standalone Node.js 22 LTS toolchain in `./.nodejs/` with symlinks in `./bin/node`, `./bin/npm`, `./bin/npx`. OpenSpec installed via isolated npm prefix with `.npmrc` configured to the internal Airlock npm registry (`http://airlock-proxy.uplink.goog:999/npm/artifact-foundry-prod/ah-3p-staging-npm/`).
* **Slash Commands**: Opsx command definitions in `.gemini/commands/opsx/` and workflows in `.agents/workflows/`.

### 6. Pre-Command Git Push Sanitization Gate (`.agents/hooks.json`, `.agents/scripts/`)
* **Purpose**: Intercepts `git push` executions in Antigravity to prevent accidental leakage of corporate cookies, JWTs, API keys, or private credentials.
* **Mechanism**: Antigravity lifecycle hook in `.agents/hooks.json` delegates `run_command` tool calls to `.agents/scripts/pre-command-hook.sh`. Non-git commands bypass instantly; git commands are scanned by `pre_command_hook.py` (which handles git aliases and unpushed diffs). Unit tested via `test_pre_command_hook.py`.

### 7. Environment Configuration (`.env`)
* **Purpose**: Sets workspace environment variables for terminal sessions and subshells.
* **Key Bindings**:
  ```bash
  WORKSPACE_ROOT=/path/to/workspace
  CLOUDSDK_CONFIG=$WORKSPACE_ROOT/.gcloud
  GOOGLE_APPLICATION_CREDENTIALS=$WORKSPACE_ROOT/.gcloud/application_default_credentials.json
  PATH=$WORKSPACE_ROOT/bin:$PATH
  UV_INDEX_URL=http://airlock-proxy.uplink.goog:999/python/artifact-foundry-prod/ah-3p-staging-python/simple/
  UV_INSECURE_HOST=airlock-proxy.uplink.goog
  UV_PYTHON_INSTALL_DIR=$WORKSPACE_ROOT/.python
  ```

### 8. Assessment Rubric & Documentation
* **`AI in 5 Days Assessment Agent.md`**: Official evaluation rubric covering 5 categories (Tool & Interface Design, Context & Memory, Orchestration & Logic, Observability & Tracing, Infrastructure & CI/CD) totaling 95 points.
* **`README.md`**: Complete quickstart guide for the workspace.

### 9. Environment Verification (`main.py`)
* **Purpose**: Sanity checks python runtime imports (`google.adk`, `pandas`, `ipykernel`) and validates environment variables.

---

## Agent Operational Guide: Recreating a Workspace

When requested by a user to recreate or provision an L200 workspace in another working directory, follow these steps:

### Step 1: Confirm Target Directory
Identify or ask for the destination path (e.g., `~/workspace/my-new-project` or `/usr/local/google/home/.../new-dir`).

### Step 2: Execute the Automated Bootstrapper
Run the `setup_workspace.py` script located in this skill:

```bash
python3 .agents/skills/recreate-workspace/scripts/setup_workspace.py \
  --target /path/to/new-workspace \
  [--argolis-project YOUR_ARGOLIS_PROJECT_ID]
```

**What this script automates**:
1. Scaffolds the full directory hierarchy (`bin`, `terraform`, `openspec`, `.agents`, `.gemini`, `.gcloud`).
2. Instantiates all configuration files and templates with dynamic absolute paths for the target directory.
3. Downloads latest standalone binaries (`uv`, `terraform`, `gh`, Node.js 22 LTS, `google-cloud-sdk`) from official sources.
4. Installs Python 3.12 and Google ADK dependencies using the Airlock PyPI mirror.
5. Installs OpenSpec CLI via the Airlock npm registry.
6. Initializes Terraform GCP provider plugins (`bin/terraform init`).
7. Initializes a clean git repository.
8. Automatically triggers the verification suite.

### Step 3: Run Post-Setup Verification
If verification was skipped or needs to be re-run manually:

```bash
python3 .agents/skills/recreate-workspace/scripts/verify_workspace.py --target /path/to/new-workspace
```

Confirm that all checks pass:
* `Directory Structure`: PASS
* `Toolchain Binaries in bin/`: PASS (uv, terraform, gh, gcloud, argolis, jetski, node, npm, npx, openspec)
* `Configuration Manifests`: PASS
* `Toolchain Execution`: PASS
* `Python & Google ADK`: PASS (`main.py` succeeds)
* `Git Push Sanitization Suite`: PASS (14/14 tests pass)

### Step 4: Instruct the User on Next Steps
After provisioning is complete, instruct the user to activate their new environment:

```bash
cd /path/to/new-workspace
source .env
source .venv/bin/activate

# Authenticate with Argolis credentials
./bin/argolis auth
```
