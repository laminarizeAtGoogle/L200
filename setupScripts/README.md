# Workspace Provisioning & Security Scripts (`setupScripts/`)

This directory contains portable, standalone operational scripts for provisioning Argolis GCP environments with strong security boundaries and Workload Identity Federation (WIF) for any project and GitHub repository.

---

## Zero-Privilege Security Boundary (`provision-argolis-env.sh`)

### Overview & Threat Model

When developing with agentic coding assistants on Cloudtop or local workstations, running commands directly against cloud infrastructure introduces risk if the agent has write or administrative permissions.

To establish a **hard security boundary** where the agent is physically incapable of escalating permissions or executing unauthorized write/admin operations, we enforce boundaries at the Google Cloud IAM layer.

### Pattern: The "Zero-Privilege Base Identity"

The underlying developer user identity (`<USER>@gcp.altostrat.com`) is stripped of all project-creation, owner, and editor roles at the organization level. It holds only one specific capability: assuming a dedicated read-only Service Account (`cloudtop-agent-reader`).

```
┌────────────────────────────────────────────────────────┐
│  <USER>@gcp.altostrat.com                              │
│  (Zero direct GCP access, cannot create/write/modify)  │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ can ONLY assume
                            ▼
┌────────────────────────────────────────────────────────┐
│  cloudtop-agent-reader (Service Account)               │
│  (Strictly Read-Only across Argolis Organization:      │
│   roles/viewer, roles/browser,                         │
│   roles/iam.securityReviewer, roles/cloudasset.viewer) │
└────────────────────────────────────────────────────────┘
```

### Why the Agent Cannot Escalate

1. **If the agent unsets service account impersonation:**
   The active identity falls back to `<USER>@gcp.altostrat.com`. Because that base identity has no viewer, editor, or owner roles anywhere, all GCP API calls fail with `403 Permission Denied`.
2. **If the agent tries to impersonate a privileged Service Account:**
   `<USER>@gcp.altostrat.com` holds `roles/iam.serviceAccountTokenCreator` *only* on the specific resource `cloudtop-agent-reader`. Attempts to assume any other service account are rejected by GCP IAM.
3. **If the agent tries to create or modify resources:**
   Neither `<USER>@gcp.altostrat.com` nor `cloudtop-agent-reader` holds write or management roles (`resourcemanager.projects.create`, `compute.admin`, etc.).

---

## Provisioning Guide

### Step 1: Execute Provisioning as Super Admin

Run `provision-argolis-env.sh` from an authenticated Super Admin session (e.g., `admin@<YOUR_ARGOLIS_DOMAIN>`).

> **Recommended Environment**: Run this inside **Google Cloud Shell** or a privileged admin browser console to ensure admin credentials are never downloaded to your Cloudtop filesystem.

```bash
# Copy or run the script in Cloud Shell:
./setupScripts/provision-argolis-env.sh --project <YOUR_BOOTSTRAP_OR_MANAGEMENT_PROJECT_ID> --user <USER>@gcp.altostrat.com
```

If `--project` or `--user` are omitted in an interactive terminal, the script prompts you to confirm or override the detected defaults.

#### CLI Options:
| Flag | Description | Default |
|---|---|---|
| `-p`, `--project` | Target GCP project hosting the service account | Interactive prompt / active `gcloud` project |
| `-u`, `--user` | Base user identity to restrict | Interactive prompt / `$(whoami)@gcp.altostrat.com` |
| `-s`, `--sa-name` | Name of the read-only service account | `cloudtop-agent-reader` |
| `-o`, `--org-id` | Argolis Organization ID | Auto-discovered from active credentials |
| `-h`, `--help` | Show usage help | |

---

### Step 2: Configure Cloudtop Workstation

Once the IAM boundary is provisioned, configure your local Cloudtop terminal session to impersonate the reader service account:

```bash
# Set gcloud CLI to automatically impersonate the reader SA
gcloud config set auth/impersonate_service_account cloudtop-agent-reader@<PROJECT_ID>.iam.gserviceaccount.com

# Verify that read-only access is operational
gcloud compute instances list
gcloud asset search-all-resources --scope="organizations/<ORG_ID>"
```

---

## Privileged Terraform Applies: GitHub Actions CI/CD or Cloud Shell

Because your local Cloudtop session is strictly bound to read-only access, all infrastructure modifications and `terraform apply` operations should **never** be run directly with local admin credentials on Cloudtop.

Instead, use either **Automated CI/CD via GitHub Actions (Recommended)** or **Isolated Cloud Shell**.

---

## Argolis GitHub Actions CI/CD (`setup-argolis-github-wif.sh`)

### Overview & Security Pattern

