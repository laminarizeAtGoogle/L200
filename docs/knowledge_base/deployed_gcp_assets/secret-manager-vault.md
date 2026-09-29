---
okf_version: "1.0"
entry_id: "secret-manager-vault"
entry_name: "Google Cloud Secret Manager & DLP Redaction Vault"
category: "deployed_gcp_assets"
sub_category: "iam"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Cloud Security & IAM Engineering"
dendrite_node_id: "secret_manager_vault"
discovered_by: "code_manifest"
last_verified: "2026-09-28"
---

# OKF (Deployed GCP Asset): Google Cloud Secret Manager & DLP Redaction Vault

## 1. Executive Summary & Purpose
- **Primary Function**: Stores sensitive tokens (`software-factory-github-token`, `software-factory-webhook-secret`) in Google Cloud Secret Manager and provides Cloud DLP PII scrubbing so zero credentials or PII are hardcoded or persisted in plaintext.
- **Target Audience / Consumer**: `a2a-software-factory-sa` runtime Service Account and [`SecretManagerVault`](../../../software_factory/infrastructure/secret_manager.py).
- **Key Outcome**: Eliminates static secret leakage across code, logs, and conversational memory.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `argolis_project`
- **Inbound Connections**:
  - `gha_apply`: Provisions `google_secret_manager_secret` resources via Terraform.
  - `a2a_software_factory_api` / `cloud_run_factory_service`: Reads secret versions at runtime via `SecretManagerServiceClient`.
- **Outbound Connections**:
  - Audit logs emitted to Cloud Logging (`SECRET_MANAGER_ACCESS`).
- **Trust Boundary & Security Classification**: Restricted to `roles/secretmanager.secretAccessor` for `a2a-software-factory-sa`.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Terraform declarations: [`terraform/main.tf`](../../../terraform/main.tf)
  - Python client: [`software_factory/infrastructure/secret_manager.py`](../../../software_factory/infrastructure/secret_manager.py)
  - PII scrubber: [`software_factory/observability/pii_redaction.py`](../../../software_factory/observability/pii_redaction.py)
- **Protocols & Interfaces**: HTTPS / gRPC (`secretmanager.googleapis.com`, `dlp.googleapis.com`).
- **Configuration & Environment Variables**:
  - `GCP_PROJECT_ID`: Hosting project for secret versions (`projects/<PROJECT_ID>/secrets/<SECRET_ID>/versions/latest`).
- **IAM Roles & Permissions**: `roles/secretmanager.secretAccessor`, `roles/dlp.user`.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Managed declaratively via [`terraform/main.tf`](../../../terraform/main.tf) and applied on PR merge to `main`.
- **Verification & Health Checks**:
  ```bash
  ./bin/argolis gcloud secrets list --project l200-509515 --impersonate-service-account=cloudtop-agent-reader@l200-509515.iam.gserviceaccount.com
  ```
- **Failure Modes & Blast Radius**:
  - If Secret Manager is unreachable in offline tests, `SecretManagerVault` logs a structured warning (`SECRET_MANAGER_FALLBACK`) and checks ephemeral environment variables without exposing secret contents.
- **Recovery & Troubleshooting**:
  - Verify `secretmanager.googleapis.com` is enabled via `google_project_service.factory_apis` in `terraform/main.tf`.

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `secret_manager_vault` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Cloud Run Factory Service: [`deployed_gcp_assets/cloud-run-factory-service.md`](cloud-run-factory-service.md)
  - Terraform Modules: [`codebase/terraform-infrastructure-modules.md`](../codebase/terraform-infrastructure-modules.md)
