---
name: fde-init-setup
description: Initialize a new SDD project workspace with standard directory layout, AGENTS.md rules, and ADK boilerplate.
---

# Project Initialization Skill (`fde-init-setup`)

This skill guides setup of a new project workspace based on Spec-Driven Development (SDD) standards.

## Process

1. **Ask User Choice**:
   - Ask: "Would you like to initialize with standard SDD foundation (directories and rule files), or include full ADK/Agent structure (agent boilerplate and dependencies)?"

2. **Execute Choice**:

### Path A: Standard SDD Foundation
```bash
# 1. Initialize uv
[ -f "pyproject.toml" ] || uv init

# 2. Create directories
mkdir -p scripts .agents/skills

# 3. Seed AGENTS.md rules
[ -f "AGENTS.md" ] || cp "$HOME/.gemini/AGENTS.md" "AGENTS.md" 2>/dev/null || echo "# AGENTS.md Placeholder" > AGENTS.md

# 4. Create placeholders
[ -f "SCOPE.md" ] || cat > SCOPE.md <<EOP
# Project Scope: [Project Name]
## P1: Foundation & Business
- **Customer**: 
- **Problem Statement**: 
- **Outcomes**: 
## P2: Environment
- **GCP Project**: 
- **Region**: 
## P3: Out of Scope
- Anything not explicitly stated in this document is out of scope.
EOP

[ -f "SPEC.md" ] || cat > SPEC.md <<EOP
# Technical Specification
## Technical Environment
- Framework: Google ADK
- Model: [See AGENTS.md for active standards]
## Implementation Plan
- [ ] Foundation setup
EOP

# 5. Git init
[ -d ".git" ] || (git init && cat > .gitignore <<EOG
.env
__pycache__/
.venv/
.pytest_cache/
*.pyc
.DS_Store
EOG
)
```

### Path B: Full ADK/Agent Structure
```bash
# Run Foundation logic (Path A) first, then:
mkdir -p app/tools
[ -f "app/__init__.py" ] || echo "from . import agent" > app/__init__.py
[ -f "app/agent.py" ] || cat > app/agent.py <<EOP
from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="Coordinator",
    instruction="You are a helpful assistant.",
)
EOP

uv add google-adk
[ -f ".env" ] || cat > .env <<EOP
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=""
GOOGLE_CLOUD_LOCATION="us-central1"
EOP
```
