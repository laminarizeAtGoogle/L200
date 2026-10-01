---
okf_version: "1.0"
component_id: "pre-command-hook"
name: "Pre-Push Credential & OSPO Sanitization Gate"
category: "cloudtop_env"
subcategory: "scripts"
status: "active"
owner: "cloudtop-admin"
last_updated: "2026-10-01"
tags:
  - "git-hook"
  - "security"
  - "sanitization"
  - "pre-tool-use"
  - "ospo"
  - "okf"
---

# Pre-Push Credential & OSPO Sanitization Gate (`pre-command-hook.sh`)

## 1. Overview & Purpose
This deterministic `PreToolUse` hook intercepts `git push` commands (including git alias expansions) and scans tracked files, staged files, and outgoing commit diffs (`@{u}..HEAD`) for leaked credentials, tokens, service account keys, sensitive filenames, and internal Google identifiers prior to invoking `/git-push-sanitization-check`.

## 2. Technical Specification
- **Script Location**: `.agents/scripts/pre-command-hook.sh` & `.agents/scripts/pre_command_hook.py`
- **Execution Hook**: `PreToolUse` on `run_command` in `.agents/hooks.json` (`git-push-sanitization-gate`)
- **Configuration**: `.agents/scripts/pre-command-config.json`
- **Subagent Command**: `/git-push-sanitization-check` (`.agents/skills/git-push-sanitization-check/SKILL.md`)

## 3. Sensitive Information Categories
Incorporates sensitive content patterns from `cloud-ai-fde/agent-driven-dev` PR #23 (`fde-cross-compliance`) alongside existing credential checks:
1. **`cookies`**: `Cookie` / `Set-Cookie` headers, session IDs (`connect.sid`, `sessionid`, `jsessionid`, `remember_token`), and cookie variables.
2. **`jwt`**: JSON Web Tokens (`eyJ...`) and JWT variable assignments.
3. **`api_keys`**: Google API keys (`AIza...`), GitHub PATs (`ghp_...`, `github_pat_...`), OpenAI (`sk-...`), Anthropic (`sk-ant-...`), expanded AWS IAM access keys (`A3T...`, `AKIA...`, `ABIA...`, `ACCA...`, `AGPA...`, `AIDA...`, `AROA...`, `AIPA...`, `ANPA...`, `ANVA...`, `ASIA...`), AWS secret keys, Slack, Stripe, SendGrid, HuggingFace, Private Key PEM blocks (`RSA`, `EC`, `OPENSSH`, `DSA`, `PGP`), generic secrets, and `Bearer` tokens.
4. **`oauth_tokens`**: Google OAuth 2.0 access tokens (`ya29...`).
5. **`service_accounts`**: GCP Service Account JSON key payloads (`"type"` service account markers and `"private_key_id"` fields).
6. **`internal_google`**: Unredacted internal Google shortlinks (`go/...`, `b/...`, `cl/...`, `yaqs/...`), internal depot/Piper paths (`//depot/...`), internal corporate hostnames, and internal documentation paths.
7. **Sensitive Filenames**: `.env*`, `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `credentials.json`, `client_secret*.json`, `*service_account*.json`, `cookies.txt`, `skill-runs.jsonl`.

## 4. Verification & Testing
- Unit and integration test suite: `.agents/scripts/test_pre_command_hook.py` (16 passing tests).
