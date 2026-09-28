# Dendrite Diagram Patterns & Blueprints

This reference guide provides standardized architecture patterns to use when designing diagrams in Dendrite (`go/dendrite`) for Google Cloud and Google Agent ecosystems.

---

## Pattern 1: Google Agent Development Kit (ADK) Multi-Tier Agent

Use this pattern when modeling AI agents built with ADK, Vertex AI, and external tool integrations.

### Architecture Topology
1. **Client / User Interface**: Web application, chat client, or API consumer.
2. **Agent Runtime**:
   - Coordinator / Parent Agent (e.g. Gemini 1.5 Pro / Flash).
   - Specialized Subagents (e.g. Research, Code Generator, Evaluator).
3. **Tool & Service Integration Tier**:
   - MCP Servers (Model Context Protocol endpoints).
   - Custom Python Tools & APIs.
4. **Context & Persistence Tier**:
   - Short-term session memory / Turn buffer.
   - Long-term Memory Bank / Vertex AI Vector Search / Firestore.
5. **Observability & Guardrails**:
   - Cloud Logging & Cloud Trace (OpenTelemetry).
   - Model Armor / Security Policy Filters.

### Dendrite Model Specification (YAML)
```yaml
dendrite_diagram:
  title: "ADK Multi-Agent Architecture"
  version: "1.0"
  dendrite_url: "http://go/dendrite"
  playground_url: "http://go/dendrite-playground"
  boundaries:
    - id: "client_tier"
      label: "User & Ingress Tier"
      type: "client"
      components:
        - id: "web_ui"
          label: "Web / CLI Client"
          type: "user_interface"
    - id: "agent_runtime"
      label: "Agent Execution Environment (Cloud Run / Vertex AI)"
      type: "compute_cluster"
      components:
        - id: "coordinator_agent"
          label: "Coordinator Agent (ADK)"
          type: "llm_agent"
          role: "Task orchestration & model routing"
        - id: "subagent_pool"
          label: "Specialized Subagents"
          type: "subagents"
          role: "Execution of isolated subtasks"
        - id: "guardrails"
          label: "Guardrails & Model Armor"
          type: "security_filter"
          role: "Input/output sanitization and policy enforcement"
    - id: "external_services"
      label: "Services & Data Tier"
      type: "persistence"
      components:
        - id: "gemini_model_api"
          label: "Gemini Model Endpoints (Vertex AI)"
          type: "foundation_model"
        - id: "mcp_servers"
          label: "MCP Tool Servers"
          type: "tool_provider"
        - id: "vector_db"
          label: "Vertex AI Vector Search / Firestore"
          type: "database"
          role: "Long-term episodic memory"
  connections:
    - from: "web_ui"
      to: "coordinator_agent"
      label: "User Prompt (REST / WebSocket)"
    - from: "coordinator_agent"
      to: "guardrails"
      label: "Filter Request (Sync)"
    - from: "guardrails"
      to: "gemini_model_api"
      label: "Model Inference (HTTPS)"
    - from: "coordinator_agent"
      to: "subagent_pool"
      label: "Delegate Tasks (Async Event)"
    - from: "coordinator_agent"
      to: "mcp_servers"
      label: "Tool Execution (JSON-RPC / SSE)"
    - from: "coordinator_agent"
      to: "vector_db"
      label: "Session Context & Memory RAG"
```

---

## Pattern 2: Argolis Zero-Privilege Infrastructure & GitHub CI/CD

Use this pattern when modeling Terraform provisioning, Workload Identity Federation (WIF), and Argolis GCP environments.

### Architecture Topology
1. **GitHub Repository**: Pull requests, actions workflows (`terraform-plan.yml`, `terraform-apply.yml`).
2. **Workload Identity Federation**: OIDC token exchange without static credentials.
3. **Target GCP Project (Argolis)**:
   - IAM Boundary & Deployment Service Account.
   - Remote State Storage (`tfstate` GCS bucket).
   - Network Boundary (VPC, Subnet, Firewall rules).
   - Target Compute Engine instances.

### Dendrite Model Specification (YAML)
```yaml
dendrite_diagram:
  title: "Argolis Zero-Privilege Deployment Topology"
  version: "1.0"
  dendrite_url: "http://go/dendrite"
  playground_url: "http://go/dendrite-playground"
  boundaries:
    - id: "github"
      label: "GitHub Enterprise / Cloud"
      type: "external"
      components:
        - id: "developer"
          label: "Engineer / Agent"
          type: "actor"
        - id: "git_repo"
          label: "GitHub Repository (L200)"
          type: "vcs"
        - id: "actions_runner"
          label: "GitHub Actions Runner"
          type: "ci_cd"
    - id: "gcp_iam"
      label: "Google Cloud IAM & Security"
      type: "iam_boundary"
      components:
        - id: "wif_pool"
          label: "Workload Identity Pool & Provider"
          type: "wif"
        - id: "deployer_sa"
          label: "Deployer Service Account"
          type: "service_account"
          role: "Scoped IAM roles (Compute Admin, Storage Admin)"
    - id: "argolis_project"
      label: "Argolis Project (Target Sandbox)"
      type: "gcp_project"
      components:
        - id: "gcs_state"
          label: "Terraform State Bucket"
          type: "gcs"
        - id: "vpc_network"
          label: "VPC Network & Subnet"
          type: "networking"
        - id: "vm_instance"
          label: "Compute Engine VM"
          type: "compute_engine"
  connections:
    - from: "developer"
      to: "git_repo"
      label: "git push / PR merge"
    - from: "git_repo"
      to: "actions_runner"
      label: "Trigger Workflow"
    - from: "actions_runner"
      to: "wif_pool"
      label: "Exchange GitHub OIDC JWT (HTTPS)"
    - from: "wif_pool"
      to: "deployer_sa"
      label: "Generate Ephemeral Google Access Token"
    - from: "actions_runner"
      to: "gcs_state"
      label: "Acquire State Lock & Sync (TLS)"
    - from: "actions_runner"
      to: "vpc_network"
      label: "Apply Network & Firewall Rules"
    - from: "actions_runner"
      to: "vm_instance"
      label: "Provision / Update VM"
```
