---
okf_version: "1.0"
entry_id: "setup-argolis-github-wif"
entry_name: "Argolis Workload Identity Federation & Terraform State Setup Script"
category: "cloudtop_env"
sub_category: "scripts"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Cloud Security & CI/CD / Academy L200"
dendrite_node_id: "wif_pool"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Cloudtop Env): Argolis WIF & Terraform Remote State Setup Script

## 1. Executive Summary & Purpose
- **Primary Function**: Provisions keyless Workload Identity Federation (WIF) and remote encrypted Terraform state infrastructure in Google Cloud, securely bridging GitHub Actions CI/CD to an Argolis GCP project via OpenID Connect (OIDC) without long-lived static service account keys.
- **Target Audience / Consumer**: Cloud Administrators, DevOps Engineers, and automated project setup pipelines.
- **Key Outcome**: Generates a zero-static-key authentication pipeline where GitHub Actions workflows (`terraform-plan.yml`, `terraform-apply.yml`) exchange ephemeral OIDC JWTs for temporary GCP credentials, accessing state storage and provisioning cloud resources.

## 2. Cloudtop Environment Context
- **Sub-Category**: `scripts`
- **File / Directory Path**: [`scripts/setup-argolis-github-wif.sh`](../../../../scripts/setup-argolis-github-wif.sh)
- **Invocation Command / Syntax**:
  ```bash
  # Standard automated setup with repo auto-detection
  ./scripts/setup-argolis-github-wif.sh --project <PROJECT_ID>

  # Fully parameterized setup with automatic GitHub CLI variable deployment
  ./scripts/setup-argolis-github-wif.sh \
    --project <PROJECT_ID> \
    --repo <OWNER/REPO> \
    --auto-deploy-gh
  ```
- **Runtime Environment & Dependencies**: Bash 5.2, POSIX shell utilities, Google Cloud SDK (`gcloud`), and GitHub CLI (`gh`) for automated variable deployment.
- **Isolation Scope**: Run once per project from Google Cloud Shell or workstation admin terminal; binds external GitHub repository identity to GCP IAM perimeter.

## 3. Technical Specifications & Configuration
- **Command-Line Arguments & Flags**:
  | Flag | Option | Default | Required | Description |
  |---|---|---|---|---|
  | `-p` | `--project` | Active gcloud project | Yes | Target Argolis GCP project ID |
  | `-r` | `--repo` | Auto-detected from `git remote` | Yes | GitHub repository path (`owner/repo`) |
  | `-s` | `--sa-name` | `github-terraform-deployer` | No | Deployment Service Account identifier |
  | `-b` | `--bucket` | `<PROJECT_ID>-tfstate` | No | Cloud Storage bucket name for remote Terraform state |
  | | `--pool` | `github-actions-pool` | No | Workload Identity Pool name |
  | | `--provider` | `github-provider` | No | Workload Identity Provider name |
  | | `--region` | `us-central1` | No | Default GCP region for state bucket |
  | | `--auto-deploy-gh` | Interactive prompt | No | Automatically set GitHub Action repository variables |
  | | `--skip-gh` | N/A | No | Skip GitHub Actions variable deployment |
  | `-h` | `--help` | N/A | No | Print usage instructions |
- **Security & IAM Resources Provisioned**:
  - **Workload Identity Pool & Provider**:
    - Pool: `projects/<PROJECT_NUM>/locations/global/workloadIdentityPools/github-actions-pool`
    - Provider: `github-provider` with issuer `https://token.actions.githubusercontent.com`
    - Attribute mappings:
      - `google.subject = assertion.sub`
      - `attribute.repository = assertion.repository`
      - `attribute.actor = assertion.actor`
      - `attribute.ref = assertion.ref`
    - Mandatory attribute condition: `attribute.repository == '<REPO>'`
  - **Deployer Service Account (`github-terraform-deployer`)**:
    - Workload identity user binding: `principalSet://iam.googleapis.com/<POOL>/attribute.repository/<REPO>`
    - Scoped roles: `roles/compute.admin`, `roles/storage.admin`, `roles/iam.serviceAccountUser`
  - **GCS Remote State Bucket**:
    - Uniform bucket-level access enabled (`--uniform-bucket-level-access`)
    - Object versioning enabled (`gcloud storage buckets update ... --versioning`)
    - Google-managed server-side encryption

## 4. Operational Runbook & Lifecycle
- **Step 1: Usage / Execution**:
  ```bash
  ./scripts/setup-argolis-github-wif.sh \
    --project argolis-dev-sandbox-1234 \
    --repo laminarizeAtGoogle/L200 \
    --auto-deploy-gh
  ```
- **Step 2: Verification & Health Check**:
  ```bash
  # Check Workload Identity Pool
  gcloud iam workload-identity-pools describe github-actions-pool \
    --location=global \
    --project=argolis-dev-sandbox-1234

  # Check State Bucket
  gcloud storage buckets describe gs://argolis-dev-sandbox-1234-tfstate

  # Check GitHub Action variables
  ./bin/gh variable list -R laminarizeAtGoogle/L200
  ```
- **Step 3: Troubleshooting & Failure Modes**:
  - *Symptom*: `GitHub Actions fails with 'Failed to exchange token: 403 Forbidden'`.
    - *Remediation*: Verify that `attribute.repository` condition matches the casing and path of the GitHub repository exactly. Check `WIF_PROVIDER` repository variable in GitHub.

## 5. References & Cross-Links
- **Dendrite Diagram Nodes**: `wif_pool`, `deployer_sa`, `gcs_tfstate` in [`docs/architecture_diagram.dendrite.yaml`](../../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../../architecture.md)
- **Related OKF Entries**:
  - WIF Pool: [`deployed_gcp_assets/wif-pool.md`](../../deployed_gcp_assets/wif-pool.md)
  - Deployer SA: [`deployed_gcp_assets/deployer-sa.md`](../../deployed_gcp_assets/deployer-sa.md)
  - State Bucket: [`deployed_gcp_assets/gcs-tfstate.md`](../../deployed_gcp_assets/gcs-tfstate.md)
  - CI/CD Pipelines: [`codebase/gha-plan.md`](../../codebase/gha-plan.md), [`codebase/gha-apply.md`](../../codebase/gha-apply.md)
