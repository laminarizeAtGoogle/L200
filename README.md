# Google Academy L200 & Argolis Workspace

Isolated development environment on Cloudtop (`/usr/local/google/home/joshholtz/Documents/L200`) configured for:
1. **Argolis GCP Instance Management**: Isolated `gcloud` configuration and `./bin/argolis` CLI helper.
2. **Terraform Development**: Standalone Terraform v1.16.4 binary and modular GCP infrastructure definitions in [`terraform/`](terraform/).
3. **GitHub Change Tracking**: Local git repository with secure ignore rules and GitHub CLI (`./bin/gh`).
4. **Google Agent Development (ADK)**: Python 3.12 virtualenv and Google ADK tooling managed with standalone `uv`.

---

## Workspace Isolation Summary

All tools, runtimes, dependencies, and credentials are strictly isolated to this workspace directory:
- **`./bin/terraform`**: Standalone Terraform binary (v1.16.4) for IaC development.
- **`./bin/argolis`**: Management wrapper for Argolis Compute Engine instances and GCP configurations.
- **`./bin/gh`**: Standalone GitHub CLI (v2.101.0) for repository and pull request management.
- **`./bin/uv`**: Standalone `uv` binary (v0.12.16) for dependency and virtualenv management.
- **`./.python/`**: Isolated Python 3.12.14 standalone toolchain.
- **`./.nodejs/`**: Isolated Node.js 22.14.0 LTS standalone toolchain.
- **`./bin/node`**, **`./bin/npm`**, **`./bin/npx`**: Standalone Node.js runtime and package manager wrappers.
- **`./bin/openspec`**: OpenSpec CLI (v1.13.1) for Spec-Driven Development (SDD).
- **`./openspec/`**: OpenSpec repository structure (`specs/`, `changes/`, `config.yaml`).
- **`./.npmrc`**: Internal Corp Airlock proxy configuration for npm package resolution.
- **Airlock Proxy**: Package resolution configured to use the internal Airlock proxy index (`http://airlock-proxy.uplink.goog:999/...`).

---

## Workspace Structure & Files

| File / Directory | Purpose |
|---|---|
| [`scripts/`](scripts/) | Operational scripts, including Argolis zero-privilege IAM boundary provisioner (`provision-argolis-env.sh`). |
| [`relocate.sh`](relocate.sh) | Portable workspace relocator to dynamically update environment paths when extracted or moved. |
| [`terraform/`](terraform/) | Terraform manifests: provider, compute instance, firewall, variables, and outputs. |
| [`terraform/terraform.tfvars.example`](terraform/terraform.tfvars.example) | Example variable configuration for Argolis projects and instances. |
| [`bin/argolis`](bin/argolis) | Helper CLI for managing Argolis instances (`status`, `list`, `ssh`, `start`, `stop`). |
| [`bin/terraform`](bin/terraform) | Standalone Linux x86_64 Terraform binary (v1.16.4). |
| [`bin/gh`](bin/gh) | Standalone Linux x86_64 GitHub CLI binary (v2.101.0). |
| [`bin/gcloud`](bin/gcloud) | Wrapper script setting `CLOUDSDK_CONFIG` and launching isolated SDK. |
| [`bin/uv`](bin/uv) | Standalone Linux x86_64 `uv` executable. |
| [`bin/openspec`](bin/openspec) | Standalone OpenSpec CLI (v1.13.1) for spec-driven development. |
| [`bin/node`](bin/node) | Isolated Node.js v22.14.0 binary symlink. |
| [`bin/npm`](bin/npm) | Isolated npm v10.9.2 package manager symlink. |
| [`.npmrc`](.npmrc) | Configures npm registry to internal Corp Airlock proxy. |
| [`openspec/`](openspec/) | OpenSpec root: specifications (`specs/`), change proposals (`changes/`), and config. |
| [`.env`](.env) | Exports isolated paths for `CLOUDSDK_CONFIG`, `GOOGLE_APPLICATION_CREDENTIALS`, `PATH`, and Terraform variables. |
| [`.gitignore`](.gitignore) | Enforces exclusion of credentials, state files, venvs, and binaries from git. |
| [`uv.toml`](uv.toml) | Configures index URL to internal Airlock proxy and allows insecure host. |
| [`pyproject.toml`](pyproject.toml) | Defines project metadata and dependencies (`google-adk[gcp]>=2.9.1`, `pandas`, `ipykernel`). |
| [`main.py`](main.py) | Verification script confirming imports and runtime configuration. |
| [`README.md`](README.md) | Workspace documentation and quickstart guide. |

---

## Quickstart & Usage Guide

### 1. Activating Workspace Environment
To add workspace binaries (`terraform`, `argolis`, `gcloud`, `uv`, `gh`) to your current terminal session:
```bash
source .env
source .venv/bin/activate
```

