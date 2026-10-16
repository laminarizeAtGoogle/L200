# Gemini Enterprise Cloud Chat Agent & Argolis Infrastructure Architecture

This document serves as the authoritative architectural blueprint for the Google Academy L200, Argolis, and **Gemini Enterprise (GE) Cloud Chat Agent** workspace.

---

## Canonical Architecture Diagram

> **Authoritative Architecture Platform**: **Mermaid** (`mermaid` diagram standard)  
> **Standalone Diagram Source**: [`docs/architecture_diagram.mmd`](architecture_diagram.mmd)  
> **Last Synchronized**: 2026-10-16

### System Architecture Topology

```mermaid
---
config:
  layout: elk
  look: neo
  theme: default
themeVariables:
  fontFamily: 'Roboto, Google Sans, Helvetica, Arial, sans-serif'
  primaryColor: '#4285F4'
  secondaryColor: '#34A853'
  tertiaryColor: '#FBBC04'
  mainBkg: '#FFFFFF'
  nodeBorder: '#4285F4'
  clusterBkg: '#F8F9FA'
  clusterBorder: '#DADCE0'
  lineColor: '#5F6368'
  edgeLabelBackground: '#ffffff'
---
flowchart TD
    %% Architecture Diagram: Gemini Enterprise Cloud Chat Agent & Argolis Infrastructure

    subgraph Zone1 ["1. Gemini Enterprise Frontend & Ingress (Perimeter Zone)"]
        direction LR
        cloudtop_shell["`**Developer Shell & Workstation**<br>• Hermetic Toolchain & .agents/ Plugin<br>• 25 Core Skills + 13 /fde-* Workflows`"]
        cloudtop_shell@{ icon: "logos:terminal" }
        wpUI_dst((("🌐<br>UI<br>Host"))):::wp_blue
        ge_frontend["`**Gemini Enterprise Web UI**<br>• Voice Recording & TTS Playback<br>• Markdown Chat Feed & Badges`"]:::gcpBlue
        iap_gateway["`**Google Identity-Aware Proxy (IAP)**<br>• Cryptographic JWT Assertion<br>• Google Login Perimeter`"]:::gcpYellow
        iap_gateway@{ icon: "gcp:identity-aware-proxy" }
        wpJWT_src((("🛡️<br>IAP<br>JWT"))):::wp_blue
    end

    subgraph Zone2 ["2. Gemini 3.8 Agent Engine & Security Boundaries (Execution Zone)"]
        direction TB
        wpJWT_dst((("🛡️<br>IAP<br>JWT"))):::wp_blue
        cloud_chat_agent["`**Gemini Enterprise Cloud Chat Agent**<br>• Conversational Coordinator<br>• Strategic Model Routing (Flash / Pro)<br>• Context Compaction & Episodic Memory`"]:::gcpBlue
        cloud_chat_agent@{ icon: "gcp:vertexai" }

        subgraph AgentServices ["Agent Capabilities & Guardrails"]
            direction LR
            cloud_tts_engine["`**Google Cloud TTS Voice Engine**<br>• Journey & Neural2 Voices<br>• Markdown Speech Cleaning`"]:::gcpBlue
            cloud_tts_engine@{ icon: "gcp:speech-to-text" }
            db_quarantine_barrier["`**Database Access Blocker Guardrail**<br>• Strictly Blocks SQL/Spanner/Firestore<br>• Directs Diagnostics to Cloud Logging`"]:::gcpRed
            readonly_cloud_prober["`**Read-Only Cloud Prober**<br>• Zero Mutating Verbs<br>• Probes VMs, Run, Storage, IAM`"]:::gcpBlue
            cloud_logging_prober["`**Cloud Logging Prober**<br>• Authorized Telemetry Queries<br>• Audit Trails & Error Traces`"]:::gcpBlue
            cloud_logging_prober@{ icon: "gcp:cloud-logging" }
        end

        wpBlock_src((("⛔<br>DB<br>Wall"))):::wp_red
        wpIAM_src((("🔑<br>SA<br>Auth"))):::wp_yellow
        wpLog_src((("📋<br>Log<br>Sink"))):::wp_green
    end

    subgraph Zone3 ["3. GitHub CI/CD & Security Boundary (Governance Zone)"]
        direction LR
        subgraph GithubPlatform ["GitHub Actions Platform"]
            direction TB
            github_repo["`**GitHub Repository (L200 Mainline)**<br>• Branch Protection & Policy<br>• Embedded PR Context & History`"]
            github_repo@{ icon: "logos:github" }
            gha_plan["`**Terraform Plan Pipeline**<br>• Automated PR Validation`"]
            gha_plan@{ icon: "logos:terraform" }
            agent_eval_pipeline["`**Golden Eval pytest Suite**<br>• 26 Automated Tests<br>• 7/7 Golden Dataset Pass Rate`"]:::gcpGreen
            agent_eval_pipeline@{ icon: "fa:circle-check" }
            wpOIDC_src((("🔐<br>OIDC<br>STS"))):::wp_yellow
        end
        subgraph IamSecurity ["Google Cloud IAM & Workload Identity"]
            direction TB
            wpOIDC_dst((("🔐<br>OIDC<br>STS"))):::wp_yellow
            wif_pool["`**Workload Identity Pool & Provider**<br>• Keyless OIDC STS Token Exchange`"]:::gcpYellow
            wif_pool@{ icon: "gcp:identity-and-access-management" }
            wpIAM_dst((("🔑<br>SA<br>Auth"))):::wp_yellow
            reader_sa["`**cloudtop-agent-reader SA**<br>• Restricted Viewer & Logging Viewer`"]:::gcpYellow
            reader_sa@{ icon: "gcp:identity-and-access-management" }
            wpInfra_src((("☁️<br>GCP<br>Read"))):::wp_green
        end
    end

    subgraph Zone4 ["4. Google Cloud Argolis Infrastructure (Resource Zone)"]
        direction LR
        subgraph ServerlessVault ["Serverless Compute & Secret Vault"]
            direction TB
            cloud_run_factory_service["`**Cloud Run Service**<br>• Containerized FastAPI Server<br>• Hosts Frontend Behind IAP`"]:::gcpBlue
            cloud_run_factory_service@{ icon: "gcp:cloud-run" }
            secret_manager_vault["`**Secret Manager & Cloud DLP Vault**<br>• Zero Hardcoded Credentials<br>• Automated PII Scrubbing`"]:::gcpGreen
            secret_manager_vault@{ icon: "gcp:secret-manager" }
            wpUI_src((("🌐<br>UI<br>Host"))):::wp_blue
        end
        subgraph LoggingZone ["Cloud Logging Systems"]
            direction TB
            wpLog_dst((("📋<br>Log<br>Sink"))):::wp_green
            cloud_logging["`**Cloud Logging API**<br>• Authorized Diagnostic Telemetry<br>• System & Application Logs`"]:::gcpGreen
            cloud_logging@{ icon: "gcp:cloud-logging" }
        end
        subgraph ComputeZone ["Compute Resources"]
            direction TB
            wpInfra_dst((("☁️<br>GCP<br>Read"))):::wp_green
            compute_vm["`**Compute Engine & Cloud Run Workloads**<br>• Monitored Infrastructure Assets`"]:::gcpBlue
            compute_vm@{ icon: "gcp:compute-engine" }
        end
        subgraph QuarantinedDBs ["Strictly Quarantined Tier"]
            direction TB
            wpBlock_dst((("⛔<br>DB<br>Wall"))):::wp_red
            internal_databases[("`**Internal Application Databases**<br>• Cloud SQL, Spanner, Firestore<br>⛔ DIRECT AGENT QUERY PROHIBITED`")]:::gcpRed
            internal_databases@{ icon: "gcp:cloud-sql" }
        end
    end

    %% Balanced 2x2 Multi-Row Ordering (Zone1+Zone3 on Row 1, Zone2+Zone4 on Row 2)
    Zone1 ~~~ Zone2
    Zone3 ~~~ Zone4

    %% Client Ingress Flow (Zone 1)
    wpUI_dst -.->|Serves Static UI| ge_frontend
    ge_frontend -->|HTTPS / Google Login| iap_gateway
    iap_gateway ==>|Verified JWT Assertion| wpJWT_src

    %% Agent Internal Routing (Zone 2)
    wpJWT_dst ==> cloud_chat_agent
    cloud_chat_agent -->|gRPC / Runtime SA Token| cloud_tts_engine
    cloud_chat_agent -->|Inspection Dispatch| readonly_cloud_prober
    cloud_chat_agent -->|Log Inspection Request| cloud_logging_prober
    cloud_chat_agent -->|Enforce Policy Hook| db_quarantine_barrier

    %% Teleporter Waypoint Exits from Zone 2 (Zero Inter-Waypoint Edges)
    db_quarantine_barrier -.-x|ACCESS DENIED| wpBlock_src
    readonly_cloud_prober -->|IAM SA Impersonation| wpIAM_src
    cloud_logging_prober -->|Read Error Logs| wpLog_src

    %% CI/CD & Governance Flow (Zone 3)
    github_repo -->|Trigger on Push/PR| agent_eval_pipeline
    github_repo -->|Trigger on PR| gha_plan
    agent_eval_pipeline -->|GitHub OIDC Token| wpOIDC_src
    wpOIDC_dst ==> wif_pool
    wif_pool -->|Federated STS Credential| reader_sa
    wpIAM_dst ==> reader_sa
    reader_sa -->|GCP Viewer & Logging APIs| wpInfra_src

    %% Argolis Resource Zone Flow (Zone 4)
    cloud_run_factory_service -->|Secret Accessor| secret_manager_vault
    cloud_run_factory_service -.-> wpUI_src
    wpLog_dst ==> cloud_logging
    wpInfra_dst ==> compute_vm
    wpBlock_dst -.-x internal_databases

    %% Google Cloud Contrast Palette Classes
    classDef gcpBlue fill:#E8F0FE,stroke:#1967D2,stroke-width:2px,color:#000,font-family:Roboto;
    classDef gcpGreen fill:#E6F4EA,stroke:#1E8E3E,stroke-width:2px,color:#000,font-family:Roboto;
    classDef gcpYellow fill:#FEF7E0,stroke:#B06000,stroke-width:2px,color:#000,font-family:Roboto;
    classDef gcpRed fill:#FCE8E6,stroke:#D93025,stroke-width:2px,color:#000,font-family:Roboto;
    classDef neutral fill:#F1F3F4,stroke:#5F6368,stroke-width:2px,color:#000,font-family:Roboto;

    %% Teleporter Waypoint Classes
    classDef wp_blue fill:#1A73E8,stroke:#0D47A1,stroke-width:2px,color:#fff,font-weight:bold;
    classDef wp_green fill:#34A853,stroke:#1B5E20,stroke-width:2px,color:#fff,font-weight:bold;
    classDef wp_yellow fill:#FBBC04,stroke:#F29900,stroke-width:2px,color:#000,font-weight:bold;
    classDef wp_red fill:#EA4335,stroke:#C5221F,stroke-width:2px,color:#fff,font-weight:bold;

    %% Explicit Subgraph Styles (Zero Default Yellow Subgraphs)
    style Zone1 fill:#e8f0fe,stroke:#1967D2,stroke-width:2px
    style Zone2 fill:#e8f0fe,stroke:#1967D2,stroke-width:2px
    style AgentServices fill:#ffffff,stroke:#1967D2,stroke-width:2px
    style Zone3 fill:#e6f4ea,stroke:#1E8E3E,stroke-width:2px
    style GithubPlatform fill:#ffffff,stroke:#1E8E3E,stroke-width:2px
    style IamSecurity fill:#ffffff,stroke:#B06000,stroke-width:2px
    style Zone4 fill:#f9f9f9,stroke:#DADCE0,stroke-width:2px
    style ServerlessVault fill:#e8f0fe,stroke:#1967D2,stroke-width:2px
    style LoggingZone fill:#e6f4ea,stroke:#1E8E3E,stroke-width:2px
    style ComputeZone fill:#e8f0fe,stroke:#1967D2,stroke-width:2px
    style QuarantinedDBs fill:#fce8e6,stroke:#D93025,stroke-dasharray:5 5,stroke-width:2px
```

