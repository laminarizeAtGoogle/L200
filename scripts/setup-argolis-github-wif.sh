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
#   ./scripts/setup-argolis-github-wif.sh --project <PROJECT_ID> --repo <OWNER/REPO>
# ==============================================================================

set -euo pipefail

# Default configuration
PROJECT_ID="${PROJECT_ID:-${ARGOLIS_PROJECT_ID:-}}"
REPO=""
SA_NAME="github-terraform-deployer"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"
REGION="us-central1"
BUCKET_NAME=""
AUTO_DEPLOY_GH=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Provisions Workload Identity Federation (WIF) and Terraform remote state in Argolis.

Options:
  -p, --project PROJECT_ID     Target Argolis GCP project ID.
                               (Defaults to \$PROJECT_ID, \$ARGOLIS_PROJECT_ID, or active gcloud project)
  -r, --repo OWNER/REPO        GitHub repository (e.g. 'octocat/hello-world').
                               (Auto-detected from git remote if inside a repository)
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
  --auto-deploy-gh             Automatically set variables in GitHub via 'gh' CLI.
  --skip-gh                    Skip GitHub CLI variable deployment.
  -h, --help                   Display this help message and exit.

Example:
  $(basename "$0")
EOF
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project)
      PROJECT_ID="$2"
      shift 2
      ;;
    -r|--repo)
      REPO="$2"
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

# Validate Project ID
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "<YOUR_ARGOLIS_PROJECT_ID>" || "${PROJECT_ID}" == "<PROJECT_ID>" ]]; then
  # Discover active gcloud project as fallback (matches provision-argolis-env.sh)
  ACTIVE_GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
  if [[ -n "${ACTIVE_GCLOUD_PROJECT}" && "${ACTIVE_GCLOUD_PROJECT}" != "(unset)" ]]; then
    PROJECT_ID="${ACTIVE_GCLOUD_PROJECT}"
    echo "Notice: Discovered active gcloud project '${PROJECT_ID}'"
  else
    echo "Error: PROJECT_ID is required." >&2
    echo "Provide it with --project <PROJECT_ID>, export PROJECT_ID=<PROJECT_ID>, or set your active gcloud project." >&2
    exit 1
  fi
fi

# GCP project IDs must be strictly lowercase
if [[ "${PROJECT_ID}" =~ [A-Z] ]]; then
  ACTIVE_GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
  echo "Error: GCP Project ID '${PROJECT_ID}' contains uppercase letters, which are invalid in Google Cloud." >&2
  if [[ -n "${ACTIVE_GCLOUD_PROJECT}" && "${ACTIVE_GCLOUD_PROJECT}" != "(unset)" ]]; then
    echo "Hint: Your active gcloud project is '${ACTIVE_GCLOUD_PROJECT}'. Try running with:" >&2
    echo "  $(basename "$0") --project ${ACTIVE_GCLOUD_PROJECT} --repo ${REPO:-<OWNER/REPO>}" >&2
  fi
  exit 1
fi

# Validate Repo
if [[ -z "${REPO}" ]]; then
  # Try to detect git remote if run inside a repo
  if git remote get-url origin >/dev/null 2>&1; then
    DETECTED_REPO=$(git remote get-url origin | sed -E 's/.*github.com[:\/](.*)\.git$/\1/')
    if [[ -n "${DETECTED_REPO}" ]]; then
      echo "Notice: Auto-detected repository from git remote: '${DETECTED_REPO}'"
      REPO="${DETECTED_REPO}"
    fi
  fi

  if [[ -z "${REPO}" ]]; then
    echo "Error: --repo <OWNER/REPO> is required (e.g. --repo laminarizeAtGoogle/L200)." >&2
    usage
    exit 1
  fi
fi