To automatically apply Terraform changes when merging pull requests to `main` from any repository of your choice:
1. **Keyless Authentication (OIDC)**: GitHub Actions authenticates via **Workload Identity Federation (WIF)**. No static service account keys (`.json`) are generated, stored in GitHub, or stored on Cloudtop.
2. **Scoping**: Only your specified repository (`OWNER/REPO`) is granted permission to impersonate the deployment Service Account (`github-terraform-deployer`).
3. **Portable & Idempotent Across New Projects/Repos**:
   - Prompts interactively for `PROJECT_ID` and `OWNER/REPO` when not explicitly passed on the CLI, preventing stale `.env` variables or cloned template `origin` remotes from silently targeting an old project/repository.
   - Can automatically create a missing GitHub repository and link `git remote origin` via the `gh` CLI.
   - If the OIDC Provider (`github-provider`) already exists in the target GCP project with a different repository condition, the script updates the OIDC provider's `--attribute-condition` (either replacing it with the new repository and cleaning up stale SA bindings, or appending the new repository).
4. **Remote State**: State is persisted in a protected Google Cloud Storage (GCS) bucket with object versioning enabled.

```
┌────────────────────────────────────────────────────────┐
│  GitHub Actions Runner (Ephemeral)                     │
│  Merge to `main` -> Requests OIDC token from GitHub    │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ Exchanges OIDC token via WIF
                            ▼
┌────────────────────────────────────────────────────────┐
│  Google Cloud STS / Workload Identity Pool             │
│  Validates repository identity & mints short-lived     │
│  access token for github-terraform-deployer SA         │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ Impersonates SA
                            ▼
┌────────────────────────────────────────────────────────┐
│  Argolis GCP Project                                   │
│  Executes 'terraform apply' against resources          │
│  Persists state to gs://<PROJECT_ID>-tfstate           │
└────────────────────────────────────────────────────────┘
```

### Provisioning Argolis for GitHub Actions

Run `setup-argolis-github-wif.sh` from Cloud Shell or an authenticated session with admin privileges in your Argolis project:

```bash
./setupScripts/setup-argolis-github-wif.sh --project <YOUR_ARGOLIS_PROJECT_ID> --repo <OWNER/REPO>
```

Or run interactively without flags to be prompted for the target GCP project, GitHub repository (`OWNER/REPO`), and automatic GitHub variable deployment:

```bash
./setupScripts/setup-argolis-github-wif.sh
```

#### CLI Options:
| Flag | Description | Default |
|---|---|---|
| `-p`, `--project` | Target Argolis GCP project ID | Interactive prompt / active `gcloud` project |
| `-r`, `--repo` | Target GitHub repository (`OWNER/REPO` or URL) | Interactive prompt / current repo `origin` |
| `-s`, `--sa-name` | Deployment Service Account name | `github-terraform-deployer` |
| `-b`, `--bucket` | GCS state bucket name | `<PROJECT_ID>-tfstate` |
| `--pool` | Workload Identity Pool name | `github-actions-pool` |
| `--provider` | Workload Identity Provider name | `github-provider` |
| `--region` | Cloud Storage bucket region | `us-central1` |
| `--replace-repo-condition` | Replace existing OIDC provider condition with only `--repo` | Interactive prompt if provider exists |
| `--append-repo-condition` | Append `--repo` to existing OIDC provider condition | Interactive prompt if provider exists |
| `--auto-deploy-gh` | Automatically deploy variables to GitHub via `gh` CLI | Interactive prompt |
| `--skip-gh` | Skip GitHub CLI variable deployment | |
| `-h`, `--help` | Show usage help | |

### Configuring the GitHub Repository

If you select automatic deployment via `gh` CLI (or pass `--auto-deploy-gh`), the script sets all 4 variables automatically. Otherwise, copy the outputs into your repository's **Settings -> Secrets and variables -> Actions**:

| Name | Type | Value |
|---|---|---|
| `GCP_PROJECT_ID` | Variable or Secret | Your Argolis project ID |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Variable or Secret | `projects/<PROJECT_NUM>/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | Variable or Secret | `github-terraform-deployer@<PROJECT_ID>.iam.gserviceaccount.com` |
| `TF_STATE_BUCKET` | Variable or Secret | `<PROJECT_ID>-tfstate` |

The repository workflow (`.github/workflows/terraform-apply.yml`) will then automatically trigger on any merge to `main`.

---

## Alternative: Manual Execution in Cloud Shell

If you need to run one-off Terraform changes manually without CI/CD:
- Maintain your `admin@<YOUR_ARGOLIS_DOMAIN>` session strictly in Cloud Shell.
- Check out your Terraform repo or sync configurations to Cloud Shell.
- Execute `terraform apply` within Cloud Shell.
- Your local Cloudtop workstation never holds high-privilege credentials on its filesystem.
