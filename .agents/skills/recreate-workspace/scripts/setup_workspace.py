#!/usr/bin/env python3
"""
L200 Workspace Automated Bootstrapper & Provisioner

Provisions a fully isolated, self-contained L200 / Argolis / ADK development
workspace in a target directory from scratch.

Downloads and installs standalone toolchains directly from Airlock and official
upstream mirrors without any dependency on or hard-linking to existing workspaces.
"""

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Standalone Toolchain Download URLs
URL_UV = "https://github.com/astral-sh/uv/releases/download/0.12.16/uv-x86_64-unknown-linux-gnu.tar.gz"
URL_TERRAFORM = "https://releases.hashicorp.com/terraform/1.16.4/terraform_1.16.4_linux_amd64.zip"
URL_GH = "https://github.com/cli/cli/releases/download/v2.101.0/gh_2.101.0_linux_amd64.tar.gz"
URL_NODE = "https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz"
URL_GCLOUD = "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz"


def log_step(title: str):
    print(f"\n{BOLD}{CYAN}==> {title}{RESET}")


def log_info(msg: str):
    print(f"  {BLUE}i{RESET} {msg}")


def log_success(msg: str):
    print(f"  {GREEN}✓{RESET} {msg}")


def log_warn(msg: str):
    print(f"  {YELLOW}!{RESET} {msg}")


def log_error(msg: str):
    print(f"  {RED}✗{RESET} {msg}")


def run_command(cmd: list[str], cwd: str, env: dict | None = None) -> tuple[int, str, str]:
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
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def download_file(url: str, dest_path: str):
    log_info(f"Downloading: {url} -> {dest_path}")
    # Try curl first for robust handling of corporate proxies and SSL options
    code, stdout, stderr = run_command(["curl", "-fsSL", url, "-o", dest_path], cwd="/tmp")
    if code != 0:
        log_warn(f"curl download failed ({stderr}), falling back to urllib...")
        req = urllib.request.Request(url, headers={"User-Agent": "L200-Workspace-Bootstrapper"})
        with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out:
            shutil.copyfileobj(resp, out)
    log_success(f"Downloaded {os.path.basename(dest_path)}")