---

## Architectural Breakdown & Core Subsystems

### 1. Ingress & Client Presentation (Zone 1)
- **Gemini Enterprise Web Frontend** ([`ge-cloud-chat-frontend.md`](knowledge_base/codebase/ge-cloud-chat-frontend.md)):
  - Built with clean Material Design 3 tokens and Google Sans styling.
  - Supports speech input via browser Web Speech API (`SpeechRecognition`).
  - Spoken audio response playback via integrated HTML5 Web Audio controls and auto-play toggle.
  - Live status badges reflecting Gemini 3.8 Flash, verified IAP identity, and active database quarantine.
- **Identity-Aware Proxy (IAP) Gateway** ([`iap-verifier.md`](knowledge_base/codebase/iap-verifier.md)):
  - Cryptographically validates `X-Goog-IAP-JWT-Assertion` and `X-Goog-Authenticated-User-Email`.
  - Enforces role-based caller authorization before forwarding requests to the conversational agent.

### 2. Conversational Agent Engine & Security Boundaries (Zone 2)
- **Gemini Enterprise Cloud Chat Agent** ([`a2a-software-factory-api.md`](knowledge_base/codebase/a2a-software-factory-api.md)):
  - Single conversational coordinator running Gemini 3.8 Flash for fast telemetry and Gemini 3.8 Pro for deep architectural synthesis.
  - Maintains persistent episodic memory and dynamic context compaction across multi-turn sessions.
