# Workspace Provisioning & Security Scripts

This directory contains standalone operational scripts for managing and provisioning Argolis GCP environments with strong security boundaries.

---

## Zero-Privilege Security Boundary (`provision-argolis-env.sh`)

### Overview & Threat Model

When developing with agentic coding assistants on Cloudtop or local workstations, running commands directly against cloud infrastructure introduces risk if the agent has write or administrative permissions.

To establish a **hard security boundary** where the agent is physically incapable of escalating permissions or executing unauthorized write/admin operations, we enforce boundaries at the Google Cloud IAM layer.

### Pattern: The "Zero-Privilege Base Identity"

The underlying developer user identity (`joshholtz@gcp.altostrat.com`) is stripped of all project-creation, owner, and editor roles at the organization level. It holds only one specific capability: assuming a dedicated read-only Service Account (`cloudtop-agent-reader`).

```
┌────────────────────────────────────────────────────────┐
│  joshholtz@gcp.altostrat.com                           │
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
   The active identity falls back to `joshholtz@gcp.altostrat.com`. Because that base identity has no viewer, editor, or owner roles anywhere, all GCP API calls fail with `403 Permission Denied`.
2. **If the agent tries to impersonate a privileged Service Account:**
   `joshholtz@gcp.altostrat.com` holds `roles/iam.serviceAccountTokenCreator` *only* on the specific resource `cloudtop-agent-reader`. Attempts to assume any other service account are rejected by GCP IAM.
3. **If the agent tries to create or modify resources:**
   Neither `joshholtz@gcp.altostrat.com` nor `cloudtop-agent-reader` holds write or management roles (`resourcemanager.projects.create`, `compute.admin`, etc.).

---

## Provisioning Guide

### Step 1: Execute Provisioning as Super Admin

Run `provision-argolis-env.sh` from an authenticated Super Admin session (e.g., `admin@joshholtz.altostrat.com`).

> **Recommended Environment**: Run this inside **Google Cloud Shell** or a privileged admin browser console to ensure admin credentials are never downloaded to your Cloudtop filesystem.

```bash
# Clone or copy the script to Cloud Shell, or run directly:
./scripts/provision-argolis-env.sh --project <YOUR_BOOTSTRAP_OR_MANAGEMENT_PROJECT_ID>
```

#### CLI Options:
| Flag | Description | Default |
|---|---|---|
| `-p`, `--project` | Target GCP project hosting the service account | `$PROJECT_ID` or `$ARGOLIS_PROJECT_ID` |
| `-u`, `--user` | Base user identity to restrict | `joshholtz@gcp.altostrat.com` |
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

## Where to Run Privileged Terraform Applies

Because your local Cloudtop session is strictly bound to read-only access, all infrastructure modifications and `terraform apply` operations should be executed via **Isolated Cloud Shell**:

- Maintain your `admin@joshholtz.altostrat.com` session strictly in Cloud Shell.
- Check out your Terraform repo or sync configurations to Cloud Shell.
- Execute `terraform apply` within Cloud Shell.
- Your local Cloudtop workstation never holds high-privilege credentials on its filesystem, ensuring that the local agent has zero access to admin tokens.

