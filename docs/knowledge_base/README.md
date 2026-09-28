# Operational Knowledge Framework (OKF) Knowledge Base

Welcome to the **Operational Knowledge Framework (OKF)** catalog for the L200, Argolis & **A2A Software Factory** workspace.

Following Google OKF standards, every architectural component represented in the [Google Dendrite Architecture Diagram](../architecture_diagram.dendrite.yaml) and all operational runbooks are organized across three canonical architectural pillars:

1. **Cloudtop Environment (`cloudtop_env/`)**: Workstation shell, hermetic package managers, developer toolchains, pre-push lifecycle gates, and agent skills.
2. **Codebase & CI/CD (`codebase/`)**: Git repository configuration, CI/CD & evaluation pipelines, Google ADK agent runtime, Unified FastAPI + A2A Focal Coordinator server, specialist A2A sub-agent mesh, and Terraform Infrastructure as Code (IaC) modules.
3. **Deployed GCP Assets (`deployed_gcp_assets/`)**: Workload Identity Federation (WIF) perimeter, IAM service accounts, Secret Manager & Cloud DLP vault, Cloud Run v2 A2A Factory service & memory bucket, GCS remote state storage, VPC networks, firewall rules, and Compute Engine VM instances.

---

## Architecture Cross-Reference Matrix & Complete Catalog

### 1. Developer Workstation Environment (`cloudtop_env/`)

| Entry ID | Component / Capability | Category / Subcategory | Dendrite Node ID | Tier | OKF Document |
|:---|:---|:---|:---|:---|:---|
| `cloudtop-shell` | Cloudtop Terminal & Antigravity Shell | `cloudtop_env/workstation` | `cloudtop_shell` | Tier 3 - Development | [`cloudtop-shell.md`](cloudtop_env/workstation/cloudtop-shell.md) |
| `isolated-binaries` | Hermetic Standalone Toolchain (`./bin`) | `cloudtop_env/package_managers` | `isolated_binaries` | Tier 3 - Development | [`isolated-binaries.md`](cloudtop_env/package_managers/isolated-binaries.md) |
| `uv-package-manager` | uv Python Package & Project Manager | `cloudtop_env/package_managers` | `isolated_binaries` | Tier 3 - Development | [`uv-package-manager.md`](cloudtop_env/package_managers/uv-package-manager.md) |
| `check-architecture-docs` | Architecture Documentation Pre-Push Gate | `cloudtop_env/scripts` | `cloudtop_shell` | Tier 3 - Development | [`check-architecture-docs.md`](cloudtop_env/scripts/check-architecture-docs.md) |
| `provision-argolis-env` | Argolis Zero-Privilege IAM Provisioning Script | `cloudtop_env/scripts` | `reader_sa` | Tier 1 - Critical Path | [`provision-argolis-env.md`](cloudtop_env/scripts/provision-argolis-env.md) |
| `setup-argolis-github-wif` | Argolis WIF & Terraform State Setup Script | `cloudtop_env/scripts` | `wif_pool` | Tier 1 - Critical Path | [`setup-argolis-github-wif.md`](cloudtop_env/scripts/setup-argolis-github-wif.md) |
| `dendrite-architecture-diagrams` | Dendrite Architecture Diagrams Skill | `cloudtop_env/skills` | `cloudtop_shell` | Tier 3 - Development | [`dendrite-architecture-diagrams.md`](cloudtop_env/skills/dendrite-architecture-diagrams.md) |

### 2. Codebase Modules & CI/CD Pipelines (`codebase/`)

| Entry ID | Component / Capability | Category / Subcategory | Dendrite Node ID | Tier | OKF Document |
|:---|:---|:---|:---|:---|:---|
| `github-repo` | GitHub Repository (L200) | `codebase/cicd` | `github_repo` | Tier 1 - Critical Path | [`github-repo.md`](codebase/github-repo.md) |
| `gha-plan` | GitHub Actions: Terraform Plan Pipeline | `codebase/cicd` | `gha_plan` | Tier 1 - Critical Path | [`gha-plan.md`](codebase/gha-plan.md) |
| `gha-apply` | GitHub Actions: Terraform Apply Pipeline | `codebase/cicd` | `gha_apply` | Tier 1 - Critical Path | [`gha-apply.md`](codebase/gha-apply.md) |
| `agent-eval-pipeline` | Golden Dataset Evaluation Harness & CI Pipeline | `codebase/cicd` | `agent_eval_pipeline` | Tier 1 - Critical Path | [`agent-eval-pipeline.md`](codebase/agent-eval-pipeline.md) |
| `adk-runtime` | Google ADK Agent Runtime & Python Toolchain | `codebase/agent_runtime` | `adk_runtime` | Tier 2 - Operational | [`adk-runtime.md`](codebase/adk-runtime.md) |
| `a2a-software-factory-api` | Unified FastAPI + A2A Focal Coordinator Server | `codebase/agent_runtime` | `a2a_software_factory_api` | Tier 1 - Critical Path | [`a2a-software-factory-api.md`](codebase/a2a-software-factory-api.md) |
| `a2a-subagent-mesh` | A2A Multi-Agent Specialist Mesh & Tool Suite | `codebase/agent_runtime` | `a2a_subagent_mesh` | Tier 1 - Critical Path | [`a2a-subagent-mesh.md`](codebase/a2a-subagent-mesh.md) |
| `terraform-infrastructure-modules` | Terraform Infrastructure Modules | `codebase/terraform` | `github_repo` | Tier 1 - Critical Path | [`terraform-infrastructure-modules.md`](codebase/terraform-infrastructure-modules.md) |