- **Google Cloud Text-to-Speech (TTS)** ([`cloud-tts-service.md`](knowledge_base/codebase/cloud-tts-service.md)):
  - Synthesizes Journey and Neural2 voices with automatic markdown-to-speech cleaning.
- **Strict Database Access Restriction Guardrail** ([`database-access-blocker-guardrail.md`](knowledge_base/codebase/database-access-blocker-guardrail.md)):
  - Intercepts and denies direct SQL/Spanner/Firestore queries while directing diagnostic workflows to Cloud Logging.
- **Read-Only Cloud Inspection Tools**:
  - Zero mutating verbs; inspects Compute Engine VMs, Cloud Run services, Storage bucket metadata, IAM roles, and Cloud Logging entries.

### 3. Google Cloud Argolis Infrastructure & Observability (Zone 4)
- **Cloud Run Service**: Containerized FastAPI service deployed behind Identity-Aware Proxy.
- **Cloud Logging Systems**: Permitted diagnostic log stream providing error traces and audit trails.
- **Secret Manager & Cloud DLP Vault**: Zero hardcoded credentials with automated PII scrubbing.
- **Internal Databases (Quarantined)**: Application databases (Cloud SQL, Spanner, Firestore) strictly isolated from agent query access.
- **IAM Permission Boundary Governance**: Project-level IAM member bindings are gated behind `manage_project_iam` (default: `false`) ensuring keyless WIF deployment pipelines operating under `roles/editor` apply infrastructure without encountering 403 `setIamPolicy` denials.
- **Declarative State Import & GCS Backend**: Declarative `import {}` blocks ([`terraform/imports.tf`](../terraform/imports.tf)) adopt pre-existing Argolis cloud resources into the remote GCS state backend (`l200-509515-tfstate`), eliminating 409 conflict errors across ephemeral GitHub Actions CI/CD runners.

