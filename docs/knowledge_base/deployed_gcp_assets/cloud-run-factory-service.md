---
okf_version: "1.0"
entry_id: "cloud-run-factory-service"
entry_name: "A2A Software Factory Cloud Run Service & Memory Bucket"
category: "deployed_gcp_assets"
sub_category: "compute"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Cloud Infrastructure & Agent Engineering"
dendrite_node_id: "cloud_run_factory_service"
discovered_by: "code_manifest"
last_verified: "2026-09-28"
---

# OKF (Deployed GCP Asset): A2A Software Factory Cloud Run Service & Memory Bucket

## 1. Executive Summary & Purpose
- **Primary Function**: Hosts the containerized Unified FastAPI + A2A Software Factory service (`google_cloud_run_v2_service.a2a_software_factory`) and its dedicated GCS memory/artifact bucket (`google_storage_bucket.factory_memory_artifacts`) in Argolis.
- **Target Audience / Consumer**: Enterprise developers and remote A2A agents invoking the Software Factory API.
- **Key Outcome**: Provides serverless, auto-scaling execution for the Focal Conversational Coordinator and specialist A2A sub-agents under a least-privilege Service Account (`a2a-software-factory-sa`).

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `argolis_project`
- **Inbound Connections**:
  - `gha_apply`: Provisioned and updated via `terraform apply` on merge to `main`.
- **Outbound Connections**:
  - `secret_manager_vault`: Accesses secret versions at runtime.
  - Vertex AI Gemini 2.5 Pro & Flash endpoints (`aiplatform.googleapis.com`).
- **Trust Boundary & Security Classification**: Internal load-balancer ingress (`INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER`) running as `a2a-software-factory-sa`.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Terraform definitions: [`terraform/main.tf`](../../../terraform/main.tf), [`terraform/variables.tf`](../../../terraform/variables.tf), [`terraform/outputs.tf`](../../../terraform/outputs.tf)
- **Protocols & Interfaces**: HTTPS / HTTP/2 (`8080`), JSON-RPC 2.0 (`/a2a/*`), REST (`/api/v1/*`).
- **Configuration & Environment Variables**:
  - `factory_service_name`: `a2a-software-factory`
  - `planning_model`: `gemini-2.5-pro`
  - `fast_model`: `gemini-2.5-flash`
- **IAM Roles & Permissions**: `roles/aiplatform.user`, `roles/secretmanager.secretAccessor`, `roles/logging.logWriter`, `roles/cloudtrace.agent`, `roles/dlp.user`, `roles/viewer`.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Open a Pull Request modifying `terraform/main.tf` from a feature branch to `main` to trigger `terraform-plan.yml` and `terraform-apply.yml`.
- **Verification & Health Checks**:
  ```bash
  ./bin/argolis gcloud run services list --project l200-509515 --impersonate-service-account=cloudtop-agent-reader@l200-509515.iam.gserviceaccount.com
  ```
- **Failure Modes & Blast Radius**:
  - Isolated to the Cloud Run revision; state is persisted in GCS (`<PROJECT_ID>-a2a-factory-memory`).
- **Recovery & Troubleshooting**:
  - Query Cloud Run revision logs via `query_cloud_logging_entries_readonly`.

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `cloud_run_factory_service` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Secret Manager Vault: [`deployed_gcp_assets/secret-manager-vault.md`](secret-manager-vault.md)
  - Focal API Codebase: [`codebase/a2a-software-factory-api.md`](../codebase/a2a-software-factory-api.md)
