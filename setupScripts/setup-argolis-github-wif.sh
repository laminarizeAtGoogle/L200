#!/usr/bin/env bash
# ==============================================================================
# Argolis GCP Workload Identity Federation (WIF) Setup for GitHub Actions
#
# PURPOSE:
#   Sets up keyless, secure authentication between GitHub Actions and an Argolis
#   GCP project using Workload Identity Federation (OIDC).
#
#   This allows GitHub Actions to run 'terraform apply' on merge to main
#   without requiring long-lived service account JSON keys.
#
# USAGE:
#   Run this script from Google Cloud Shell (recommended) or an authenticated
#   admin terminal with permission to create IAM resources in the target project.
#
#   ./setupScripts/setup-argolis-github-wif.sh --project <PROJECT_ID> --repo <OWNER/REPO>
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default configuration
ENV_PROJECT_ID="${PROJECT_ID:-${ARGOLIS_PROJECT_ID:-}}"
PROJECT_ID=""
REPO=""
CLI_PROJECT_SET="false"
CLI_REPO_SET="false"
SA_NAME="github-terraform-deployer"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"
REGION="us-central1"
BUCKET_NAME=""
AUTO_DEPLOY_GH=""
CONDITION_MODE="" # "replace" or "append"

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Provisions Workload Identity Federation (WIF) and Terraform remote state in Argolis.
Portable across any GCP project and GitHub repository.

Options:
  -p, --project PROJECT_ID     Target Argolis GCP project ID.
                               (Prompts interactively or uses active gcloud project if omitted)
  -r, --repo OWNER/REPO        GitHub repository (e.g. 'octocat/hello-world' or full GitHub URL).
                               (Prompts interactively if omitted)
  -s, --sa-name SA_NAME        Deployment Service Account name.
                               (Default: ${SA_NAME})
  -b, --bucket BUCKET_NAME     GCS bucket for Terraform state.
                               (Default: <PROJECT_ID>-tfstate)
  --pool POOL_NAME             Workload Identity Pool name.
                               (Default: ${POOL_NAME})
  --provider PROVIDER_NAME     Workload Identity Provider name.
                               (Default: ${PROVIDER_NAME})
  --region REGION              GCP region for state bucket.
                               (Default: ${REGION})
  --replace-repo-condition     If OIDC provider exists, replace its attribute condition with only --repo.
  --append-repo-condition      If OIDC provider exists, append --repo to its existing attribute condition.
  --auto-deploy-gh             Automatically set variables in GitHub via 'gh' CLI.
  --skip-gh                    Skip GitHub CLI variable deployment.
  -h, --help                   Display this help message and exit.

Examples:
  $(basename "$0") --project my-gcp-project-1234 --repo octocat/my-new-project
  $(basename "$0")
EOF
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project)
      PROJECT_ID="$2"
      CLI_PROJECT_SET="true"
      shift 2
      ;;
    -r|--repo)
      REPO="$2"
      CLI_REPO_SET="true"
      shift 2
      ;;
    -s|--sa-name)
      SA_NAME="$2"
      shift 2
      ;;
    -b|--bucket)
      BUCKET_NAME="$2"
      shift 2
      ;;
    --pool)
      POOL_NAME="$2"
      shift 2
      ;;
    --provider)
      PROVIDER_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --replace-repo-condition)
      CONDITION_MODE="replace"
      shift
      ;;
    --append-repo-condition)
      CONDITION_MODE="append"
      shift
      ;;
    --auto-deploy-gh|--deploy-gh)
      AUTO_DEPLOY_GH="true"
      shift
      ;;
    --skip-gh)
      AUTO_DEPLOY_GH="false"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: Unknown argument '$1'" >&2
      usage
      exit 1
      ;;
  esac
done

# ------------------------------------------------------------------------------
# Discover GitHub CLI ('gh') Binary (System PATH, local ./bin/gh, or sibling workspace)
# ------------------------------------------------------------------------------
GH_BIN=""
if command -v gh >/dev/null 2>&1; then
  GH_BIN="$(command -v gh)"
elif [[ -x "./bin/gh" ]]; then
  GH_BIN="$(cd ./bin && pwd)/gh"
elif [[ -x "${SCRIPT_DIR}/../bin/gh" ]]; then
  GH_BIN="$(cd "${SCRIPT_DIR}/../bin" && pwd)/gh"