---

## Operational Knowledge Framework (OKF) Catalog

Every architectural component is documented in [`docs/knowledge_base/`](knowledge_base/):
- **Web Frontend**: [`docs/knowledge_base/codebase/ge-cloud-chat-frontend.md`](knowledge_base/codebase/ge-cloud-chat-frontend.md)
- **IAP Verifier**: [`docs/knowledge_base/codebase/iap-verifier.md`](knowledge_base/codebase/iap-verifier.md)
- **Cloud TTS Service**: [`docs/knowledge_base/codebase/cloud-tts-service.md`](knowledge_base/codebase/cloud-tts-service.md)
- **Database Guardrail**: [`docs/knowledge_base/codebase/database-access-blocker-guardrail.md`](knowledge_base/codebase/database-access-blocker-guardrail.md)
- **Pre-Push Credential & OSPO Sanitization Gate**: [`docs/knowledge_base/cloudtop_env/scripts/pre-command-hook.md`](knowledge_base/cloudtop_env/scripts/pre-command-hook.md)
- **Argolis WIF & Terraform State Setup Script (`~/workspace/setupScripts/`)**: [`docs/knowledge_base/cloudtop_env/scripts/setup-argolis-github-wif.md`](knowledge_base/cloudtop_env/scripts/setup-argolis-github-wif.md)
- **Argolis Zero-Privilege IAM Provisioning Script (`~/workspace/setupScripts/`)**: [`docs/knowledge_base/cloudtop_env/scripts/provision-argolis-env.md`](knowledge_base/cloudtop_env/scripts/provision-argolis-env.md)
- **FDE & Official ADK-Python Skills Catalog**: [`docs/knowledge_base/cloudtop_env/skills/fde-and-adk-skills-suite.md`](knowledge_base/cloudtop_env/skills/fde-and-adk-skills-suite.md)