# ------------------------------------------------------------------------------
# GitHub CLI Authentication Check & Configuration Choice
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
  if ! command -v gh >/dev/null 2>&1; then
    echo "Notice: GitHub CLI ('gh') is not installed. Variables will be output for manual entry."
    AUTO_DEPLOY_GH="false"
  else
    echo "Checking GitHub CLI ('gh') authentication status..."
    if gh auth status --hostname github.com >/dev/null 2>&1; then
      GH_USER=$(gh api user -q .login 2>/dev/null || echo "authenticated user")
      echo "✓ GitHub CLI is already authenticated as '${GH_USER}'."
    else
      echo "Notice: You are not currently authenticated to GitHub in this terminal session."
      if [[ -t 0 ]]; then
        read -r -p "Would you like to log in now using 'gh auth login'? [Y/n]: " LOGIN_CHOICE
        LOGIN_CHOICE="${LOGIN_CHOICE:-Y}"
        if [[ "${LOGIN_CHOICE}" =~ ^[Yy]$ ]]; then
          echo "Launching 'gh auth login'..."
          gh auth login
          if gh auth status --hostname github.com >/dev/null 2>&1; then
            GH_USER=$(gh api user -q .login 2>/dev/null || echo "authenticated user")
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
  fi
fi

if [[ -z "${BUCKET_NAME}" ]]; then
  BUCKET_NAME="${PROJECT_ID}-tfstate"
fi

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

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
  ACTIVE_GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
  if [[ -n "${ACTIVE_GCLOUD_PROJECT}" && "${ACTIVE_GCLOUD_PROJECT}" != "(unset)" && "${ACTIVE_GCLOUD_PROJECT}" != "${PROJECT_ID}" ]]; then
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

# 6. Create Workload Identity Provider
echo "==> [6/7] Configuring Workload Identity Provider..."
if gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
  --location="global" \
  --workload-identity-pool="${POOL_NAME}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "    Workload Identity Provider '${PROVIDER_NAME}' already exists."
else
  echo "    Creating OIDC Provider '${PROVIDER_NAME}' with repository condition..."
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_NAME}" \
    --location="global" \
    --workload-identity-pool="${POOL_NAME}" \
    --display-name="GitHub Actions OIDC Provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.repository == '${REPO}'" \
    --project="${PROJECT_ID}"
fi

# 7. Grant GitHub Repository Access to Impersonate Service Account
echo "==> [7/7] Authorizing GitHub repository to impersonate Service Account..."
WIF_MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${REPO}"

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
if [[ "${AUTO_DEPLOY_GH}" == "true" ]]; then
  echo ""
  echo "==> Deploying variables to GitHub repository '${REPO}' via GitHub CLI..."
  gh variable set GCP_PROJECT_ID --body "${PROJECT_ID}" --repo "${REPO}"
  echo "    ✓ Set GCP_PROJECT_ID=${PROJECT_ID}"
  gh variable set GCP_WORKLOAD_IDENTITY_PROVIDER --body "${WIF_PROVIDER_FULL}" --repo "${REPO}"
  echo "    ✓ Set GCP_WORKLOAD_IDENTITY_PROVIDER"
  gh variable set GCP_SERVICE_ACCOUNT --body "${SA_EMAIL}" --repo "${REPO}"
  echo "    ✓ Set GCP_SERVICE_ACCOUNT=${SA_EMAIL}"
  gh variable set TF_STATE_BUCKET --body "${BUCKET_NAME}" --repo "${REPO}"
  echo "    ✓ Set TF_STATE_BUCKET=${BUCKET_NAME}"
  echo ""
  echo "✓ All 4 variables successfully configured in GitHub repository '${REPO}'!"
  echo "You can verify them at: https://github.com/${REPO}/settings/variables/actions"
else
  echo ""
  echo "Configure these GitHub Variables or Secrets manually in:"
  echo "https://github.com/${REPO}/settings/secrets/actions"
  echo ""
  echo "Tip: You can set these automatically using the GitHub CLI if authenticated:"
  echo ""
  echo "  gh variable set GCP_PROJECT_ID --body \"${PROJECT_ID}\" --repo \"${REPO}\""
  echo "  gh variable set GCP_WORKLOAD_IDENTITY_PROVIDER --body \"${WIF_PROVIDER_FULL}\" --repo \"${REPO}\""
  echo "  gh variable set GCP_SERVICE_ACCOUNT --body \"${SA_EMAIL}\" --repo \"${REPO}\""
  echo "  gh variable set TF_STATE_BUCKET --body \"${BUCKET_NAME}\" --repo \"${REPO}\""
fi

echo ""
echo "Done."
