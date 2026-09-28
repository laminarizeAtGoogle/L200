---
name: dendrite-architecture-diagrams
description: Instructs agents to always use Google's internal Dendrite diagram tool (go/dendrite) when building, proposing, or documenting architecture diagrams, system designs, or cloud infrastructure topologies.
---

# Dendrite Architecture Diagrams Skill

This skill enforces the mandatory standard for authoring system and infrastructure architecture diagrams within this workspace and Google engineering environments.

## Mandatory Policy

Whenever an agent or engineer is asked to design, document, propose, or update a system architecture, infrastructure topology, data flow, or component design:

1. **Always Use Dendrite (`go/dendrite`)**:
   - The agent **MUST** use Google's internal **Dendrite** diagram tool ([go/dendrite](http://go/dendrite)) as the authoritative platform for building and publishing architecture diagrams.
   - **Do NOT** use external third-party diagram tools (such as Lucidchart, draw.io, Visio, or Miro).
   - If an inline text representation is requested in markdown (e.g., in OpenSpec `design.md`, RFCs, PRDs, or `README.md`), the agent must provide:
     - The canonical link to the diagram in Dendrite ([go/dendrite](http://go/dendrite)) and the interactive viewer in the Dendrite Playground ([go/dendrite-playground](http://go/dendrite-playground)).
     - A structured, declarative Dendrite specification (YAML/JSON blueprint) representing the topology.
     - An optional high-level ASCII or Mermaid flow summary for fast text scanning, explicitly noting that Dendrite is the primary source of truth.

---

## Scope & Applicability

This skill applies whenever producing or reviewing:
- **Cloud Infrastructure Topologies**: Google Cloud Platform (GCP) projects, Argolis sandbox environments, VPC networks, subnets, firewall rules, and compute instances.
- **Agentic & AI System Architectures**: Google Agent Development Kit (ADK) agents, Vertex AI Reasoning Engine / Agent Engine, Vertex AI Search & Vector Stores, LLM routing, and memory consolidation pipelines.
- **Security & IAM Boundaries**: Workload Identity Federation (WIF) pools, Service Account impersonation, zero-privilege IAM perimeters, and VPC Service Controls (VPC-SC).
- **CI/CD & Deployment Pipelines**: GitHub Actions workflows, Terraform state backends (GCS), artifact registries, and deployment runners.
- **Microservices & Data Flows**: Inter-service communications, gRPC/REST APIs, event-driven streaming (Pub/Sub), and database storage layers.

---

## Dendrite Architecture Standards & Conventions

When constructing architecture diagrams in Dendrite, agents must follow standard Google Cloud and enterprise engineering conventions:

### 1. Hierarchical Containment & Boundaries
Represent architectural security and resource boundaries cleanly using Dendrite group/container frames:
- **Google Cloud Organization & Folders**: Top-level governance boundary.
- **Google Cloud Project**: Resource and billing container (e.g., `argolis-project-id`).
- **Network / VPC Perimeter**: Virtual Private Cloud networks, shared VPCs, and subnets.
- **Security & IAM Trust Zones**: Explicitly delineate public internet, untrusted clients, authenticated developer environments (Cloudtop), and zero-privilege execution sandboxes.
- **VPC Service Controls (VPC-SC)**: Clearly demarcate the perimeter enclosing sensitive storage (GCS) and APIs.

### 2. Standard Component Notations
Every component on the diagram must specify:
- **Component Identifier**: Clear, descriptive name (e.g., `Agent Runner`, `GCS Remote State Bucket`, `WIF Provider`).
- **Service Type / Icon**: Official Google Cloud product or infrastructure icon (e.g., Compute Engine, Cloud Run, Vertex AI, Cloud Storage, Pub/Sub, IAM).
- **Execution Role**: Brief description of runtime responsibility (e.g., `Ephemeral CI/CD runner`, `Read-only IAM Service Account`).
- **Tier / Zone**: Region (e.g., `us-central1`), zone (`us-central1-a`), or network tier.

### 3. Connector Lines & Data Flows
- **Directionality**: Use directed arrows showing the direction of requests/flow. Preferred layout is **Left-to-Right** (Ingress / Client $\rightarrow$ Logic / Agent $\rightarrow$ Storage / Downstream) or **Top-to-Bottom** for hierarchical execution.
- **Edge Labels**: Every line connecting components must explicitly state:
  - **Protocol / Transport**: HTTPS, gRPC, SSH, Pub/Sub subscription.
  - **Authentication / Authorization**: OIDC token, Workload Identity Federation, Service Account impersonation, IAM role (`roles/viewer`).
  - **Data vs Control Flow**: Distinguish between control-plane commands (Terraform API calls) and data-plane traffic (ADK event streams).

---

## Agent Step-by-Step Procedure

When requested to build an architecture diagram or draft a design document containing architecture diagrams:

### Step 1: Analyze Architecture Components & Scope
Break down the architecture into:
- Clients & Ingress (e.g., User Browser, Cloudtop, GitHub Actions).
- IAM Identities & Auth mechanisms (e.g., WIF, OIDC, Service Accounts).
- Compute & Application layers (e.g., ADK Python, Cloud Run, Compute Engine).
- Networking & Perimeter boundaries (e.g., VPC, Subnets, Firewalls).
- Data, Storage & External Services (e.g., GCS, BigQuery, Vertex AI Model APIs).

### Step 2: Formulate the Dendrite Specification
Construct the declarative architecture model with defined nodes, groups/boundaries, and directional edges.

#### Example Dendrite Model Template (YAML):
```yaml
dendrite_diagram:
  title: "Argolis L200 CI/CD & ADK Agent Architecture"
  version: "1.0"
  dendrite_url: "http://go/dendrite"
  playground_url: "http://go/dendrite-playground"
  boundaries:
    - id: "github_cloud"
      label: "GitHub Environment"
      type: "external_service"
      components:
        - id: "gh_actions"
          label: "GitHub Actions Runner"
          type: "ci_cd"
          role: "Executes terraform-plan.yml & terraform-apply.yml"
    - id: "gcp_project"
      label: "GCP Project: argolis-sandbox"
      type: "cloud_project"
      components:
        - id: "wif_pool"
          label: "Workload Identity Federation"
          type: "iam_wif_provider"
          role: "Validates GitHub OIDC token"
        - id: "deployer_sa"
          label: "Deployer Service Account"
          type: "iam_service_account"
          role: "github-terraform-deployer SA"
        - id: "gcs_tfstate"
          label: "GCS Remote State Bucket"
          type: "cloud_storage"
          role: "Encrypted Terraform state store"
        - id: "compute_instance"
          label: "Argolis Compute Engine VM"
          type: "compute_engine"
          role: "Target compute instance"
  connections:
    - from: "gh_actions"
      to: "wif_pool"
      label: "OIDC Token Exchange (HTTPS)"
    - from: "wif_pool"
      to: "deployer_sa"
      label: "Assume SA Role (STS)"
    - from: "deployer_sa"
      to: "gcs_tfstate"
      label: "Read/Write State (TLS)"
    - from: "deployer_sa"
      to: "compute_instance"
      label: "Provision & Configure (GCP API)"
```

### Step 3: Embed Diagram in Design Deliverables
When generating or modifying design artifacts (e.g., `openspec/changes/<change-name>/design.md` or `README.md`):

1. **Reference Dendrite Directly**:
   Include a clear heading and callout linking to Dendrite and the playground viewer:
   ```markdown
   ### System Architecture Diagram
   > **Canonical Architecture Diagram**: Authored in **Dendrite** ([go/dendrite](http://go/dendrite))  
   > **Interactive Viewer**: [go/dendrite-playground](http://go/dendrite-playground)  
   ```

2. **Include Declarative Specification**:
   Embed the YAML/JSON Dendrite model so that any engineer or agent can import, inspect, or reconstruct the diagram in Dendrite.

3. **Provide Textual Walkthrough**:
   Document the flow of requests, security boundaries, and trust model step by step.

---

## Pre-Push Architecture Synchronization (`./docs/`)

The repository enforces an automated pre-tool-use hook (`git-push-architecture-docs-gate`) on `git push`. Prior to pushing changes to GitHub, agents **MUST** ensure that:

1. The `./docs/` folder exists and contains:
   - [`docs/architecture.md`](docs/architecture.md): System architecture narrative and Dendrite diagram.
   - [`docs/architecture_diagram.dendrite.yaml`](docs/architecture_diagram.dendrite.yaml): Declarative Dendrite architecture model.
2. The architecture diagram and documentation are updated to reflect all changes comprised in the git push action.
3. All `./docs/` updates are staged and committed (`git add docs/ && git commit -m "docs: update architecture diagram"`).

### How to Respond When Hook Triggers / Fails:
If `git push` is rejected by the hook:
1. Inspect the outgoing commit range:
   ```bash
   git diff @{u}..HEAD --stat
   ```
2. Update `docs/architecture_diagram.dendrite.yaml` with any new components, boundaries, or connections.
3. Refresh `docs/architecture.md` with the updated diagram and subsystem descriptions.
4. Stage and commit the documentation:
   ```bash
   git add docs/
   git commit -m "docs: update architecture diagram and documentation"
   ```
5. Retry `git push`.

---

## Reference Patterns

For reusable architecture blueprints and complete multi-tier models, refer to:
- [Dendrite Diagram Patterns & Blueprints](references/diagram_patterns.md): Includes ready-to-use patterns for **ADK Multi-Agent Architectures** and **Argolis Zero-Privilege Infrastructure & GitHub CI/CD**.
