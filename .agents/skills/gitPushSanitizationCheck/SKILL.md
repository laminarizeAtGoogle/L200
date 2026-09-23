---
name: gitPushSanitizationCheck
description: >-
  Sanitizes and validates repository changes prior to git push.
  Checks for sensitive credentials, uncommitted secrets, lint issues, or forbidden artifacts.
---

# gitPushSanitizationCheck Subagent

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

2. **Verify No Secrets or Sensitive Files**:
   - Check for sensitive files (e.g. `.env`, service account keys, `.pem` files, API keys).
   - Ensure `.gitignore` properly excludes local configuration files.

3. **Validation Outcome**:
   - If **all checks pass**:
     - Conclude with a clear confirmation: `SANITIZATION_CHECK: PASSED`.
   - If **issues are detected**:
     - State clearly what issue was found: `SANITIZATION_CHECK: FAILED: <details of issue>`.
     - Detail the corrective actions needed (e.g. `git reset`, untracking sensitive files, or removing hardcoded secrets).
