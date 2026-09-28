---
okf_version: "1.0"
component_id: "firewall-rules"
component_name: "Compute Engine Security Firewalls"
category: "Networking"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Network Security Team"
dendrite_node_id: "firewall_rules"
last_verified: "2026-09-28"
---

# OKF: Compute Engine Security Firewalls

## 1. Executive Summary & Purpose
Compute Engine Security Firewalls enforce ingress and egress network filtering rules at the virtual machine level. They protect Argolis instances from unauthorized network access by strictly limiting inbound traffic to approved Identity-Aware Proxy (IAP) ranges, developer IPs, and internal VPC subnets.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `argolis_project`
- **Inbound Connections**:
  - Ingress traffic from Google Identity-Aware Proxy (IAP) CIDR (`35.235.240.0/20`).
  - Internal subnet-to-subnet traffic.
- **Outbound Connections**:
  - Egress rules filtering outbound connections to public endpoints and GCP APIs.
- **Trust Boundary & Security Classification**: Stateful packet filter enforced by Andromeda virtual network virtualization.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Terraform firewall definitions: [`terraform/main.tf`](../../terraform/main.tf)
- **Protocols & Ports Filtered**:
  - `tcp:22` (SSH via Identity-Aware Proxy / IAP)
  - `tcp:80`, `tcp:443` (HTTP/HTTPS for web agents if enabled)
  - `icmp` (Diagnostics)
- **Source Ranges**:
  - IAP Range: `35.235.240.0/20`
  - Internal VPC CIDR: `10.128.0.0/9`

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Defined declaratively in Terraform manifests.
- **Verification & Health Checks**:
  ```bash
  gcloud compute firewall-rules list --filter="network:default"
  gcloud compute firewall-rules describe default-allow-ssh
  ```
- **Failure Modes & Blast Radius**:
  - Overly restrictive firewall rules block SSH or agent telemetry; overly permissive rules violate zero-trust policy.
- **Recovery & Troubleshooting**:
  - Test IAP connectivity:
    ```bash
    gcloud compute ssh <INSTANCE> --tunnel-through-iap
    ```

## 5. References & Linked Assets
- Dendrite Diagram Node: `firewall_rules` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Related OKF Entries: [`vpc-network`](vpc-network.md), [`compute-vm`](compute-vm.md)
