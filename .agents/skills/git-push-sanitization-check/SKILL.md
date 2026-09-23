---
name: git-push-sanitization-check
description: >-
  Sanitizes and validates repository changes prior to git push.
  Checks for sensitive credentials, uncommitted secrets, lint issues, or forbidden artifacts.
---

# git-push-sanitization-check Subagent
 
This subagent is automatically triggered prior to running `git push`.
It reviews outgoing changes to ensure all code and repository states are sanitized before pushing to remote.

## Instructions

Configure your sanitization rules and checks below:

1. **Check Outgoing Commits and Diffs**:
   - Inspect unpushed commits:
     ```bash
     git log @{u}..HEAD --oneline
     ```
   - Inspect diff of unpushed commits:
     ```bash
     git diff @{u}..HEAD
     ```

2. **Verify No Credentials, Secrets, or Sensitive Files**:
   - **Cookies**: Check for hardcoded cookie strings, session IDs (`sessionid=`, `connect.sid=`, `remember_token=`), and `Cookie:` / `Set-Cookie:` headers.
   - **JWTs**: Check for JSON Web Tokens (`eyJ...`), auth headers, or hardcoded session tokens.
   - **API Keys & Tokens**: Check for provider-specific API keys (Google `AIza...`, GitHub `ghp_...`, OpenAI `sk-...`, Anthropic `sk-ant-...`, AWS `AKIA...`, Stripe, Slack, HuggingFace) and generic `api_key = "..."`, `secret_key = "..."`, `Bearer <token>`.
   - **Sensitive Files**: Check for sensitive or untracked configuration files (e.g. `.env`, `.env.local`, service account keys, `.pem` files, private keys, `credentials.json`, `cookies.txt`).
   - Ensure `.gitignore` properly excludes local credentials and configuration files.

3. **Validation Outcome**:
   - If **all checks pass**:
     - Conclude with a clear confirmation: `SANITIZATION_CHECK: PASSED`.
   - If **issues are detected**:
     - State clearly what issue was found: `SANITIZATION_CHECK: FAILED: <details of issue>`.
     - Detail the corrective actions needed (e.g. `git reset`, untracking sensitive files, or removing hardcoded secrets).
