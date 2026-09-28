---
okf_version: "1.0"
component_id: "compute-vm"
component_name: "Argolis Compute Engine Instances"
category: "Compute & Runtime"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Infrastructure & Compute Operations"
dendrite_node_id: "compute_vm"
last_verified: "2026-09-28"
---

# OKF: Argolis Compute Engine Instances

## 1. Executive Summary & Purpose
Argolis Compute Engine Instances provide dedicated virtual machine compute resources deployed within the Argolis sandbox. They execute test workloads, host microservices, and provide isolated agent validation environments managed completely via Terraform and the `./bin/argolis` CLI helper.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `argolis_project`
- **Inbound Connections**:
  - `gha_apply`: Provisioned, resized, or updated via Terraform `google_compute_instance`.
  - `cloudtop_shell`: Accessed via `./bin/argolis ssh` (tunneled through IAP).
- **Outbound Connections**:
  - `gcs_tfstate`, Google APIs: Reached via private Google access or NAT.
- **Trust Boundary & Security Classification**: Isolated compute tier within private VPC subnet.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Instance definition: [`terraform/main.tf`](../../terraform/main.tf)
  - Variables: [`terraform/variables.tf`](../../terraform/variables.tf)
  - Outputs: [`terraform/outputs.tf`](../../terraform/outputs.tf)
  - Helper CLI: [`bin/argolis`](../../bin/argolis)
- **Machine Specifications**:
  - Machine Type: `e2-medium` (or custom configured via `instance_type`)
  - Operating System: Debian GNU/Linux 12 (Bookworm)
  - Boot Disk: 20 GB standard persistent disk (`pd-standard`)
  - Zone: `us-central1-a`

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Automated by GitHub Actions merge or manual Terraform apply:
    ```bash
    ./bin/terraform -chdir=terraform apply
    ```
- **Verification & Health Checks**:
  ```bash
  ./bin/argolis status
  ./bin/argolis list
  ```
- **Lifecycle Management**:
  ```bash
  ./bin/argolis start <INSTANCE_NAME>
  ./bin/argolis stop <INSTANCE_NAME>
  ./bin/argolis ssh <INSTANCE_NAME>
  ```
- **Failure Modes & Blast Radius**:
  - Instance crashes or misconfigurations only affect isolated workloads on that VM; VPC network and state bucket remain intact.
- **Recovery & Troubleshooting**:
  - Review serial console output:
    ```bash
    gcloud compute instances get-serial-port-output <INSTANCE_NAME>
    ```

## 5. References & Linked Assets
- Dendrite Diagram Node: `compute_vm` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Related OKF Entries: [`vpc-network`](vpc-network.md), [`firewall-rules`](firewall-rules.md), [`deployer-sa`](deployer-sa.md), [`compute-instances`](../deployed_gcp_assets/compute-instances.md), [`terraform-infrastructure-modules`](../codebase/terraform-infrastructure-modules.md)
