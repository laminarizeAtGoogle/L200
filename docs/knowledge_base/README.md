# Operational Knowledge Framework (OKF) Knowledge Base

Welcome to the **Operational Knowledge Framework (OKF)** catalog for the L200 & Argolis workspace.

Following Google OKF standards, every architectural component represented in the [Dendrite Architecture Diagram](../architecture_diagram.dendrite.yaml) possesses a formal, structured entry documented below. In addition, detailed operational guides, environment configurations, and live asset runbooks are maintained within subcategory directories.

---

## 1. Canonical Architectural Components (`components/`)

These documents represent the 1-to-1 canonical architecture components matching nodes in the authoritative [Google Dendrite Architecture Diagram](../architecture_diagram.dendrite.yaml).

| Component ID | Component Name | Subsystem / Boundary | Category | Criticality Tier | Dendrite Node ID | OKF Document |
|:---|:---|:---|:---|:---|:---|:---|
| `cloudtop-shell` | Cloudtop Terminal & Antigravity Shell | Developer Workstation | Dev Tooling | Tier 3 - Development | `cloudtop_shell` | [`cloudtop-shell.md`](components/cloudtop-shell.md) |
| `adk-runtime` | Google ADK Agent Runtime & Python Toolchain | Developer Workstation | Compute & Runtime | Tier 2 - Operational | `adk_runtime` | [`adk-runtime.md`](components/adk-runtime.md) |
| `isolated-binaries` | Hermetic Standalone Toolchain (`./bin`) | Developer Workstation | Dev Tooling | Tier 3 - Development | `isolated_binaries` | [`isolated-binaries.md`](components/isolated-binaries.md) |
| `github-repo` | GitHub Repository (L200) | GitHub Platform | CI/CD | Tier 1 - Critical Path | `github_repo` | [`github-repo.md`](components/github-repo.md) |
| `gha-plan` | GitHub Actions: Terraform Plan Pipeline | GitHub Platform | CI/CD | Tier 1 - Critical Path | `gha_plan` | [`gha-plan.md`](components/gha-plan.md) |
| `gha-apply` | GitHub Actions: Terraform Apply Pipeline | GitHub Platform | CI/CD | Tier 1 - Critical Path | `gha_apply` | [`gha-apply.md`](components/gha-apply.md) |
| `wif-pool` | Workload Identity Federation (WIF) Pool | GCP IAM Boundary | IAM & Security | Tier 1 - Critical Path | `wif_pool` | [`wif-pool.md`](components/wif-pool.md) |
| `deployer-sa` | Deployer Service Account (`github-terraform-deployer`) | GCP IAM Boundary | IAM & Security | Tier 1 - Critical Path | `deployer_sa` | [`deployer-sa.md`](components/deployer-sa.md) |
| `reader-sa` | Read-Only Service Account (`cloudtop-agent-reader`) | GCP IAM Boundary | IAM & Security | Tier 2 - Operational | `reader_sa` | [`reader-sa.md`](components/reader-sa.md) |
| `gcs-tfstate` | Cloud Storage Remote Terraform State Bucket | Argolis GCP Project | Storage & Data | Tier 1 - Critical Path | `gcs_tfstate` | [`gcs-tfstate.md`](components/gcs-tfstate.md) |
| `vpc-network` | Virtual Private Cloud (VPC) & Subnets | Argolis GCP Project | Networking | Tier 1 - Critical Path | `vpc_network` | [`vpc-network.md`](components/vpc-network.md) |
| `firewall-rules` | Compute Engine Security Firewalls | Argolis GCP Project | Networking | Tier 1 - Critical Path | `firewall_rules` | [`firewall-rules.md`](components/firewall-rules.md) |
| `compute-vm` | Argolis Compute Engine Instances | Argolis GCP Project | Compute & Runtime | Tier 1 - Critical Path | `compute_vm` | [`compute-vm.md`](components/compute-vm.md) |

---

## 2. Subcategory Operational Guides & Environment Runbooks

These entries provide in-depth operational procedures, implementation specifications, runtime scripts, and asset runbooks organized across the three OKF pillars:

### A. Cloudtop Developer Environment (`cloudtop_env/`)

Documents workstation tools, package managers, agent skills, and automation scripts.

| Entry ID | Title / Capability | Sub-Category | Associated Component | OKF Document |
|:---|:---|:---|:---|:---|
| `uv-package-manager` | uv Python Package & Project Manager | `package_managers` | `isolated-binaries`, `adk-runtime` | [`uv-package-manager.md`](cloudtop_env/package_managers/uv-package-manager.md) |
| `check-architecture-docs` | Architecture Documentation Pre-Push Gate | `scripts` | `cloudtop-shell` | [`check-architecture-docs.md`](cloudtop_env/scripts/check-architecture-docs.md) |
| `provision-argolis-env` | Argolis Zero-Privilege IAM Provisioning Script | `scripts` | `reader-sa` | [`provision-argolis-env.md`](cloudtop_env/scripts/provision-argolis-env.md) |
| `setup-argolis-github-wif` | Argolis WIF & Terraform State Setup Script | `scripts` | `wif-pool`, `deployer-sa` | [`setup-argolis-github-wif.md`](cloudtop_env/scripts/setup-argolis-github-wif.md) |
| `dendrite-architecture-diagrams` | Dendrite Architecture Diagrams Skill | `skills` | `cloudtop-shell` | [`dendrite-architecture-diagrams.md`](cloudtop_env/skills/dendrite-architecture-diagrams.md) |

### B. Codebase Modules & Pipelines (`codebase/`)

Documents Infrastructure as Code modules, CI/CD pipelines, and agent application runtimes.

| Entry ID | Title / Capability | Sub-Category | Associated Component | OKF Document |
|:---|:---|:---|:---|:---|
| `terraform-infrastructure-modules` | Terraform Infrastructure Modules | `terraform` | `github-repo`, `gcs-tfstate` | [`terraform-infrastructure-modules.md`](codebase/terraform-infrastructure-modules.md) |

### C. Deployed GCP Cloud Assets (`deployed_gcp_assets/`)

Documents live deployed cloud resources discovered via the read-only agent inspection persona (`cloudtop-agent-reader`).

| Entry ID | Title / Capability | Sub-Category | Associated Component | OKF Document |
|:---|:---|:---|:---|:---|
| `compute-instances` | Argolis Compute Engine Instances | `compute` | `compute-vm`, `vpc-network` | [`compute-instances.md`](deployed_gcp_assets/compute-instances.md) |

---

## 3. Standards, Schemas & Maintenance

- **Schema Definition**: See [Google OKF Specification](OKF_SPEC.md) for required YAML frontmatter and documentation sections.
- **Entry Templates**:
  - General Template: [`TEMPLATE.md`](TEMPLATE.md)
  - Cloudtop Environment Template: [`templates/cloudtop_env_template.md`](templates/cloudtop_env_template.md)
  - Codebase Module Template: [`templates/codebase_template.md`](templates/codebase_template.md)
  - Deployed GCP Asset Template: [`templates/deployed_gcp_asset_template.md`](templates/deployed_gcp_asset_template.md)
- **Dendrite Diagram Synchronization**: When adding or updating components in [Dendrite](http://go/dendrite) (or viewing in [Dendrite Playground](http://go/dendrite-playground)) and in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml), a corresponding OKF document must be added or revised under [`components/`](components/).
- **Pre-Push Validation**: The repository's `git-push-architecture-docs-gate` validates that `./docs` and its knowledge base components reflect all outgoing changes prior to executing `git push`.
