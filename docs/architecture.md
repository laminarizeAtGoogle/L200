# L200 System, Infrastructure & A2A Software Factory Architecture

This document serves as the authoritative architectural blueprint for the Google Academy L200, Argolis, and **A2A Agent Graph Software Factory** workspace.

---

## Canonical Architecture Diagram

> **Authoritative Architecture Platform**: Google Internal **Dendrite** ([go/dendrite](http://go/dendrite))  
> **Interactive Diagram Viewer**: [go/dendrite-playground](http://go/dendrite-playground)  
> **Source Model File**: [`docs/architecture_diagram.dendrite.yaml`](architecture_diagram.dendrite.yaml)  
> **Last Synchronized**: 2026-09-28

```yaml
# Dendrite Declarative Architecture Specification (go/dendrite)
dendrite_diagram:
  title: "L200 Argolis Infrastructure, CI/CD & A2A Software Factory Architecture"
  version: "2.0.0"
  dendrite_url: "http://go/dendrite"
  playground_url: "http://go/dendrite-playground"
  boundaries:
    - id: "developer_workstation"
      label: "Developer Environment (Cloudtop)"
      type: "workstation"
      trust_level: "authenticated_internal"
      components:
        - id: "cloudtop_shell"
          label: "Cloudtop Terminal / Antigravity"
          type: "dev_environment"
          role: "Local coding, testing, and git operations"
        - id: "adk_runtime"
          label: "Google ADK Agent Runtime"
          type: "ai_agent"
          role: "Python 3.12 + Google ADK + A2A SDK execution"
        - id: "a2a_software_factory_api"
          label: "Unified FastAPI + A2A Focal Coordinator Server"
          type: "api_gateway"
          role: "Single conversational focal point (/api/v1/chat) & mounted A2A endpoints"
        - id: "a2a_subagent_mesh"
          label: "A2A Specialist Sub-Agent Mesh"
          type: "subagent_cluster"
          role: "Architect, Builder, WIF/Git PR Delivery, Read-Only gcloud Probe, Sequential & Parallel workflows"
        - id: "isolated_binaries"
          label: "Standalone Binaries (./bin)"
          type: "toolchain"
          role: "Terraform v1.16.4, gcloud SDK, gh CLI, uv, openspec"

    - id: "github_platform"
      label: "GitHub Enterprise / Cloud"
      type: "vcs_cicd"
      trust_level: "managed_external"
      components:
        - id: "github_repo"
          label: "GitHub Repository (L200 / External Target)"
          type: "vcs_repository"
          role: "Git source of truth with branch protection & pre-push sanitization hooks"
        - id: "gha_plan"
          label: "GitHub Actions: terraform-plan.yml"
          type: "ci_pipeline"
          role: "Automated lint, init, validate, and plan on PRs"
        - id: "gha_apply"
          label: "GitHub Actions: terraform-apply.yml"
          type: "cd_pipeline"
          role: "Automated terraform apply on merge to main"
        - id: "agent_eval_pipeline"
          label: "GitHub Actions: agent-eval-and-test.yml"
          type: "ci_pipeline"
          role: "Automated pytest & Golden Dataset agent evaluation suite"

    - id: "gcp_iam_boundary"
      label: "Google Cloud IAM & Workload Identity"
      type: "security_perimeter"
      trust_level: "zero_privilege"
      components:
        - id: "wif_pool"
          label: "Workload Identity Pool & Provider"
          type: "iam_wif"
          role: "OIDC validation for GitHub Actions across local & external projects"
        - id: "deployer_sa"
          label: "Deployer Service Account"
          type: "service_account"
          role: "github-terraform-deployer SA (scoped Compute, Run & Storage Admin)"
        - id: "reader_sa"
          label: "Read-Only Cloudtop SA"
          type: "service_account"
          role: "cloudtop-agent-reader SA (strictly Viewer permissions only)"

    - id: "argolis_project"
      label: "Argolis GCP Project (Sandbox / External Target)"
      type: "gcp_project"
      trust_level: "cloud_resources"
      components:
        - id: "gcs_tfstate"
          label: "Cloud Storage (tfstate Bucket)"
          type: "cloud_storage"
          role: "Remote encrypted Terraform state with object locking"
        - id: "secret_manager_vault"
          label: "Secret Manager & Cloud DLP Vault"
          type: "security_vault"
          role: "Zero hardcoded secrets + active PII redaction across logs and memory"
        - id: "cloud_run_factory_service"
          label: "Cloud Run v2 Service & Memory Bucket"
          type: "serverless_compute"
          role: "Hosts containerized A2A Software Factory & persistent episodic memory store"
        - id: "vpc_network"
          label: "VPC Network & Subnet"
          type: "vpc_networking"
          role: "Isolated virtual private network (a2a-factory-vpc in us-central1)"
        - id: "firewall_rules"
          label: "Firewall Rules"
          type: "security_firewall"
          role: "Ingress controls (SSH/IAP 35.235.240.0/20)"
        - id: "compute_vm"
          label: "Compute Engine Instances"
          type: "compute_engine"
          role: "Managed VM workloads and test beds"

  connections:
    - from: "cloudtop_shell"
      to: "a2a_software_factory_api"
      protocol: "HTTP / JSON-RPC"
      auth: "Authenticated Session"
      label: "POST /api/v1/chat & /a2a/* (user intent <-> agent state)"
      type: "control"
    - from: "a2a_software_factory_api"
      to: "a2a_subagent_mesh"
      protocol: "ADK / A2A JSON-RPC"
      auth: "Internal Guardrails & HITL Gate"
      label: "Delegate to Architect, Builder, WIF/Git, and Read-Only Probe agents"
      type: "control"
    - from: "a2a_software_factory_api"
      to: "secret_manager_vault"
      protocol: "HTTPS / gRPC"
      auth: "ADC / Runtime SA"
      label: "Resolve secrets & scrub PII via Cloud DLP"
      type: "data"
    - from: "a2a_subagent_mesh"
      to: "github_repo"
      protocol: "HTTPS / Git / gh CLI"
      auth: "GitHub Token (Secret Manager)"
      label: "Create feature branch from main, commit with context, and open PR"
      type: "control"
    - from: "cloudtop_shell"
      to: "github_repo"
      protocol: "HTTPS / SSH"
      auth: "GitHub CLI / SSH Key"
      label: "git push feature branch (gated by pre-push hooks)"
      type: "control"
    - from: "github_repo"
      to: "agent_eval_pipeline"
      protocol: "GitHub Webhook"
      label: "Trigger pytest & Golden Dataset eval on PR/push"
      type: "event"
    - from: "github_repo"
      to: "gha_plan"
      protocol: "GitHub Webhook"
      label: "Trigger on PR to main"
      type: "event"
    - from: "github_repo"
      to: "gha_apply"
      protocol: "GitHub Webhook"
      label: "Trigger on Merge to main"
      type: "event"
    - from: "gha_apply"
      to: "wif_pool"
      protocol: "HTTPS"
      auth: "GitHub OIDC JWT"
      label: "Exchange OIDC token for federated credentials"
      type: "auth"
    - from: "wif_pool"
      to: "deployer_sa"
      protocol: "GCP STS API"
      auth: "Federated Token"
      label: "Assume Deployer SA (ephemeral token)"
      type: "auth"
    - from: "gha_apply"
      to: "gcs_tfstate"
      protocol: "HTTPS / GCS API"
      auth: "Deployer SA Token"
      label: "Acquire lock & sync terraform.tfstate"
      type: "data"
    - from: "gha_apply"
      to: "cloud_run_factory_service"
      protocol: "HTTPS / Cloud Run API"
      auth: "Deployer SA Token"
      label: "Provision Cloud Run v2 A2A Factory & Memory Bucket"
      type: "provisioning"
    - from: "gha_apply"
      to: "secret_manager_vault"
      protocol: "HTTPS / Secret Manager API"
      auth: "Deployer SA Token"
      label: "Provision Secret Manager secrets"
      type: "provisioning"
    - from: "gha_apply"
      to: "vpc_network"
      protocol: "HTTPS / GCP Compute API"
      auth: "Deployer SA Token"
      label: "Apply VPC & Subnet configuration"
      type: "provisioning"
    - from: "gha_apply"
      to: "firewall_rules"
      protocol: "HTTPS / GCP Compute API"
      auth: "Deployer SA Token"
      label: "Apply IAP SSH firewall rules"
      type: "provisioning"
    - from: "gha_apply"
      to: "compute_vm"
      protocol: "HTTPS / GCP Compute API"
      auth: "Deployer SA Token"
      label: "Provision & manage Compute Engine VMs"
      type: "provisioning"
    - from: "a2a_subagent_mesh"
      to: "reader_sa"
      protocol: "GCP IAM API"
      auth: "Read-Only SA Impersonation"
      label: "gcloud_readonly_probe_agent probes resources & Cloud Logging"
      type: "auth"
    - from: "cloudtop_shell"
      to: "reader_sa"
      protocol: "GCP IAM API"
      auth: "Google User ADC"
      label: "Impersonate read-only SA for inspection"
      type: "auth"
```

---

## Architectural Subsystems

### 1. Unified FastAPI + A2A Focal Coordinator & Specialist Mesh
- **Focal Conversational Coordinator (`a2a_software_factory_api`)**: Exposes `POST /api/v1/chat` as a single conversational focal point communicating state from the agent graph to the user and intent from the user to the specialist agents, while mounting native A2A protocol endpoints (`/a2a/focal`, `/a2a/architect`, `/a2a/builder`, `/a2a/wif_delivery`, `/a2a/gcloud_probe`).
- **A2A Specialist Sub-Agent Mesh (`a2a_subagent_mesh`)**:
  - `workspace_architect_agent` (`gemini-2.5-pro`): Inspects target workspaces and designs software & Dendrite/OKF specs.
  - `software_builder_agent` (`gemini-2.5-pro`): Writes software artifacts, tests, and cross-project Terraform HCL.
  - `wif_git_delivery_agent` (`gemini-2.5-pro`): Creates isolated feature branches from `main`, onboards external projects via WIF, commits with multi-line context, requests Human-in-the-Loop approval, and opens Pull Requests.
  - `gcloud_readonly_probe_agent` (`gemini-2.5-flash`): Impersonates `cloudtop-agent-reader` to probe live GCP resources, read Cloud Logging, and verify deployed infrastructure.
  - `software_delivery_pipeline` (`SequentialAgent`) & `parallel_verification_agent` (`ParallelAgent`).

### 2. CI/CD, Golden Dataset Evaluation & WIF Infrastructure Delivery
- **GitHub Actions Workflows**:
  - `agent-eval-and-test.yml`: Executes `pytest` and the Golden Dataset evaluation harness (`evals/run_evaluation_suite.py`) on PRs and pushes.
  - `terraform-plan.yml`: Triggered on pull requests targeting `main`.
  - `terraform-apply.yml`: Triggered upon merge to `main`, authenticating via keyless OIDC Workload Identity Federation (`wif_pool` -> `deployer_sa`).

### 3. Argolis Security Perimeter, Secret Manager & Cloud Run Runtime
- **Privilege Separation**:
  - `github-terraform-deployer`: Service account restricted to CI/CD deployment.
  - `cloudtop-agent-reader`: Read-only service account used by `gcloud_readonly_probe_agent`.
  - `a2a-software-factory-sa`: Least-privilege runtime SA for the Cloud Run v2 service (`cloud_run_factory_service`).
- **Secret Manager & Cloud DLP (`secret_manager_vault`)**: Eliminates hardcoded credentials and scrubs PII from structured JSON logs and persistent vector memory.

---

## Operational Knowledge Framework (OKF) Knowledge Base

Every architectural component identified in the Dendrite architecture diagram is documented in the [OKF Knowledge Base](knowledge_base/README.md):
- **Developer Workstation (`cloudtop_env/`)**:
  - [`cloudtop-shell`](knowledge_base/cloudtop_env/workstation/cloudtop-shell.md), [`isolated-binaries`](knowledge_base/cloudtop_env/package_managers/isolated-binaries.md), [`uv-package-manager`](knowledge_base/cloudtop_env/package_managers/uv-package-manager.md), [`check-architecture-docs`](knowledge_base/cloudtop_env/scripts/check-architecture-docs.md), [`provision-argolis-env`](knowledge_base/cloudtop_env/scripts/provision-argolis-env.md), [`setup-argolis-github-wif`](knowledge_base/cloudtop_env/scripts/setup-argolis-github-wif.md), [`dendrite-architecture-diagrams`](knowledge_base/cloudtop_env/skills/dendrite-architecture-diagrams.md)
- **GitHub Platform & Codebase (`codebase/`)**:
  - [`github-repo`](knowledge_base/codebase/github-repo.md), [`gha-plan`](knowledge_base/codebase/gha-plan.md), [`gha-apply`](knowledge_base/codebase/gha-apply.md), [`agent-eval-pipeline`](knowledge_base/codebase/agent-eval-pipeline.md), [`adk-runtime`](knowledge_base/codebase/adk-runtime.md), [`a2a-software-factory-api`](knowledge_base/codebase/a2a-software-factory-api.md), [`a2a-subagent-mesh`](knowledge_base/codebase/a2a-subagent-mesh.md), [`terraform-infrastructure-modules`](knowledge_base/codebase/terraform-infrastructure-modules.md)
- **Argolis GCP Cloud Assets (`deployed_gcp_assets/`)**:
  - [`wif-pool`](knowledge_base/deployed_gcp_assets/wif-pool.md), [`deployer-sa`](knowledge_base/deployed_gcp_assets/deployer-sa.md), [`reader-sa`](knowledge_base/deployed_gcp_assets/reader-sa.md), [`secret-manager-vault`](knowledge_base/deployed_gcp_assets/secret-manager-vault.md), [`cloud-run-factory-service`](knowledge_base/deployed_gcp_assets/cloud-run-factory-service.md), [`gcs-tfstate`](knowledge_base/deployed_gcp_assets/gcs-tfstate.md), [`vpc-network`](knowledge_base/deployed_gcp_assets/vpc-network.md), [`firewall-rules`](knowledge_base/deployed_gcp_assets/firewall-rules.md), [`compute-instances`](knowledge_base/deployed_gcp_assets/compute-instances.md)
