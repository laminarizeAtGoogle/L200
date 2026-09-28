---
okf_version: "1.0"
entry_id: "vpc-network"
entry_name: "Virtual Private Cloud (VPC) & Subnets"
category: "deployed_gcp_assets"
sub_category: "networking"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Network Infrastructure Team"
dendrite_node_id: "vpc_network"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Deployed GCP Asset): Virtual Private Cloud (VPC) & Subnets

## 1. Executive Summary & Purpose
The VPC Network defines the software-defined networking perimeter for the Argolis GCP sandbox. It isolates internal compute instances, manages IP address allocation (CIDR blocks), routes internal traffic, and provides private Google access for internal workloads.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `argolis_project`
- **Inbound Connections**:
  - `gha_apply`: Provisioned and updated via Terraform (`google_compute_network`).
  - External SSH/IAP ingress routed through firewall rules.
- **Outbound Connections**:
  - `compute_vm`: Provides network interfaces (`nic0`) and IP assignment.
  - Private Google APIs: Route traffic internally without public IP exposure.
- **Trust Boundary & Security Classification**: Isolated VPC boundary in `us-central1`.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Network manifests: [`terraform/main.tf`](../../../terraform/main.tf)
  - Variables: [`terraform/variables.tf`](../../../terraform/variables.tf)
- **Subnet Configuration**:
  - Region: `us-central1`
  - Subnet CIDR: `10.128.0.0/20` (or default subnetwork)
  - MTU: `1460`
  - Routing mode: `REGIONAL`

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Managed via Terraform in `terraform/main.tf`:
    ```bash
    ./bin/terraform -chdir=terraform apply
    ```
- **Verification & Health Checks**:
  ```bash
  gcloud compute networks describe default
  gcloud compute networks subnets list --network=default
  ```
- **Failure Modes & Blast Radius**:
  - Network deletion or routing changes disconnect running compute instances.
- **Recovery & Troubleshooting**:
  - Review network routes and subnets: `gcloud compute routes list --filter="network:default"`

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `vpc_network` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Security Firewalls: [`deployed_gcp_assets/firewall-rules.md`](firewall-rules.md)
  - Compute Instances: [`deployed_gcp_assets/compute-instances.md`](compute-instances.md)
  - Terraform Modules: [`codebase/terraform-infrastructure-modules.md`](../codebase/terraform-infrastructure-modules.md)