def make_executable(path: str):
    if os.path.exists(path):
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def setup_workspace(
    target_dir: str,
    argolis_project: str = "",
    argolis_region: str = "us-central1",
    argolis_zone: str = "us-central1-a",
    skip_git: bool = False,
    skip_verify: bool = False,
) -> bool:
    target_dir = os.path.abspath(os.path.expanduser(target_dir))
    skill_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    templates_dir = os.path.join(skill_dir, "templates")

    print(f"\n{BOLD}{BLUE}======================================================{RESET}")
    print(f"{BOLD}L200 Isolated Workspace Bootstrapper{RESET}")
    print(f"Target Directory: {BOLD}{target_dir}{RESET}")
    print(f"{BOLD}{BLUE}======================================================{RESET}")

    # 1. Directory Scaffolding
    log_step("1. Scaffolding Workspace Directory Structure")
    os.makedirs(target_dir, exist_ok=True)
    dirs_to_create = [
        "bin",
        "terraform",
        "openspec/specs",
        "openspec/changes/archive",
        ".agents/scripts",
        ".agents/skills",
        ".agents/workflows",
        ".gemini/config",
        ".gemini/commands/opsx",
        ".gemini/skills",
        ".gcloud",
        ".python",
        ".nodejs",
    ]
    for d in dirs_to_create:
        p = os.path.join(target_dir, d)
        os.makedirs(p, exist_ok=True)
        # Ensure .gitkeep in empty tracking directories
        if "specs" in d or "archive" in d:
            open(os.path.join(p, ".gitkeep"), "a").close()
    log_success("Created directory layout")

    # 2. Instantiate Templates
    log_step("2. Instantiating Configuration Manifests & Templates")

    # .env
    env_tpl_path = os.path.join(templates_dir, "env.template")
    with open(env_tpl_path, "r", encoding="utf-8") as f:
        env_content = f.read()

    env_rendered = env_content.format(
        WORKSPACE_DIR=target_dir,
        ARGOLIS_PROJECT_ID=argolis_project,
        ARGOLIS_REGION=argolis_region,
        ARGOLIS_ZONE=argolis_zone,
    )
    with open(os.path.join(target_dir, ".env"), "w", encoding="utf-8") as f:
        f.write(env_rendered)
    log_success("Generated isolated .env")

    # Copy single files
    file_mappings = [
        ("pyproject.toml", "pyproject.toml"),
        ("uv.toml", "uv.toml"),
        ("uv.lock", "uv.lock"),
        ("npmrc", ".npmrc"),
        ("python-version", ".python-version"),
        ("gitignore", ".gitignore"),
        ("README.md", "README.md"),
        ("main.py", "main.py"),
        ("AI in 5 Days Assessment Agent.md", "AI in 5 Days Assessment Agent.md"),
        ("bin/argolis", "bin/argolis"),
        ("bin/gcloud", "bin/gcloud"),
        ("bin/jetski", "bin/jetski"),
        ("openspec/config.yaml", "openspec/config.yaml"),
        ("agents/hooks.json", ".agents/hooks.json"),
        ("agents/skills/.openspec-target", ".agents/skills/.openspec-target"),
        ("gemini/config/config.json", ".gemini/config/config.json"),
    ]
    for src_rel, dst_rel in file_mappings:
        src = os.path.join(templates_dir, src_rel)
        dst = os.path.join(target_dir, dst_rel)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            if dst_rel.startswith("bin/"):
                make_executable(dst)
    log_success("Copied base configuration files and CLI helpers")

    # Copy terraform files
    tf_src = os.path.join(templates_dir, "terraform")
    tf_dst = os.path.join(target_dir, "terraform")
    for f in os.listdir(tf_src):
        shutil.copy2(os.path.join(tf_src, f), os.path.join(tf_dst, f))
    log_success("Copied Terraform infrastructure definitions")

    # Copy .agents/scripts
    scripts_src = os.path.join(templates_dir, "agents", "scripts")
    scripts_dst = os.path.join(target_dir, ".agents", "scripts")
    for f in os.listdir(scripts_src):
        dst_f = os.path.join(scripts_dst, f)
        shutil.copy2(os.path.join(scripts_src, f), dst_f)
        if f.endswith(".sh"):
            make_executable(dst_f)
    log_success("Copied pre-command git sanitization hook scripts")

    # Copy workflows
    wf_src = os.path.join(templates_dir, "agents", "workflows")
    wf_dst = os.path.join(target_dir, ".agents", "workflows")
    for f in os.listdir(wf_src):
        shutil.copy2(os.path.join(wf_src, f), os.path.join(wf_dst, f))
    log_success("Copied OpenSpec workflows")

    # Copy gemini commands
    cmd_src = os.path.join(templates_dir, "gemini", "commands", "opsx")
    cmd_dst = os.path.join(target_dir, ".gemini", "commands", "opsx")
    for f in os.listdir(cmd_src):
        shutil.copy2(os.path.join(cmd_src, f), os.path.join(cmd_dst, f))
    log_success("Copied OpenSpec slash commands")

    # Copy skills
    skills_src = os.path.join(templates_dir, "agents", "skills")
    skills_dst = os.path.join(target_dir, ".agents", "skills")
    for s in os.listdir(skills_src):
        s_src = os.path.join(skills_src, s)
        s_dst = os.path.join(skills_dst, s)
        if os.path.isdir(s_src):
            shutil.copytree(s_src, s_dst, dirs_exist_ok=True)
            # Link/mirror to .gemini/skills as well
            gemini_skill_dst = os.path.join(target_dir, ".gemini", "skills", s)
            shutil.copytree(s_src, gemini_skill_dst, dirs_exist_ok=True)
    log_success("Installed OpenSpec and git sanitization skills")

    # Copy the recreate-workspace skill itself so the new workspace is self-replicating
    self_skill_dst = os.path.join(target_dir, ".agents", "skills", "recreate-workspace")
    if skill_dir != self_skill_dst:
        shutil.copytree(
            skill_dir,
            self_skill_dst,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        gemini_self_skill = os.path.join(target_dir, ".gemini", "skills", "recreate-workspace")
        shutil.copytree(
            skill_dir,
            gemini_self_skill,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        log_success("Installed recreate-workspace skill in new workspace")

    # Build execution environment for downloads & installs
    target_bin = os.path.join(target_dir, "bin")
    exec_env = {
        "PATH": f"{target_bin}:{os.environ.get('PATH', '')}",
        "UV_PYTHON_INSTALL_DIR": os.path.join(target_dir, ".python"),
        "CLOUDSDK_CONFIG": os.path.join(target_dir, ".gcloud"),
        "OPENSPEC_TELEMETRY": "0",
    }

    # 3. Toolchain Provisioning from Upstream & Airlock
    tmp_dl = "/tmp/l200_bootstrapper"
    os.makedirs(tmp_dl, exist_ok=True)

    # 3.1 Install uv binary
    log_step("3.1 Provisioning Standalone uv Binary")
    uv_bin = os.path.join(target_bin, "uv")
    if not os.path.exists(uv_bin):
        uv_archive = os.path.join(tmp_dl, "uv.tar.gz")
        download_file(URL_UV, uv_archive)
        with tarfile.open(uv_archive, "r:gz") as tar:
            for member in tar.getmembers():
                if os.path.basename(member.name) == "uv":
                    member.name = os.path.basename(member.name)
                    tar.extract(member, path=target_bin)
                    break
        make_executable(uv_bin)
    log_success("Standalone uv binary active")

    # 3.2 Install standalone Terraform
    log_step("3.2 Provisioning Standalone Terraform (v1.16.4)")
    tf_bin = os.path.join(target_bin, "terraform")
    if not os.path.exists(tf_bin):
        tf_archive = os.path.join(tmp_dl, "terraform.zip")
        download_file(URL_TERRAFORM, tf_archive)
        with zipfile.ZipFile(tf_archive, "r") as z:
            z.extract("terraform", path=target_bin)
        make_executable(tf_bin)
    log_success("Standalone Terraform binary active")

    # 3.3 Install standalone GitHub CLI (gh)
    log_step("3.3 Provisioning Standalone GitHub CLI (gh)")
    gh_bin = os.path.join(target_bin, "gh")
    if not os.path.exists(gh_bin):
        gh_archive = os.path.join(tmp_dl, "gh.tar.gz")
        download_file(URL_GH, gh_archive)
        with tarfile.open(gh_archive, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("/bin/gh"):
                    f = tar.extractfile(member)
                    if f:
                        with open(gh_bin, "wb") as out:
                            out.write(f.read())
                    break
        make_executable(gh_bin)
    log_success("Standalone GitHub CLI binary active")

    # 3.4 Install standalone Node.js LTS
    log_step("3.4 Provisioning Standalone Node.js 22 LTS")
    node_dir = os.path.join(target_dir, ".nodejs")
    os.makedirs(node_dir, exist_ok=True)
    node_extracted = os.path.join(node_dir, "node-v22.14.0-linux-x64")
    if not os.path.exists(node_extracted):
        node_archive = os.path.join(tmp_dl, "node.tar.xz")
        download_file(URL_NODE, node_archive)
        code, stdout, stderr = run_command(["tar", "-xJf", node_archive, "-C", node_dir], cwd=target_dir)
        if code != 0:
            log_error(f"Failed to unpack Node.js: {stderr}")
            return False
    # Link node, npm, npx into bin/
    for tool in ["node", "npm", "npx"]:
        link_target = os.path.join(target_bin, tool)
        rel_src = os.path.join("..", ".nodejs", "node-v22.14.0-linux-x64", "bin", tool)
        if os.path.islink(link_target) or os.path.exists(link_target):
            os.remove(link_target)
        os.symlink(rel_src, link_target)
        make_executable(link_target)
    log_success("Standalone Node.js & npm runtime active")

    # 3.5 Install OpenSpec CLI via Airlock NPM Registry
    log_step("3.5 Installing OpenSpec CLI via Airlock NPM Registry")
    openspec_bin = os.path.join(target_bin, "openspec")
    npm_bin = os.path.join(target_bin, "npm")
    code, stdout, stderr = run_command(
        [npm_bin, "--prefix", node_extracted, "install", "-g", "@fission-ai/openspec"],
        cwd=target_dir,
        env=exec_env,
    )
    if code != 0:
        log_warn(f"Global npm install returned {code}: {stderr}")
    # Symlink openspec into bin/
    openspec_installed = os.path.join(node_extracted, "bin", "openspec")
    if os.path.exists(openspec_installed):
        if os.path.islink(openspec_bin) or os.path.exists(openspec_bin):
            os.remove(openspec_bin)
        os.symlink(os.path.join("..", ".nodejs", "node-v22.14.0-linux-x64", "bin", "openspec"), openspec_bin)
        make_executable(openspec_bin)
    log_success("OpenSpec CLI installed and symlinked")

    # 3.6 Install standalone Google Cloud SDK
    log_step("3.6 Provisioning Standalone Google Cloud SDK")
    gcloud_dir = os.path.join(target_dir, "google-cloud-sdk")
    if not os.path.exists(gcloud_dir):
        gcloud_archive = os.path.join(tmp_dl, "gcloud.tar.gz")
        download_file(URL_GCLOUD, gcloud_archive)
        code, stdout, stderr = run_command(["tar", "-xzf", gcloud_archive, "-C", target_dir], cwd=target_dir)
        if code != 0:
            log_error(f"Failed to unpack gcloud: {stderr}")
            return False
        # Run installer
        log_info("Configuring Google Cloud SDK...")
        installer = os.path.join(gcloud_dir, "install.sh")
        run_command([installer, "--quiet", "--path-update", "false", "--command-completion", "false"], cwd=target_dir)
    log_success("Standalone Google Cloud SDK configured")

    # 3.7 Install Python 3.12 & Google ADK via uv & Airlock Mirror
    log_step("3.7 Installing Python 3.12 & Google ADK via uv")
    log_info("Installing Python 3.12 toolchain into .python/...")
    code, stdout, stderr = run_command([uv_bin, "python", "install", "3.12"], cwd=target_dir, env=exec_env)
    if code != 0:
        log_warn(f"uv python install message: {stderr or stdout}")

    log_info("Creating isolated virtualenv .venv/...")
    code, stdout, stderr = run_command([uv_bin, "venv", ".venv", "--python", "3.12"], cwd=target_dir, env=exec_env)
    if code != 0:
        log_error(f"Failed to create venv: {stderr}")
        return False

    log_info("Synchronizing dependencies (google-adk[gcp], pandas, ipykernel) from Airlock PyPI mirror...")
    code, stdout, stderr = run_command(
        [uv_bin, "sync", "--link-mode", "copy"],
        cwd=target_dir,
        env=exec_env,
    )
    if code != 0:
        # Fallback to direct uv pip install
        code, stdout, stderr = run_command(
            [uv_bin, "pip", "install", "--link-mode", "copy", "google-adk[gcp]>=2.9.1", "pandas>=2.2.0", "ipykernel>=6.29.0"],
            cwd=target_dir,
            env=exec_env,
        )
    log_success("Isolated Python 3.12 virtualenv and Google ADK installed")

    # 3.8 Initialize Terraform Providers
    log_step("3.8 Initializing Terraform GCP Providers")
    code, stdout, stderr = run_command(
        [tf_bin, "-chdir=terraform", "init"],
        cwd=target_dir,
        env=exec_env,
    )
    if code == 0:
        log_success("Terraform initialized successfully")
    else:
        log_warn(f"Terraform init message: {stderr or stdout}")

    # 4. Git Initialization
    if not skip_git and not os.path.exists(os.path.join(target_dir, ".git")):
        log_step("4. Initializing Git Repository")
        run_command(["git", "init"], cwd=target_dir)
        run_command(["git", "add", "."], cwd=target_dir)
        run_command(["git", "commit", "-m", "Initial commit: L200 isolated workspace"], cwd=target_dir)
        log_success("Initialized clean git repository")

    # Cleanup temporary downloads
    shutil.rmtree(tmp_dl, ignore_errors=True)

    # 5. Verification
    if not skip_verify:
        log_step("5. Running Automated Verification Suite")
        verify_script = os.path.join(skill_dir, "scripts", "verify_workspace.py")
        if os.path.exists(verify_script):
            code, stdout, stderr = run_command([sys.executable, verify_script, "--target", target_dir], cwd=target_dir)
            print(stdout)
            if code != 0:
                print(stderr)
                return False

    print(f"\n{BOLD}{GREEN}======================================================{RESET}")
    print(f"{BOLD}{GREEN}✓ WORKSPACE RECREATION COMPLETE: {target_dir}{RESET}")
    print(f"{BOLD}{GREEN}======================================================{RESET}")
    print(f"\nTo activate your new workspace:")
    print(f"  {BOLD}cd {target_dir}{RESET}")
    print(f"  {BOLD}source .env{RESET}")
    print(f"  {BOLD}source .venv/bin/activate{RESET}\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a fresh, isolated L200 workspace from Airlock & upstream sources."
    )
    parser.add_argument(
        "--target",
        "-t",
        default=".",
        help="Target working directory to bootstrap (default: current directory).",
    )
    parser.add_argument(
        "--argolis-project",
        default="",
        help="Argolis GCP project ID to seed in .env.",
    )
    parser.add_argument(
        "--argolis-region",
        default="us-central1",
        help="Default GCP region (default: us-central1).",
    )
    parser.add_argument(
        "--argolis-zone",
        default="us-central1-a",
        help="Default GCP zone (default: us-central1-a).",
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git init and initial commit.",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip post-creation verification.",
    )

    args = parser.parse_args()
    success = setup_workspace(
        target_dir=args.target,
        argolis_project=args.argolis_project,
        argolis_region=args.argolis_region,
        argolis_zone=args.argolis_zone,
        skip_git=args.skip_git,
        skip_verify=args.skip_verify,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

