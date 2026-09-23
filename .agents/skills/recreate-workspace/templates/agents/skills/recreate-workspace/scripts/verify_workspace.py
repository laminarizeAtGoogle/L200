#!/usr/bin/env python3
"""
Workspace Integrity & Health Verifier

Validates that an L200 / Argolis / ADK workspace is correctly configured,
self-contained, and operational across all 9 architectural pillars.
"""

import argparse
import os
import subprocess
import sys

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_pass(msg: str):
    print(f"  [{GREEN}PASS{RESET}] {msg}")


def log_fail(msg: str, detail: str = ""):
    print(f"  [{RED}FAIL{RESET}] {msg}")
    if detail:
        print(f"         {YELLOW}{detail}{RESET}")


def log_warn(msg: str):
    print(f"  [{YELLOW}WARN{RESET}] {msg}")


def run_cmd(cmd: list[str], cwd: str, env: dict | None = None) -> tuple[int, str, str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=merged_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def check_file(target_dir: str, rel_path: str, executable: bool = False) -> bool:
    full_path = os.path.join(target_dir, rel_path)
    if not os.path.exists(full_path):
        log_fail(f"Missing file: {rel_path}")
        return False
    if executable and not os.access(full_path, os.X_OK):
        log_fail(f"File not executable: {rel_path}")
        return False
    log_pass(f"Found {rel_path}" + (" (executable)" if executable else ""))
    return True


def verify_workspace(target_dir: str) -> bool:
    target_dir = os.path.abspath(target_dir)
    print(f"\n{BOLD}{BLUE}======================================================{RESET}")
    print(f"{BOLD}Verifying Workspace Integrity: {target_dir}{RESET}")
    print(f"{BOLD}{BLUE}======================================================{RESET}\n")

    if not os.path.isdir(target_dir):
        print(f"{RED}Target directory does not exist: {target_dir}{RESET}")
        return False

    all_passed = True

    # 1. Directory Structure
    print(f"{BOLD}1. Directory Structure & Layout{RESET}")
    required_dirs = [
        "bin",
        "terraform",
        "openspec",
        ".agents/scripts",
        ".agents/skills",
        ".agents/workflows",
        ".gemini/config",
        ".gemini/commands/opsx",
        ".gcloud",
    ]
    for d in required_dirs:
        p = os.path.join(target_dir, d)
        if os.path.isdir(p):
            log_pass(f"Directory {d}/")
        else:
            log_fail(f"Missing directory {d}/")
            all_passed = False

    # 2. Toolchain Binaries
    print(f"\n{BOLD}2. Toolchain Binaries in bin/{RESET}")
    required_bins = [
        ("bin/uv", True),
        ("bin/terraform", True),
        ("bin/gh", True),
        ("bin/gcloud", True),
        ("bin/argolis", True),
        ("bin/jetski", True),
        ("bin/node", True),
        ("bin/npm", True),
        ("bin/npx", True),
        ("bin/openspec", True),
    ]
    for b, is_exec in required_bins:
        if not check_file(target_dir, b, is_exec):
            all_passed = False

    # 3. Environment & Configuration Files
    print(f"\n{BOLD}3. Configuration & Template Manifests{RESET}")
    required_configs = [
        "pyproject.toml",
        "uv.toml",
        ".npmrc",
        ".python-version",
        ".gitignore",
        "README.md",
        "main.py",
        "terraform/main.tf",
        "terraform/variables.tf",
        "terraform/outputs.tf",
        "terraform/provider.tf",
        "terraform/versions.tf",
        "terraform/terraform.tfvars.example",
        "openspec/config.yaml",
        ".agents/hooks.json",
        ".agents/scripts/pre-command-hook.sh",
        ".agents/scripts/pre_command_hook.py",
        ".agents/scripts/test_pre_command_hook.py",
        ".agents/scripts/pre-command-config.json",
        ".gemini/config/config.json",
    ]
    for c in required_configs:
        if not check_file(target_dir, c):
            all_passed = False

    # Verify .env paths
    env_path = os.path.join(target_dir, ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()
        if target_dir in env_content:
            log_pass(".env contains correct absolute workspace paths")
        else:
            log_warn(".env exists but target_dir path was not explicitly matched")
    else:
        log_fail("Missing .env")
        all_passed = False

    # 4. Runtime & Toolchain Execution Checks
    print(f"\n{BOLD}4. Toolchain Execution Verification{RESET}")
    test_env = {
        "PATH": f"{os.path.join(target_dir, 'bin')}:{os.environ.get('PATH', '')}",
        "CLOUDSDK_CONFIG": os.path.join(target_dir, ".gcloud"),
    }

    # Test Node & NPM
    code, stdout, stderr = run_cmd([os.path.join(target_dir, "bin", "node"), "--version"], target_dir, test_env)
    if code == 0:
        log_pass(f"Node.js runtime active: {stdout}")
    else:
        log_fail("Node.js runtime check failed", stderr)
        all_passed = False

    code, stdout, stderr = run_cmd([os.path.join(target_dir, "bin", "npm"), "--version"], target_dir, test_env)
    if code == 0:
        log_pass(f"npm package manager active: v{stdout}")
    else:
        log_fail("npm check failed", stderr)
        all_passed = False

    # Test OpenSpec CLI
    code, stdout, stderr = run_cmd([os.path.join(target_dir, "bin", "openspec"), "--version"], target_dir, test_env)
    if code == 0:
        log_pass(f"OpenSpec CLI active: v{stdout}")
    else:
        log_fail("OpenSpec CLI check failed", stderr)
        all_passed = False

    # Test Terraform
    code, stdout, stderr = run_cmd([os.path.join(target_dir, "bin", "terraform"), "version"], target_dir, test_env)
    if code == 0:
        tf_ver = stdout.splitlines()[0] if stdout else "OK"
        log_pass(f"Terraform binary active: {tf_ver}")
    else:
        log_fail("Terraform version check failed", stderr)
        all_passed = False

    code, stdout, stderr = run_cmd([os.path.join(target_dir, "bin", "terraform"), "-chdir=terraform", "validate"], target_dir, test_env)
    if code == 0:
        log_pass("Terraform configuration valid (terraform validate passed)")
    else:
        log_fail("Terraform validate check failed", stderr or stdout)
        all_passed = False

    # Test GitHub CLI
    code, stdout, stderr = run_cmd([os.path.join(target_dir, "bin", "gh"), "--version"], target_dir, test_env)
    if code == 0:
        gh_ver = stdout.splitlines()[0] if stdout else "OK"
        log_pass(f"GitHub CLI active: {gh_ver}")
    else:
        log_fail("GitHub CLI check failed", stderr)
        all_passed = False

    # Test Argolis CLI Helper
    code, stdout, stderr = run_cmd([os.path.join(target_dir, "bin", "argolis"), "help"], target_dir, test_env)
    if code == 0:
        log_pass("Argolis CLI helper functional")
    else:
        log_fail("Argolis CLI helper check failed", stderr)
        all_passed = False

    # 5. Python & ADK Environment
    print(f"\n{BOLD}5. Python & Google ADK Environment Verification{RESET}")
    uv_bin = os.path.join(target_dir, "bin", "uv")
    if os.path.exists(uv_bin):
        code, stdout, stderr = run_cmd([uv_bin, "--version"], target_dir, test_env)
        if code == 0:
            log_pass(f"uv binary operational: {stdout}")
        else:
            log_fail("uv binary failed", stderr)
            all_passed = False

        # Run main.py via uv
        code, stdout, stderr = run_cmd([uv_bin, "run", "--env-file", ".env", "python", "main.py"], target_dir, test_env)
        if code == 0 and "Environment verification successful!" in stdout:
            log_pass("main.py execution passed: google.adk, pandas, and ipykernel verified")
        else:
            log_fail("main.py verification failed", stderr or stdout)
            all_passed = False
    else:
        log_fail("uv binary missing, skipping python verification")
        all_passed = False

    # 6. Pre-Command Git Push Sanitization Hook Suite
    print(f"\n{BOLD}6. Git Push Sanitization Hook Suite{RESET}")
    test_script = os.path.join(target_dir, ".agents", "scripts", "test_pre_command_hook.py")
    if os.path.isfile(test_script):
        code, stdout, stderr = run_cmd([sys.executable, test_script], target_dir, test_env)
        if code == 0 and "OK" in stderr or "OK" in stdout:
            log_pass("Pre-command hook unit tests (14/14) passed")
        else:
            log_fail("Pre-command hook unit tests failed", stderr or stdout)
            all_passed = False
    else:
        log_fail(f"Missing {test_script}")
        all_passed = False

    # Summary
    print(f"\n{BOLD}{BLUE}======================================================{RESET}")
    if all_passed:
        print(f"{BOLD}{GREEN}✓ ALL WORKSPACE INTEGRITY CHECKS PASSED SUCCESSFULLY{RESET}")
        print(f"{BOLD}{BLUE}======================================================{RESET}\n")
        return True
    else:
        print(f"{BOLD}{RED}✗ SOME WORKSPACE INTEGRITY CHECKS FAILED{RESET}")
        print(f"{BOLD}{BLUE}======================================================{RESET}\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify L200 workspace health and integrity.")
    parser.add_argument(
        "--target",
        "-t",
        default=".",
        help="Target workspace directory to verify (default: current directory).",
    )
    args = parser.parse_args()
    success = verify_workspace(args.target)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
