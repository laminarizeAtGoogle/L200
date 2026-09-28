# L200 System & Infrastructure Architecture

This document serves as the authoritative architectural blueprint for the Google Academy L200 and Argolis workspace.

---

## Canonical Architecture Diagram

> **Authoritative Architecture Platform**: Google Internal **Dendrite** ([go/dendrite](http://go/dendrite))  
> **Interactive Diagram Viewer**: [go/dendrite-playground](http://go/dendrite-playground)  
> **Source Model File**: [`docs/architecture_diagram.dendrite.yaml`](architecture_diagram.dendrite.yaml)  
> **Last Synchronized**: 2026-09-28

```yaml
# Dendrite Declarative Architecture Specification (go/dendrite)
dendrite_diagram:
  title: "L200 Argolis Infrastructure, CI/CD & Agent Architecture"
  version: "1.0.0"
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
          role: "Python 3.12 + Google ADK agent execution"
        - id: "isolated_binaries"
          label: "Standalone Binaries (./bin)"
          type: "toolchain"
          role: "Terraform v1.16.4, gcloud SDK, gh CLI, uv"

    - id: "github_platform"
      label: "GitHub Enterprise / Cloud"
      type: "vcs_cicd"
      trust_level: "managed_external"
      components:
        - id: "github_repo"
          label: "GitHub Repository (L200)"
          type: "vcs_repository"
          role: "Git source of truth with strict sanitization hooks"
        - id: "gha_plan"
          label: "GitHub Actions: terraform-plan.yml"
          type: "ci_pipeline"
          role: "Automated lint, init, validate, and plan on PRs"
        - id: "gha_apply"
          label: "GitHub Actions: terraform-apply.yml"
          type: "cd_pipeline"
          role: "Automated terraform apply on merge to main"

    - id: "gcp_iam_boundary"
      label: "Google Cloud IAM & Workload Identity"
      type: "security_perimeter"
      trust_level: "zero_privilege"
      components:
        - id: "wif_pool"
          label: "Workload Identity Pool & Provider"
          type: "iam_wif"
          role: "OIDC validation for GitHub Actions (no static keys)"
        - id: "deployer_sa"
          label: "Deployer Service Account"
          type: "service_account"
          role: "github-terraform-deployer SA (scoped Compute & Storage Admin)"
        - id: "reader_sa"
          label: "Read-Only Cloudtop SA"
          type: "service_account"
          role: "cloudtop-agent-reader SA (Viewer permissions only)"

    - id: "argolis_project"
      label: "Argolis GCP Project (Sandbox)"
      type: "gcp_project"
      trust_level: "cloud_resources"
      components:
        - id: "gcs_tfstate"
          label: "Cloud Storage (tfstate Bucket)"
          type: "cloud_storage"
          role: "Remote encrypted Terraform state with object locking"
        - id: "vpc_network"
          label: "VPC Network & Subnet"
          type: "vpc_networking"
          role: "Isolated virtual private network (e.g. us-central1)"
        - id: "firewall_rules"
          label: "Firewall Rules"
          type: "security_firewall"
          role: "Ingress controls (SSH/IAP, internal subnets)"
        - id: "compute_vm"
          label: "Compute Engine Instances"
          type: "compute_engine"
          role: "Managed VM workloads and test beds"

  connections:
    - from: "cloudtop_shell"
      to: "github_repo"
      protocol: "HTTPS / SSH"
      auth: "GitHub CLI / SSH Key"
      label: "git push (gated by pre-push hooks)"
      type: "control"
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
      to: "vpc_network"
      protocol: "HTTPS / GCP Compute API"
      auth: "Deployer SA Token"
      label: "Apply VPC & Subnet configuration"
      type: "provisioning"
    - from: "gha_apply"
      to: "firewall_rules"
      protocol: "HTTPS / GCP Compute API"
      auth: "Deployer SA Token"
      label: "Apply firewall rules"
      type: "provisioning"
    - from: "gha_apply"
      to: "compute_vm"
      protocol: "HTTPS / GCP Compute API"
      auth: "Deployer SA Token"
      label: "Provision & manage Compute Engine VMs"
      type: "provisioning"
    - from: "cloudtop_shell"
      to: "reader_sa"
      protocol: "GCP IAM API"
      auth: "Google User ADC"
      label: "Impersonate read-only SA for inspection"
      type: "auth"
```

---

## Architectural Subsystems

### 1. Developer Environment & Toolchain Isolation
- **Location**: `/usr/local/google/home/joshholtz/Documents/L200`
- **Binaries (`./bin`)**: Standalone, hermetic binaries for `terraform` (v1.16.4), `gcloud`, `gh` (v2.101.0), and `uv` (v0.12.16).
- **Google Agent Development Kit (ADK)**: Python 3.12 standalone toolchain managed with `uv`, integrating ADK agents with Vertex AI services and local execution runtimes.
- **Pre-Push Lifecycle Hooks**: Enforce credential sanitization (cookies, JWTs, API keys) and verify architecture documentation updates prior to `git push`.

### 2. CI/CD & Automated Infrastructure Delivery
- **GitHub Actions Workflows**:
  - `terraform-plan.yml`: Triggered on pull requests targeting `main`. Performs format verification, initialization, validation, and plan generation.
  - `terraform-apply.yml`: Triggered upon merge to `main`. Executes automated `terraform apply` against the remote state.
- **Zero-Key Authentication (WIF)**: All CI/CD actions authenticate to GCP via **Workload Identity Federation** using GitHub OIDC tokens, avoiding long-lived static service account keys.

### 3. Argolis Security Perimeter & IAM Controls
- **Privilege Separation**:
  - `github-terraform-deployer`: Service account restricted to deployment roles (Compute Admin, Storage Admin).
  - `cloudtop-agent-reader`: Read-only service account for local Cloudtop inspection via impersonation.
- **Remote State Backend**: GCS bucket with uniform bucket-level access and encryption storing `terraform.tfstate`.

### 4. Compute & Network Infrastructure
- **VPC & Subnets**: Regional networks in `us-central1` hosting Compute Engine instances.
- **Firewall Rules**: Strictly controlled ingress (SSH/IAP and internal communications) defined declaratively in [`terraform/`](../terraform/).

---

## Operational Knowledge Framework (OKF) Knowledge Base

Every architectural component identified in the Dendrite architecture diagram is documented in detail in the [OKF Knowledge Base](knowledge_base/README.md) organized across three operational pillars:
- **Developer Workstation (`cloudtop_env/`)**:
  - Environment & Shell: [`cloudtop-shell`](knowledge_base/cloudtop_env/workstation/cloudtop-shell.md)
  - Toolchains & Packages: [`isolated-binaries`](knowledge_base/cloudtop_env/package_managers/isolated-binaries.md), [`uv-package-manager`](knowledge_base/cloudtop_env/package_managers/uv-package-manager.md)
  - Provisioning & Setup Scripts: [`provision-argolis-env`](knowledge_base/cloudtop_env/scripts/provision-argolis-env.md), [`setup-argolis-github-wif`](knowledge_base/cloudtop_env/scripts/setup-argolis-github-wif.md)
  - Architectural Governance: [`check-architecture-docs`](knowledge_base/cloudtop_env/scripts/check-architecture-docs.md), [`dendrite-architecture-diagrams`](knowledge_base/cloudtop_env/skills/dendrite-architecture-diagrams.md)
- **GitHub Platform & Codebase (`codebase/`)**:
  - Version Control: [`github-repo`](knowledge_base/codebase/github-repo.md)
  - CI/CD Pipelines: [`gha-plan`](knowledge_base/codebase/gha-plan.md), [`gha-apply`](knowledge_base/codebase/gha-apply.md)
  - Agent Runtime: [`adk-runtime`](knowledge_base/codebase/adk-runtime.md)
  - Infrastructure as Code: [`terraform-infrastructure-modules`](knowledge_base/codebase/terraform-infrastructure-modules.md)
- **Argolis GCP Cloud Assets (`deployed_gcp_assets/`)**:
  - IAM & Security Perimeter: [`wif-pool`](knowledge_base/deployed_gcp_assets/wif-pool.md), [`deployer-sa`](knowledge_base/deployed_gcp_assets/deployer-sa.md), [`reader-sa`](knowledge_base/deployed_gcp_assets/reader-sa.md)
  - Remote State Backend: [`gcs-tfstate`](knowledge_base/deployed_gcp_assets/gcs-tfstate.md)
  - Networking & Ingress: [`vpc-network`](knowledge_base/deployed_gcp_assets/vpc-network.md), [`firewall-rules`](knowledge_base/deployed_gcp_assets/firewall-rules.md)
  - Compute Workloads: [`compute-instances`](knowledge_base/deployed_gcp_assets/compute-instances.md)

---

## Architectural Maintenance Requirements

As mandated by repository policy:
1. Any code, infrastructure, or configuration update pushed to GitHub **must be reflected** in this document and in [`docs/architecture_diagram.dendrite.yaml`](architecture_diagram.dendrite.yaml).
2. Each architectural component must have an up-to-date entry in [`docs/knowledge_base/`](knowledge_base/README.md) conforming to [Google OKF Specification](knowledge_base/OKF_SPEC.md).
3. The pre-command hook (`git-push-architecture-docs-gate`) triggers the subagent slash command `/update-architecture-docs` to update the architecture documentation and Dendrite diagrams before allowing `git push`.