---

### 2. Argolis GCP Instance Management
Authenticate and manage your Argolis project and instances:
```bash
# Authenticate CLI and Application Default Credentials (ADC)
./bin/argolis auth

# Set your active Argolis project ID
./bin/argolis set-project <YOUR_ARGOLIS_PROJECT_ID>

# Check current configuration status
./bin/argolis status

# List Compute Engine instances in the project
./bin/argolis list

# SSH into an instance
./bin/argolis ssh <INSTANCE_NAME>

# Start / stop an instance
./bin/argolis start <INSTANCE_NAME>
./bin/argolis stop <INSTANCE_NAME>
```

---

### 3. Workspace Portability & Relocation
When extracting the workspace from a portable backup archive or moving it to another directory:
```bash
./relocate.sh
```
This automatically updates `.env` with the new working directory's absolute paths, relocates `.venv/pyvenv.cfg` and virtualenv shebangs, and runs `main.py` to verify full operation.

---

### 4. Argolis Zero-Privilege Security Boundary (Fresh Environments)
To enforce a hard security boundary at the IAM layer preventing local coding agents from escalating privileges or making unauthorized GCP modifications:

1. **Run Provisioner as Super Admin** (in Cloud Shell or privileged terminal):
   ```bash
   ./scripts/provision-argolis-env.sh --project <YOUR_ARGOLIS_PROJECT_ID>
   ```

2. **Configure Cloudtop to Impersonate the Read-Only Service Account**:
   ```bash
   gcloud config set auth/impersonate_service_account cloudtop-agent-reader@<YOUR_ARGOLIS_PROJECT_ID>.iam.gserviceaccount.com
   ```

For detailed architectural patterns, threat model, and privileged Terraform execution rules, see [`scripts/README.md`](scripts/README.md).

---

### 5. Terraform Development
The Terraform configuration in [`terraform/`](terraform/) deploys and manages Argolis Compute Engine instances.

1. **Configure Variables**:
   ```bash
   cp terraform/terraform.tfvars.example terraform/terraform.tfvars
   # Edit terraform/terraform.tfvars with your Argolis project ID
   ```

2. **Initialize Terraform**:
   ```bash
   ./bin/terraform -chdir=terraform init
   ```

3. **Plan and Review Changes**:
   ```bash
   ./bin/terraform -chdir=terraform plan
   ```

4. **Apply Infrastructure**:
   ```bash
   ./bin/terraform -chdir=terraform apply
   ```

5. **Format & Validate Code**:
   ```bash
   ./bin/terraform -chdir=terraform fmt
   ./bin/terraform -chdir=terraform validate
   ```

---

### 6. GitHub Tracking & Git Workflow

The workspace is initialized as a git repository with strict `.gitignore` rules that prevent credentials, local state, or heavy binaries from being committed.

1. **Configure Git Identity** (if not already set globally):
   ```bash
   git config user.name "Your Name"
   git config user.email "your.email@example.com"
   ```

2. **Connect to GitHub Remote**:
   ```bash
   # Add your GitHub repository as remote
   git remote add origin https://github.com/<USERNAME>/<REPO>.git
   # Or using SSH:
   # git remote add origin git@github.com:<USERNAME>/<REPO>.git

   # Push to main
   git push -u origin main
   ```

3. **Using GitHub CLI (`gh`)**:
   ```bash
   # Authenticate with GitHub
   ./bin/gh auth login

   # Check repository or create PRs
   ./bin/gh repo view
   ```

---

### 7. Google Agent Development Kit (ADK) & Python

```bash
# Run verification script
./bin/uv run --env-file .env python main.py

# Launch ADK Web Console
./bin/uv run --env-file .env adk web
```

---

### 8. Spec-Driven Development with OpenSpec

OpenSpec structures AI development around formal specifications, design choices, and implementation tasks.

1. **Check CLI & OpenSpec Status**:
   ```bash
   ./bin/openspec --version
   ./bin/openspec status
   ./bin/openspec view
   ```

2. **Propose a New Feature or Change**:
   In Antigravity chat, run:
   ```text
   /opsx-propose "Your feature description"
   ```
   Or via CLI:
   ```bash
   ./bin/openspec new change <change-name>
   ```

3. **OpenSpec Lifecycle**:
   - **`openspec/changes/<change-name>/proposal.md`**: Problem statement and user-facing requirements.
   - **`openspec/changes/<change-name>/specs/`**: RFC 2119 functional specifications and criteria.
   - **`openspec/changes/<change-name>/design.md`**: Architecture, data schemas, and technical approach.
   - **`openspec/changes/<change-name>/tasks.md`**: Ordered implementation checklist.
   - **Implement**: `/opsx-apply` to execute implementation tasks.
   - **Archive**: `/opsx-archive` once changes are tested and synced with root specs.