else
  # Search sibling project directories (e.g. ../other-workspace/bin/gh) if running in a new workspace
  for candidate in "$(cd "${SCRIPT_DIR}/../.." 2>/dev/null && pwd)"/*/bin/gh; do
    if [[ -x "${candidate}" ]]; then
      GH_BIN="${candidate}"
      break
    fi
  done
fi

# Helper to normalize a GitHub repo input (strips https://github.com/, git@github.com:, and .git)
normalize_github_repo() {
  local raw="$1"
  raw="$(echo "${raw}" | sed -E 's|^[[:space:]]+||; s|[[:space:]]+$||')"
  raw="$(echo "${raw}" | sed -E 's|^.*github\.com[:/]([^/]+/[^/]+?)(\.git)?/?$|\1|')"
  raw="${raw%.git}"
  raw="${raw%/}"
  echo "${raw}"
}

# ------------------------------------------------------------------------------
# 1. Resolve & Validate GCP Project ID
# ------------------------------------------------------------------------------
ACTIVE_GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
if [[ "${ACTIVE_GCLOUD_PROJECT}" == "(unset)" ]]; then
  ACTIVE_GCLOUD_PROJECT=""
fi

if [[ "${CLI_PROJECT_SET}" != "true" ]]; then
  # Prefer active gcloud config over potentially stale environment variables from another workspace
  DEFAULT_PROJECT="${ACTIVE_GCLOUD_PROJECT:-${ENV_PROJECT_ID:-}}"
  if [[ "${DEFAULT_PROJECT}" == "<YOUR_ARGOLIS_PROJECT_ID>" || "${DEFAULT_PROJECT}" == "<PROJECT_ID>" ]]; then
    DEFAULT_PROJECT=""
  fi

  if [[ -t 0 ]]; then
    if [[ -n "${DEFAULT_PROJECT}" ]]; then
      read -r -p "Target GCP Project ID [${DEFAULT_PROJECT}]: " INPUT_PROJECT
      PROJECT_ID="${INPUT_PROJECT:-${DEFAULT_PROJECT}}"
    else
      read -r -p "Enter Target GCP Project ID: " PROJECT_ID
    fi
  else
    PROJECT_ID="${DEFAULT_PROJECT}"
  fi
fi

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "<YOUR_ARGOLIS_PROJECT_ID>" || "${PROJECT_ID}" == "<PROJECT_ID>" ]]; then
  echo "Error: PROJECT_ID is required." >&2
  echo "Provide it with --project <PROJECT_ID>, export PROJECT_ID=<PROJECT_ID>, or set your active gcloud project." >&2
  exit 1
fi

# GCP project IDs must be strictly lowercase
if [[ "${PROJECT_ID}" =~ [A-Z] ]]; then
  echo "Error: GCP Project ID '${PROJECT_ID}' contains uppercase letters, which are invalid in Google Cloud." >&2
  if [[ -n "${ACTIVE_GCLOUD_PROJECT}" ]]; then
    echo "Hint: Your active gcloud project is '${ACTIVE_GCLOUD_PROJECT}'. Try running with:" >&2
    echo "  $(basename "$0") --project ${ACTIVE_GCLOUD_PROJECT} --repo ${REPO:-<OWNER/REPO>}" >&2
  fi
  exit 1
fi

# ------------------------------------------------------------------------------
# 2. Resolve & Validate GitHub Repository (OWNER/REPO)
# ------------------------------------------------------------------------------
# Do NOT silently inherit git remote 'origin' from the directory where the script
# is stored (e.g. an existing repo clone in Cloud Shell or another workspace).
# Require explicit --repo or interactive user input for the target repository.
GH_DEFAULT_OWNER=""
if [[ -n "${GH_BIN}" ]]; then
  if "${GH_BIN}" auth status --hostname github.com >/dev/null 2>&1; then
    GH_DEFAULT_OWNER=$("${GH_BIN}" api user -q .login 2>/dev/null || true)
  fi
fi

if [[ "${CLI_REPO_SET}" != "true" && -z "${REPO}" ]]; then
  if [[ -t 0 ]]; then
    echo ""
    if [[ -n "${GH_DEFAULT_OWNER}" ]]; then
      read -r -p "Enter Target GitHub Repository (OWNER/REPO, or REPO name under '${GH_DEFAULT_OWNER}'): " INPUT_REPO
      INPUT_REPO="$(normalize_github_repo "${INPUT_REPO}")"
      if [[ -n "${INPUT_REPO}" && "${INPUT_REPO}" != *"/"* ]]; then
        REPO="${GH_DEFAULT_OWNER}/${INPUT_REPO}"
      else
        REPO="${INPUT_REPO}"
      fi
    else
      read -r -p "Enter Target GitHub Repository (OWNER/REPO, e.g. octocat/my-project): " INPUT_REPO
      REPO="$(normalize_github_repo "${INPUT_REPO}")"
    fi
  else
    echo "Error: --repo <OWNER/REPO> is required when running non-interactively." >&2
    usage
    exit 1
  fi
fi

REPO="$(normalize_github_repo "${REPO}")"
if [[ -n "${REPO}" && "${REPO}" != *"/"* && -n "${GH_DEFAULT_OWNER}" ]]; then
  REPO="${GH_DEFAULT_OWNER}/${REPO}"
fi

if [[ -z "${REPO}" || ! "${REPO}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo "Error: Valid --repo <OWNER/REPO> is required (e.g. --repo octocat/my-project)." >&2
  usage
  exit 1
fi

# ------------------------------------------------------------------------------
# 3. GitHub CLI Authentication Check & Repository / Variable Setup
# ------------------------------------------------------------------------------
if [[ -z "${AUTO_DEPLOY_GH}" ]]; then
  if [[ -t 0 ]]; then
    echo ""
    echo "================================================================="
    echo " GitHub CLI Deployment Integration"
    echo "================================================================="
    echo "This script can automatically configure the resulting variables"
    echo "in GitHub repository '${REPO}' using the GitHub CLI ('gh')."
    echo ""
    read -r -p "Would you like to automatically deploy variables to GitHub? [Y/n]: " GH_CHOICE
    GH_CHOICE="${GH_CHOICE:-Y}"
    if [[ "${GH_CHOICE}" =~ ^[Yy]$ ]]; then
      AUTO_DEPLOY_GH="true"
    else
      AUTO_DEPLOY_GH="false"
    fi
  else
    AUTO_DEPLOY_GH="false"
  fi
fi

if [[ "${AUTO_DEPLOY_GH}" == "true" ]]; then
  if [[ -z "${GH_BIN}" ]]; then
    echo "Notice: GitHub CLI ('gh') is not installed or found in bin/. Variables will be output for manual entry."
    AUTO_DEPLOY_GH="false"
  else
    echo "Checking GitHub CLI ('gh') authentication status..."
    if "${GH_BIN}" auth status --hostname github.com >/dev/null 2>&1; then
      GH_USER=$("${GH_BIN}" api user -q .login 2>/dev/null || echo "authenticated user")
      echo "✓ GitHub CLI is already authenticated as '${GH_USER}'."
    else
      echo "Notice: You are not currently authenticated to GitHub in this terminal session."
      if [[ -t 0 ]]; then
        read -r -p "Would you like to log in now using 'gh auth login'? [Y/n]: " LOGIN_CHOICE
        LOGIN_CHOICE="${LOGIN_CHOICE:-Y}"
        if [[ "${LOGIN_CHOICE}" =~ ^[Yy]$ ]]; then
          echo "Launching 'gh auth login'..."
          "${GH_BIN}" auth login
          if "${GH_BIN}" auth status --hostname github.com >/dev/null 2>&1; then
            GH_USER=$("${GH_BIN}" api user -q .login 2>/dev/null || echo "authenticated user")
            echo "✓ Successfully authenticated with GitHub as '${GH_USER}'!"
          else
            echo "Warning: GitHub authentication was not completed. Variables will be output for manual entry."
            AUTO_DEPLOY_GH="false"
          fi
        else
          echo "Skipping automatic deployment. Variables will be displayed at the end for manual entry."
          AUTO_DEPLOY_GH="false"
        fi
      else
        echo "Non-interactive session detected. Skipping 'gh auth login'."
        AUTO_DEPLOY_GH="false"
      fi
    fi

    # Check if the target GitHub repository exists; offer to create it if missing
    if [[ "${AUTO_DEPLOY_GH}" == "true" ]]; then
      if ! "${GH_BIN}" repo view "${REPO}" >/dev/null 2>&1; then
        echo "Notice: GitHub repository '${REPO}' was not found or is not yet created."
        if [[ -t 0 ]]; then
          read -r -p "Would you like to create GitHub repository '${REPO}' now? [Y/n]: " CREATE_REPO_CHOICE
          CREATE_REPO_CHOICE="${CREATE_REPO_CHOICE:-Y}"
          if [[ "${CREATE_REPO_CHOICE}" =~ ^[Yy]$ ]]; then
            read -r -p "Repository visibility ([p]rivate / pub[l]ic) [p]: " VIS_CHOICE
            VIS_FLAG="--private"
            if [[ "${VIS_CHOICE}" =~ ^[Ll]$ || "${VIS_CHOICE}" == "public" ]]; then
              VIS_FLAG="--public"
            fi
            if git -C "$(pwd)" rev-parse --is-inside-work-tree >/dev/null 2>&1 && ! git -C "$(pwd)" remote get-url origin >/dev/null 2>&1; then
              "${GH_BIN}" repo create "${REPO}" "${VIS_FLAG}" --source="$(pwd)" --remote=origin
              echo "✓ Created GitHub repository '${REPO}' and linked local git remote 'origin'."
            else
              "${GH_BIN}" repo create "${REPO}" "${VIS_FLAG}"
              echo "✓ Created GitHub repository '${REPO}'."
            fi
          fi
        fi
      elif git -C "$(pwd)" rev-parse --is-inside-work-tree >/dev/null 2>&1 && ! git -C "$(pwd)" remote get-url origin >/dev/null 2>&1; then
        if [[ -t 0 ]]; then
          read -r -p "Link current directory's git remote 'origin' to 'https://github.com/${REPO}.git'? [Y/n]: " LINK_ORIGIN_CHOICE
          LINK_ORIGIN_CHOICE="${LINK_ORIGIN_CHOICE:-Y}"
          if [[ "${LINK_ORIGIN_CHOICE}" =~ ^[Yy]$ ]]; then
            git -C "$(pwd)" remote add origin "https://github.com/${REPO}.git"
            echo "✓ Set git remote 'origin' -> https://github.com/${REPO}.git"
          fi
        fi
      fi
    fi
  fi
fi

if [[ -z "${BUCKET_NAME}" ]]; then
  BUCKET_NAME="${PROJECT_ID}-tfstate"
fi

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo ""
echo "================================================================="
echo "Argolis GitHub Actions Workload Identity Federation Provisioner"
echo "================================================================="
echo "Target GCP Project:   ${PROJECT_ID}"
echo "GitHub Repository:    ${REPO}"
echo "Deployer SA:          ${SA_EMAIL}"
echo "WIF Pool Name:        ${POOL_NAME}"
echo "WIF Provider Name:    ${PROVIDER_NAME}"
echo "State Bucket:         gs://${BUCKET_NAME}"
echo "================================================================="
echo ""

# 1. Retrieve Project Number
echo "==> [1/7] Discovering project number..."
if ! PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)" 2>/dev/null); then
  echo "Error: Could not find or access GCP project '${PROJECT_ID}'." >&2
  echo "Please verify that the project ID is correct and that you have permissions on it." >&2
  if [[ -n "${ACTIVE_GCLOUD_PROJECT}" && "${ACTIVE_GCLOUD_PROJECT}" != "${PROJECT_ID}" ]]; then
    echo "Notice: Your active gcloud project is '${ACTIVE_GCLOUD_PROJECT}'." >&2
  fi
  exit 1
fi
echo "    Project Number: ${PROJECT_NUMBER}"

# 2. Enable Required APIs
echo "==> [2/7] Enabling required GCP APIs..."
gcloud services enable \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

# 3. Create Cloud Storage State Bucket
echo "==> [3/7] Provisioning Terraform state bucket..."
if gcloud storage buckets describe "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "    Bucket gs://${BUCKET_NAME} already exists."
else
  echo "    Creating bucket gs://${BUCKET_NAME} in ${REGION}..."
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi

# Ensure bucket versioning is enabled
gcloud storage buckets update "gs://${BUCKET_NAME}" --versioning >/dev/null 2>&1 || true
echo "    Bucket versioning is enabled."

# 4. Create Service Account
echo "==> [4/7] Configuring deployment Service Account..."
if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "    Service Account ${SA_EMAIL} already exists."
else
  echo "    Creating Service Account ${SA_NAME}..."
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="GitHub Actions Terraform Deployer" \
    --project="${PROJECT_ID}"
fi

# Grant roles to Service Account (Project Editor + Storage Admin)
echo "    Binding roles/editor on project ${PROJECT_ID}..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/editor" \
  --condition=None >/dev/null

echo "    Binding roles/storage.admin on gs://${BUCKET_NAME}..."
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin" >/dev/null 2>&1 || true

# 5. Create Workload Identity Pool
echo "==> [5/7] Configuring Workload Identity Pool..."
if gcloud iam workload-identity-pools describe "${POOL_NAME}" --location="global" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "    Workload Identity Pool '${POOL_NAME}' already exists."
else
  echo "    Creating Workload Identity Pool '${POOL_NAME}'..."
  gcloud iam workload-identity-pools create "${POOL_NAME}" \
    --location="global" \
    --display-name="GitHub Actions Pool" \
    --description="Pool for GitHub Actions workflows" \
    --project="${PROJECT_ID}"
fi

# 6. Create or Update Workload Identity Provider
echo "==> [6/7] Configuring Workload Identity Provider..."
DESIRED_REPO_CLAUSE="assertion.repository == '${REPO}'"
REMOVE_STALE_SA_BINDINGS="false"

if gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
  --location="global" \
  --workload-identity-pool="${POOL_NAME}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  EXISTING_CONDITION=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
    --location="global" \
    --workload-identity-pool="${POOL_NAME}" \
    --project="${PROJECT_ID}" \
    --format="value(attributeCondition)" 2>/dev/null || true)

  if [[ "${EXISTING_CONDITION}" == "${DESIRED_REPO_CLAUSE}" ]]; then
    echo "    Workload Identity Provider '${PROVIDER_NAME}' already configured for '${REPO}'."
  else
    echo "    Workload Identity Provider '${PROVIDER_NAME}' exists with condition:"
    echo "      ${EXISTING_CONDITION:-<none>}"

    if [[ -z "${CONDITION_MODE}" ]]; then
      if [[ -t 0 && -n "${EXISTING_CONDITION}" ]]; then
        read -r -p "    [R]eplace provider condition with '${REPO}' only, or [A]ppend '${REPO}' to existing condition? [R/a]: " COND_CHOICE
        COND_CHOICE="${COND_CHOICE:-R}"
        if [[ "${COND_CHOICE}" =~ ^[Aa]$ ]]; then
          CONDITION_MODE="append"
        else
          CONDITION_MODE="replace"
        fi
      else
        CONDITION_MODE="replace"
      fi
    fi

    if [[ "${CONDITION_MODE}" == "append" && -n "${EXISTING_CONDITION}" ]]; then
      if [[ "${EXISTING_CONDITION}" == *"'${REPO}'"* ]]; then
        NEW_CONDITION="${EXISTING_CONDITION}"
      else
        NEW_CONDITION="(${EXISTING_CONDITION}) || ${DESIRED_REPO_CLAUSE}"
      fi
    else
      NEW_CONDITION="${DESIRED_REPO_CLAUSE}"
      REMOVE_STALE_SA_BINDINGS="true"
    fi

    echo "    Updating OIDC Provider '${PROVIDER_NAME}' attribute condition to:"
    echo "      ${NEW_CONDITION}"
    gcloud iam workload-identity-pools providers update-oidc "${PROVIDER_NAME}" \
      --location="global" \
      --workload-identity-pool="${POOL_NAME}" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
      --attribute-condition="${NEW_CONDITION}" \
      --project="${PROJECT_ID}" >/dev/null
    echo "    ✓ Updated OIDC Provider '${PROVIDER_NAME}'."
  fi
else
  echo "    Creating OIDC Provider '${PROVIDER_NAME}' for repository '${REPO}'..."
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_NAME}" \
    --location="global" \
    --workload-identity-pool="${POOL_NAME}" \
    --display-name="GitHub Actions OIDC Provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="${DESIRED_REPO_CLAUSE}" \
    --project="${PROJECT_ID}"
fi

# 7. Grant GitHub Repository Access to Impersonate Service Account
echo "==> [7/7] Authorizing GitHub repository '${REPO}' to impersonate Service Account..."
WIF_POOL_PREFIX="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/"
WIF_MEMBER="${WIF_POOL_PREFIX}${REPO}"

# If replacing a previous repo condition on this project, clean up any stale WIF repo bindings on the SA
if [[ "${REMOVE_STALE_SA_BINDINGS}" == "true" ]]; then
  EXISTING_WIF_MEMBERS=$(gcloud iam service-accounts get-iam-policy "${SA_EMAIL}" \
    --project="${PROJECT_ID}" \
    --flatten="bindings[].members" \
    --filter="bindings.role=roles/iam.workloadIdentityUser" \
    --format="value(bindings.members)" 2>/dev/null || true)
  while IFS= read -r member; do
    if [[ -n "${member}" && "${member}" == "${WIF_POOL_PREFIX}"* && "${member}" != "${WIF_MEMBER}" ]]; then
      echo "    Removing stale WIF binding: ${member}"
      gcloud iam service-accounts remove-iam-policy-binding "${SA_EMAIL}" \
        --role="roles/iam.workloadIdentityUser" \
        --member="${member}" \
        --project="${PROJECT_ID}" >/dev/null 2>&1 || true
    fi
  done <<< "${EXISTING_WIF_MEMBERS}"
fi

gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="${WIF_MEMBER}" \
  --project="${PROJECT_ID}" >/dev/null

WIF_PROVIDER_FULL="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"

echo ""
echo "================================================================="
echo " Argolis Workload Identity Federation Configured Successfully!"
echo "================================================================="
echo ""
echo "Configure the following GitHub Variables or Secrets in:"
echo "https://github.com/${REPO}/settings/secrets/actions"
echo ""
echo "Variable / Secret Names & Values:"
echo "-----------------------------------------------------------------"
echo "GCP_PROJECT_ID:"
echo "${PROJECT_ID}"
echo ""
echo "GCP_WORKLOAD_IDENTITY_PROVIDER:"
echo "${WIF_PROVIDER_FULL}"
echo ""
echo "GCP_SERVICE_ACCOUNT:"
echo "${SA_EMAIL}"
echo ""
echo "TF_STATE_BUCKET:"
echo "${BUCKET_NAME}"
echo "-----------------------------------------------------------------"
if [[ "${AUTO_DEPLOY_GH}" == "true" && -n "${GH_BIN}" ]]; then
  echo ""
  echo "==> Deploying variables to GitHub repository '${REPO}' via GitHub CLI..."
  "${GH_BIN}" variable set GCP_PROJECT_ID --body "${PROJECT_ID}" --repo "${REPO}"
  echo "    ✓ Set GCP_PROJECT_ID=${PROJECT_ID}"
  "${GH_BIN}" variable set GCP_WORKLOAD_IDENTITY_PROVIDER --body "${WIF_PROVIDER_FULL}" --repo "${REPO}"
  echo "    ✓ Set GCP_WORKLOAD_IDENTITY_PROVIDER"
  "${GH_BIN}" variable set GCP_SERVICE_ACCOUNT --body "${SA_EMAIL}" --repo "${REPO}"
  echo "    ✓ Set GCP_SERVICE_ACCOUNT=${SA_EMAIL}"
  "${GH_BIN}" variable set TF_STATE_BUCKET --body "${BUCKET_NAME}" --repo "${REPO}"
  echo "    ✓ Set TF_STATE_BUCKET=${BUCKET_NAME}"
  echo ""
  echo "✓ All 4 variables successfully configured in GitHub repository '${REPO}'!"
  echo "You can verify them at: https://github.com/${REPO}/settings/variables/actions"
else
  GH_CMD_DISPLAY="${GH_BIN:-gh}"
  echo ""
  echo "Configure these GitHub Variables or Secrets manually in:"
  echo "https://github.com/${REPO}/settings/secrets/actions"
  echo ""
  echo "Tip: You can set these automatically using the GitHub CLI if authenticated:"
  echo ""
  echo "  ${GH_CMD_DISPLAY} variable set GCP_PROJECT_ID --body \"${PROJECT_ID}\" --repo \"${REPO}\""
  echo "  ${GH_CMD_DISPLAY} variable set GCP_WORKLOAD_IDENTITY_PROVIDER --body \"${WIF_PROVIDER_FULL}\" --repo \"${REPO}\""
  echo "  ${GH_CMD_DISPLAY} variable set GCP_SERVICE_ACCOUNT --body \"${SA_EMAIL}\" --repo \"${REPO}\""
  echo "  ${GH_CMD_DISPLAY} variable set TF_STATE_BUCKET --body \"${BUCKET_NAME}\" --repo \"${REPO}\""
fi

echo ""
echo "Done."
