# Gemini Enterprise Cloud Chat Agent & Argolis Infrastructure Architecture

This document serves as the authoritative architectural blueprint for the Google Academy L200, Argolis, and **Gemini Enterprise (GE) Cloud Chat Agent** workspace.

---

## Canonical Architecture Diagram

> **Authoritative Architecture Platform**: Google Internal **Dendrite** ([go/dendrite](http://go/dendrite))  
> **Interactive Diagram Viewer**: [go/dendrite-playground](http://go/dendrite-playground)  
> **Canonical DSL Model**: [`docs/architecture_diagram.dendrite`](architecture_diagram.dendrite)  
> **Declarative Model File**: [`docs/architecture_diagram.dendrite.yaml`](architecture_diagram.dendrite.yaml)  
> **Executive Standard**: Google Cloud Executive Reference Standard v3.3 (`BENTO-SANDWICH` 16:9 Matrix)  
> **Last Synchronized**: 2026-09-29

### 1. Dendrite Native DSL Model (`docs/architecture_diagram.dendrite`)

```dendrite
theme: "gcp-pro"
renderOrder: nodes-first
direction: down
spacing: 28

const GcpBlue = "#1a73e8"
const GcpGreen = "#1e8e3e"
const EmeraldTeal = "#0d9488"
const DarkSlate = "#202124"
const SubText = "#5f6368"
const CardBorder = "#dadce0"
const BusStroke = "#334155"
const SurfaceWhite = "#ffffff"
const DangerRed = "#d93025"

Style @Ghost {
  fill: transparent, strokeWidth: 0, fontColor: transparent, padding: 0
}
Style @ArchitectureRoot {
  fill: "#f8fafd", strokeColor: "#c2d7f5", strokeWidth: 1.5, borderRadius: 16,
  padding: 24, gap: 18, fontColor: "#3c4043", fontSize: 24, labelWeight: bold,
  icon: "GoogleCloud", iconSize: 28
}
Style @PerimeterZone {
  fill: "#e8f0fe", strokeColor: "#8ab4f8", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 14, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @ExecutionZone {
  fill: "#fce8e6", strokeColor: "#f6aea9", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 16, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @GovernanceZone {
  fill: "#e6f4ea", strokeColor: "#81c995", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 14, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @ResourceZone {
  fill: "#fef7e0", strokeColor: "#fde293", strokeWidth: 1.5, borderRadius: 12,
  padding: 16, gap: 16, fontColor: $DarkSlate, fontSize: 16, labelWeight: bold
}
Style @PeachSubGroup {
  fill: "#f8d3c8", strokeColor: darken("#f8d3c8", 12), strokeWidth: 1, borderRadius: 10,
  padding: 12, gap: 10, fontColor: $DarkSlate, fontSize: 13.5, labelWeight: bold
}
Style @GreenSubGroup {
  fill: "#ceead6", strokeColor: darken("#ceead6", 14), strokeWidth: 1, borderRadius: 10,
  padding: 10, gap: 8, fontColor: $DarkSlate, fontSize: 13.5, labelWeight: bold
}
Style @AmberSubGroup {
  fill: "#f9e4a7", strokeColor: darken("#f9e4a7", 14), strokeWidth: 1, borderRadius: 10,
  padding: 12, gap: 12, fontColor: $DarkSlate, fontSize: 13.5, labelWeight: bold
}
Style @ActorCard {
  width: 178, height: 56,
  fill: $SurfaceWhite, strokeColor: $CardBorder, strokeWidth: 1, borderRadius: 8,
  fontColor: $DarkSlate, subFontColor: $SubText,
  fontSize: 14, subFontSize: 11, labelWeight: bold,
  textAlign: "left", textVAlign: "middle",
  iconPosition: "left", iconSize: 28, padding: 12, shadow: true
}
Style @ProductCard {
  width: 164, height: 58,
  fill: $SurfaceWhite, strokeColor: $CardBorder, strokeWidth: 1, borderRadius: 8,
  fontColor: $DarkSlate, subFontColor: $SubText,
  fontSize: 13.5, subFontSize: 11, labelWeight: bold,
  textAlign: "left", textVAlign: "middle",
  iconPosition: "left", iconSize: 28, padding: 10, shadow: true
}
Style @GatewayHubCard {
  base: @ProductCard,
  width: 204, height: 68, strokeColor: $GcpBlue, strokeWidth: 2,
  fontSize: 15, subFontSize: 11.5, iconSize: 32, padding: 12
}
Style @BlockedCard {
  base: @ProductCard,
  strokeColor: $DangerRed, strokeWidth: 2,
  fill: "#fff8f7", fontColor: $DangerRed
}

Zone @L200EnterpriseArchitecture {
  title: "Google Cloud Platform"
  subtitle: "Gemini Enterprise Cloud Chat Agent & Argolis Infrastructure Architecture"
  style: @ArchitectureRoot
  layout: matrix
  areas: [
    "z1 z1 z1 z1 z1",
    "z2 z2 z3 z3 z3",
    "z4 z4 z4 z4 z4"
  ]
  sizes: ["1.05fr", "1.05fr", "0.96fr", "0.96fr", "0.96fr"]
  gap: 20

  Zone @Zone1_Perimeter {
    area: "z1"
    title: "1. Gemini Enterprise Frontend & Ingress"
    subtitle: "Client Ingress & IAP Security Perimeter"
    style: @PerimeterZone
    layout: row, gap: 18, align: center, justify: center

    [ge_frontend: "Gemini Enterprise\nWeb Frontend" | "Voice & Text UI"] {
      style: @ActorCard, width: 200, icon: "Laptop",
      description: "Interactive chat UI with Web Speech microphone input, real-time response rendering, and TTS audio playback"
    }
    [iap_gateway: "Identity-Aware\nProxy (IAP)" | "Google Auth Perimeter"] {
      style: @ProductCard, width: 188, icon: "GoogleIdentity",
      description: "Cryptographic JWT signature verification, audience validation, and caller authorization enforcement"
    }
    [cloudtop_shell: "Developer Shell\n& Toolchain" | "Local Environment"] {
      style: @ProductCard, width: 180, icon: "GcpDeveloperTools",
      description: "Hermetic standalone toolchain including Terraform v1.16.4, gcloud CLI, uv, and pre-push hooks"
    }
  }

  Zone @Zone2_AgentEngine {
    area: "z2"
    title: "2. Gemini 3.8 Agent Engine"
    subtitle: "Conversational Coordinator, TTS & Guardrails"
    style: @ExecutionZone
    layout: column, gap: 14, align: center

    [cloud_chat_agent: "Gemini Enterprise\nCloud Chat Agent" | "Gemini 3.8 Flash / Pro"] {
      style: @GatewayHubCard, icon: "Gemini",
      description: "Single conversational coordinator with strategic model routing, history compaction, and persistent memory"
    }

    Zone @AgentServicesSubMesh {
      title: "Agent Capabilities & Security Guardrails"
      style: @PeachSubGroup
      layout: matrix, cols: 2, gap: 10, align: center, justify: center

      [cloud_tts_engine: "Google Cloud TTS\nVoice Engine" | "Journey / Neural2"] {
        style: @ProductCard, width: 160, icon: "Audio",
        description: "Converts conversational answers into natural neural speech audio with automatic markdown cleaning"
      }
      [db_quarantine_barrier: "Database Access\nBlocker Guardrail" | "Strict Security Boundary"] {
        style: @BlockedCard, width: 160, icon: "ShieldAlert",
        description: "Strictly forbids direct queries to internal application databases (Cloud SQL, Spanner, Firestore)"
      }
      [readonly_cloud_prober: "Read-Only Cloud\nInspection Tools" | "Zero Mutation"] {
        style: @ProductCard, width: 160, icon: "ShieldCheck",
        description: "Schema-validated read-only inspection for Compute VMs, Cloud Run services, Storage buckets, and IAM"
      }
      [cloud_logging_prober: "Cloud Logging\nInspection Tool" | "Diagnostic Logs"] {
        style: @ProductCard, width: 160, icon: "GcpLogging",
        description: "Queries Cloud Logging system for application error logs, audit events, and crash traces"
      }
    }
  }

  Zone @Zone3_CicdAndIam {
    area: "z3"
    title: "3. GitHub CI/CD & Security"
    subtitle: "Keyless WIF & Automated Evaluation"
    style: @GovernanceZone
    layout: row, gap: 18, align: center, justify: center

    Zone @GithubPlatformSubZone {
      title: "GitHub Actions CI/CD"
      style: @GreenSubGroup
      layout: column, gap: 10, align: center

      [github_repo: "GitHub Repository\nBranch Protection" | "L200 Mainline"] {
        style: @ProductCard, width: 220, icon: "Github",
        description: "Source of truth repository with branch protection, PR context embedding, and pre-push gates"
      }

      Zone @PipelinesRow {
        style: @Ghost, layout: row, gap: 8, align: center

        [agent_eval_pipeline: "Golden Eval\npytest Suite" | "7/7 Cases Passing"] {
          style: @ProductCard, width: 140, icon: "Code",
          description: "Automated 26-test pytest suite and 7-scenario Golden Evaluation Dataset measuring guardrails"
        }
        [gha_plan: "Terraform Plan\nPR Validation" | "CI Pipeline"] {
          style: @ProductCard, width: 140, icon: "GitMerge",
          description: "Automated terraform init, validate, and plan on PRs targeting main"
        }
      }
    }

    Zone @IamSecuritySubZone {
      title: "Google Cloud IAM & WIF"
      style: @GreenSubGroup
      layout: column, gap: 10, align: center

      [wif_pool: "Workload Identity\nPool & Provider" | "GitHub OIDC JWT"] {
        style: @ProductCard, width: 176, icon: "GoogleIdentity",
        description: "Exchanges GitHub Actions OIDC JWT tokens for federated GCP STS credentials without keys"
      }
      [reader_sa: "Read-Only SA\nViewer & Logging" | "Impersonated SA"] {
        style: @ProductCard, width: 176, icon: "Key",
        description: "cloudtop-agent-reader service account strictly restricted to Viewer and Logging Viewer roles"
      }
    }
  }

  Zone @Zone4_ArgolisInfrastructure {
    area: "z4"
    title: "4. Argolis GCP Project Infrastructure"
    subtitle: "Cloud Run API, Logging Systems & Isolated Databases"
    style: @ResourceZone
    layout: matrix, cols: 3, sizes: ["1.1fr", "0.9fr", "1.3fr"], gap: 18, align: center

    Zone @ServerlessVaultSubZone {
      title: "Serverless Compute & Secret Vault"
      style: @AmberSubGroup
      layout: row, gap: 12, align: center, justify: center

      [cloud_run_factory_service: "Cloud Run Service\nIAP Protected" | "FastAPI Server"] {
        style: @ProductCard, width: 182, icon: "GcpCloudRun",
        description: "Hosts the GE Web Frontend and conversational API protected by Identity-Aware Proxy"
      }
      [secret_manager_vault: "Secret Manager\n& Cloud DLP Vault" | "PII Redaction"] {
        style: @ProductCard, width: 176, icon: "SecretManager",
        description: "Zero hardcoded credentials with automated Cloud DLP PII redaction across logs and memory"
      }
    }

    Zone @LoggingSubZone {
      title: "Cloud Logging Systems (Permitted)"
      style: @AmberSubGroup
      layout: row, align: center, justify: center

      [cloud_logging: "Cloud Logging API\nSystem & Audit Logs" | "Permitted Telemetry"] {
        style: @ProductCard, width: 178, icon: "GcpLogging",
        description: "Authorized telemetry and error log stream queried by the read-only agent for diagnostics"
      }
    }

    Zone @QuarantinedDatabasesSubZone {
      title: "Internal Databases (Strictly Quarantined)"
      style: @AmberSubGroup
      layout: row, gap: 10, align: center, justify: center

      [internal_databases: "Internal Databases\nCloud SQL / Spanner" | "Direct Query Prohibited"] {
        style: @BlockedCard, width: 210, icon: "DatabaseLock",
        description: "Customer tables and application databases strictly isolated from direct agent querying"
      }
    }
  }
}
```

### 2. Declarative Model Specification (`docs/architecture_diagram.dendrite.yaml`)

```yaml
dendrite_diagram:
  title: "Gemini Enterprise Cloud Chat Agent & Argolis Infrastructure Architecture"
  version: "3.3.0"
  standard: "Executive Standard v3.3"
  archetype: "BENTO-SANDWICH"
  dendrite_url: "http://go/dendrite"
  playground_url: "http://go/dendrite-playground"
  last_updated: "2026-09-29"
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