### 3. Deployed GCP Cloud Assets (`deployed_gcp_assets/`)

| Entry ID | Component / Capability | Category / Subcategory | Dendrite Node ID | Tier | OKF Document |
|:---|:---|:---|:---|:---|:---|
| `wif-pool` | Workload Identity Federation (WIF) Pool | `deployed_gcp_assets/iam` | `wif_pool` | Tier 1 - Critical Path | [`wif-pool.md`](deployed_gcp_assets/wif-pool.md) |
| `deployer-sa` | Deployer Service Account (`github-terraform-deployer`) | `deployed_gcp_assets/iam` | `deployer_sa` | Tier 1 - Critical Path | [`deployer-sa.md`](deployed_gcp_assets/deployer-sa.md) |
| `reader-sa` | Read-Only Service Account (`cloudtop-agent-reader`) | `deployed_gcp_assets/iam` | `reader_sa` | Tier 2 - Operational | [`reader-sa.md`](deployed_gcp_assets/reader-sa.md) |
| `secret-manager-vault` | Google Cloud Secret Manager & DLP Redaction Vault | `deployed_gcp_assets/iam` | `secret_manager_vault` | Tier 1 - Critical Path | [`secret-manager-vault.md`](deployed_gcp_assets/secret-manager-vault.md) |
| `cloud-run-factory-service` | A2A Software Factory Cloud Run Service & Memory Bucket | `deployed_gcp_assets/compute` | `cloud_run_factory_service` | Tier 1 - Critical Path | [`cloud-run-factory-service.md`](deployed_gcp_assets/cloud-run-factory-service.md) |
| `gcs-tfstate` | Cloud Storage Remote Terraform State Bucket | `deployed_gcp_assets/storage` | `gcs_tfstate` | Tier 1 - Critical Path | [`gcs-tfstate.md`](deployed_gcp_assets/gcs-tfstate.md) |
| `vpc-network` | Virtual Private Cloud (VPC) & Subnets | `deployed_gcp_assets/networking` | `vpc_network` | Tier 1 - Critical Path | [`vpc-network.md`](deployed_gcp_assets/vpc-network.md) |
| `firewall-rules` | Compute Engine Security Firewalls | `deployed_gcp_assets/networking` | `firewall_rules` | Tier 1 - Critical Path | [`firewall-rules.md`](deployed_gcp_assets/firewall-rules.md) |
| `compute-instances` | Argolis Compute Engine Instances | `deployed_gcp_assets/compute` | `compute_vm` | Tier 1 - Critical Path | [`compute-instances.md`](deployed_gcp_assets/compute-instances.md) |

---

## Standards, Schemas & Maintenance

- **Schema Definition**: See [Google OKF Specification](OKF_SPEC.md) for required YAML frontmatter and documentation sections.
- **Entry Templates**:
  - General Template: [`TEMPLATE.md`](TEMPLATE.md)
  - Cloudtop Environment Template: [`templates/cloudtop_env_template.md`](templates/cloudtop_env_template.md)
  - Codebase Module Template: [`templates/codebase_template.md`](templates/codebase_template.md)
  - Deployed GCP Asset Template: [`templates/deployed_gcp_asset_template.md`](templates/deployed_gcp_asset_template.md)
- **Dendrite Diagram Synchronization**: When adding or updating components in [Dendrite](http://go/dendrite) (or viewing in [Dendrite Playground](http://go/dendrite-playground)) and in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml), a corresponding OKF document must be added or revised under its corresponding category.
- **Pre-Push Validation**: The repository's `git-push-architecture-docs-gate` validates that `./docs` and its knowledge base components reflect all outgoing changes prior to executing `git push`.
