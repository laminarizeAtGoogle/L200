---
okf_version: "1.0"
entry_id: "provision-argolis-env"
entry_name: "Argolis Zero-Privilege IAM Provisioning Script"
category: "cloudtop_env"
sub_category: "scripts"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Cloud Security & Infrastructure / Academy L200"
dendrite_node_id: "reader_sa"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Cloudtop Env): Argolis Zero-Privilege IAM Provisioning Script

## 1. Executive Summary & Purpose
- **Primary Function**: Provisions a hardened zero-privilege IAM security boundary in Argolis GCP environments by creating the `cloudtop-agent-reader` Service Account with organization-level read-only roles and permitting the developer identity to assume/impersonate it without granting direct broad permissions.
- **Target Audience / Consumer**: Argolis Super Administrators, Security Engineers, and Cloudtop developers setting up new sandboxes.
- **Key Outcome**: Enforces least-privilege architecture preventing local AI agents and workstations from executing unauthorized write/mutate operations on cloud infrastructure while allowing complete inspection visibility for auditing, planning, and drift detection.

## 2. Cloudtop Environment Context
- **Sub-Category**: `scripts`
- **File / Directory Path**: [`scripts/provision-argolis-env.sh`](../../../../scripts/provision-argolis-env.sh)
- **Invocation Command / Syntax**:
  ```bash
  # Execute with explicit target project
  ./scripts/provision-argolis-env.sh --project <PROJECT_ID>

  # Custom developer user and service account name
  ./scripts/provision-argolis-env.sh \
    --project <PROJECT_ID> \
    --user <USER_EMAIL> \
    --sa-name cloudtop-agent-reader
  ```
- **Runtime Environment & Dependencies**: Bash 5.2, POSIX shell utilities, Google Cloud SDK (`gcloud`), requires Super Admin privilege at execution time.
- **Isolation Scope**: Administrative bootstrap script run once per project or during environment initialization from Google Cloud Shell or an admin terminal session.

## 3. Technical Specifications & Configuration
- **Command-Line Arguments & Flags**:
  | Flag | Option | Default | Required | Description |
  |---|---|---|---|---|
  | `-p` | `--project` | `$PROJECT_ID` or active gcloud | Yes | Target GCP project hosting the service account |
  | `-u` | `--user` | `joshholtz@gcp.altostrat.com` | No | Developer user email to restrict to read-only impersonation |
  | `-s` | `--sa-name` | `cloudtop-agent-reader` | No | Name of the read-only service account |
  | `-o` | `--org-id` | Auto-discovered | No | Argolis Organization ID for org-level role grants |
  | `-h` | `--help` | N/A | No | Print usage instructions |
- **Security & IAM Boundary Configuration**:
  - **Required Execution APIs**:
    - `iamcredentials.googleapis.com` (IAM Service Account Credentials API)
    - `cloudasset.googleapis.com` (Cloud Asset API)
  - **Organization-Level Read-Only Roles Granted to Service Account**:
    - `roles/viewer` (Read-only access to all GCP resources)
    - `roles/browser` (Hierarchy browsing)
    - `roles/iam.securityReviewer` (Security & IAM policy inspection)
    - `roles/cloudasset.viewer` (Comprehensive inventory query access)
  - **Workstation Impersonation Binding**:
    - Grants `roles/iam.serviceAccountTokenCreator` on the Service Account resource specifically to `user:<USER_IDENTITY>`.

## 4. Operational Runbook & Lifecycle
- **Step 1: Usage / Execution (from Google Cloud Shell or Admin session)**:
  ```bash
  gcloud auth login admin@joshholtz.altostrat.com
  ./scripts/provision-argolis-env.sh --project argolis-dev-sandbox-1234
  ```
- **Step 2: Verification & Impersonation Validation**:
  ```bash
  # Verify Service Account exists
  gcloud iam service-accounts describe \
    cloudtop-agent-reader@argolis-dev-sandbox-1234.iam.gserviceaccount.com \
    --project argolis-dev-sandbox-1234

  # Test read-only impersonation from Cloudtop workstation
  gcloud compute instances list \
    --project argolis-dev-sandbox-1234 \
    --impersonate-service-account=cloudtop-agent-reader@argolis-dev-sandbox-1234.iam.gserviceaccount.com
  ```
- **Step 3: Troubleshooting & Failure Modes**:
  - *Symptom*: `Unable to auto-discover Organization ID`.
    - *Remediation*: Pass `--org-id <NUMERIC_ID>` manually, verifying that the executing identity has `resourcemanager.organizations.get`.
  - *Symptom*: `PermissionDenied: Unable to create service account`.
    - *Remediation*: Confirm admin privileges: caller requires `roles/resourcemanager.organizationAdmin` or `roles/iam.serviceAccountAdmin` on the target project.

## 5. References & Cross-Links
- **Dendrite Diagram Node**: `reader_sa` in [`docs/architecture_diagram.dendrite.yaml`](../../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../../architecture.md)
- **Related OKF Entries**:
  - Reader Service Account: [`deployed_gcp_assets/reader-sa.md`](../../deployed_gcp_assets/reader-sa.md)
  - Workstation Shell: [`cloudtop_env/workstation/cloudtop-shell.md`](../workstation/cloudtop-shell.md)
  - WIF Pairing Script: [`cloudtop_env/scripts/setup-argolis-github-wif.md`](setup-argolis-github-wif.md)
