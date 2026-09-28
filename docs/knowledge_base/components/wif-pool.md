---
okf_version: "1.0"
component_id: "wif-pool"
component_name: "Workload Identity Federation (WIF) Pool & Provider"
category: "IAM & Security"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Security Architecture / IAM Team"
dendrite_node_id: "wif_pool"
last_verified: "2026-09-28"
---

# OKF: Workload Identity Federation (WIF) Pool & Provider

## 1. Executive Summary & Purpose
Workload Identity Federation (WIF) enables GitHub Actions workflows to authenticate to Google Cloud without storing static service account keys in GitHub Secrets. It exchanges short-lived GitHub OIDC JWT tokens for federated Google access tokens.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `gcp_iam_boundary`
- **Inbound Connections**:
  - `gha_plan`, `gha_apply`: Sends GitHub OIDC JWT via HTTPS to Google Security Token Service (STS).
- **Outbound Connections**:
  - `deployer_sa`: Permits token exchange to impersonate `github-terraform-deployer` SA based on repository attribute condition.
- **Trust Boundary & Security Classification**: Zero-Key Trust Boundary. Strict attribute condition restricts federation strictly to the designated repository (`attribute.repository == "OWNER/REPO"`).

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Provisioning script: [`scripts/setup-argolis-github-wif.sh`](../../scripts/setup-argolis-github-wif.sh)
- **Protocols & Interfaces**: HTTPS / OIDC (OpenID Connect v1.0) / OAuth 2.0 Token Exchange (RFC 8693).
- **GCP Resource Hierarchy**:
  - Pool: `projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-actions-pool`
  - Provider: `.../providers/github-provider`
- **Issuer URL**: `https://token.actions.githubusercontent.com`
- **Attribute Mapping**:
  ```text
  google.subject=assertion.sub
  attribute.actor=assertion.actor
  attribute.repository=assertion.repository
  attribute.ref=assertion.ref
  ```

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  ./scripts/setup-argolis-github-wif.sh --project <PROJECT_ID> --repo <OWNER/REPO>
  ```
- **Verification & Health Checks**:
  ```bash
  gcloud iam workload-identity-pools describe github-actions-pool --location=global
  gcloud iam workload-identity-pools providers describe github-provider --workload-identity-pool=github-actions-pool --location=global
  ```
- **Failure Modes & Blast Radius**:
  - Misconfigured repository filter or issuer URL causes OIDC validation rejection; all CI/CD pipelines fail to authenticate.
- **Recovery & Troubleshooting**:
  - Confirm repository attribute match: check `assertion.repository` in GitHub Actions logs against the WIF provider condition.

## 5. References & Linked Assets
- Dendrite Diagram Node: `wif_pool` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Google Cloud WIF Guide: `https://cloud.google.com/iam/docs/workload-identity-federation`
- Related OKF Entries: [`deployer-sa`](deployer-sa.md), [`gha-plan`](gha-plan.md), [`gha-apply`](gha-apply.md), [`setup-argolis-github-wif`](../cloudtop_env/scripts/setup-argolis-github-wif.md)
