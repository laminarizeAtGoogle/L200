#!/usr/bin/env python3
"""
Pre-command hook script for Antigravity.
Intercepts tool executions (specifically run_command), detects matching commands
(such as 'git push'), and launches a subagent slash command before allowing or denying.
"""

import json
import os
import re
import shutil
import subprocess
import sys


def find_agy_binary():
    """Finds the agy CLI binary path."""
    which_path = shutil.which("agy")
    if which_path:
        return which_path

    common_paths = [
        os.path.expanduser("~/.gemini/bin/agy"),
        os.path.expanduser("~/.gemini/antigravity/bin/agy"),
        "/usr/local/bin/agy",
    ]
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def main():
    # Read payload from stdin (PreToolUse contract)
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return
        payload = json.loads(raw_input)
    except Exception as e:
        # If input cannot be parsed, allow by default to avoid deadlock
        sys.stderr.write(f"Error parsing PreToolUse payload: {e}\n")
        print(json.dumps({"decision": "allow"}))
        return

    # Extract command line
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    command_line = args.get("CommandLine", "")

    # Load configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "pre-command-config.json")
    config = {
        "targetCommandPattern": r"(^|\b)git\s+push\b",
        "slashCommand": "gitPushSanitizationCheck",
        "denyOnFailure": True,
        "timeoutSeconds": 60,
    }

    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config.update(loaded)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load config from {config_path}: {e}\n")

    pattern = config.get("targetCommandPattern", r"(^|\b)git\s+push\b")
    slash_cmd = config.get("slashCommand", "gitPushSanitizationCheck")
    deny_on_failure = config.get("denyOnFailure", True)
    timeout_sec = config.get("timeoutSeconds", 60)

    # Check if this command matches the target pattern
    if not command_line or not re.search(pattern, command_line, re.IGNORECASE):
        print(json.dumps({"decision": "allow"}))
        return

    # Determine workspace directory
    workspace_paths = payload.get("workspacePaths", [])
    if workspace_paths and os.path.isdir(workspace_paths[0]):
        cwd = workspace_paths[0]
    else:
        # Default to repository root (parent of .agents)
        cwd = os.path.abspath(os.path.join(script_dir, "..", ".."))

    # Check for test override environment variable
    mock_result = os.environ.get("MOCK_SUBAGENT_RESULT")
    if mock_result:
        if mock_result.lower() == "pass":
            print(json.dumps({"decision": "allow"}))
            return
        else:
            reason = os.environ.get(
                "MOCK_SUBAGENT_REASON",
                f"Subagent '{slash_cmd}' detected sanitization issues in outgoing commits.",
            )
            print(
                json.dumps(
                    {
                        "decision": "deny",
                        "reason": f"Pre-command check failed: {slash_cmd} rejected '{command_line}'.\nDetails: {reason}\n\nPlease take corrective actions and try again.",
                    }
                )
            )
            return

    # Find agy CLI binary
    agy_bin = find_agy_binary()
    if not agy_bin:
        sys.stderr.write(f"Warning: agy CLI binary not found. Skipping subagent check.\n")
        print(json.dumps({"decision": "allow"}))
        return

    # Ensure CLI log/crash directory exists
    try:
        os.makedirs(os.path.expanduser("~/.gemini/antigravity-cli"), exist_ok=True)
    except Exception:
        pass

    # Launch subagent slash command
    # Prefix with slash if not present
    cmd_name = slash_cmd if slash_cmd.startswith("/") else f"/{slash_cmd}"
    prompt = f"{cmd_name} Intercepted '{command_line}'. Review outgoing commits and repository state for sanitization."

    agy_cmd = [
        agy_bin,
        "-p",
        prompt,
        "--print-timeout",
        f"{timeout_sec}s",
    ]

    try:
        proc = subprocess.run(
            agy_cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec + 5,
        )
        stdout_output = proc.stdout.strip()
        stderr_output = proc.stderr.strip()

        # Check for failure: non-zero return code or explicit failure marker in output
        failed = False
        failure_details = []

        if proc.returncode != 0:
            failed = True
            if stderr_output:
                failure_details.append(stderr_output)
            if stdout_output:
                failure_details.append(stdout_output)
        elif "SANITIZATION_CHECK: FAILED" in stdout_output:
            failed = True
            failure_details.append(stdout_output)

        if failed and deny_on_failure:
            detail_msg = "\n".join(failure_details) if failure_details else "Check did not pass."
            decision_payload = {
                "decision": "deny",
                "reason": (
                    f"Pre-push sanitization check ({slash_cmd}) failed prior to '{command_line}'.\n"
                    f"Subagent output:\n{detail_msg}\n\n"
                    f"Please review the issues reported by /{slash_cmd}, take corrective actions, and try again."
                ),
            }
            print(json.dumps(decision_payload))
            return

        # Passed
        print(json.dumps({"decision": "allow"}))

    except subprocess.TimeoutExpired:
        if deny_on_failure:
            print(
                json.dumps(
                    {
                        "decision": "deny",
                        "reason": f"Pre-command check ({slash_cmd}) timed out after {timeout_sec}s. Please check subagent status or retry.",
                    }
                )
            )
        else:
            print(json.dumps({"decision": "allow"}))
    except Exception as e:
        sys.stderr.write(f"Error launching subagent {slash_cmd}: {e}\n")
        # On runtime execution error of the hook itself, allow or deny based on policy
        if deny_on_failure:
            print(
                json.dumps(
                    {
                        "decision": "deny",
                        "reason": f"Unable to complete pre-command check ({slash_cmd}): {e}. Execution halted for safety.",
                    }
                )
            )
        else:
            print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
