#!/usr/bin/env bash
# Wrapper to invoke python pre-command hook
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/pre_command_hook.py"
