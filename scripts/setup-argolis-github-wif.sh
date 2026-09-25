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

usage() {
  cat <<EOF
Usage: $(basename "$0") -p <PROJECT_ID> -r <OWNER/REPO> [OPTIONS]

Provisions Workload Identity Federation (WIF) and Terraform remote state in Argolis.

Required Options:
  -p, --project PROJECT_ID     Target Argolis GCP project ID.
  -r, --repo OWNER/REPO        GitHub repository (e.g. 'octocat/hello-world').

Optional Options:
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
  -h, --help                   Display this help message and exit.

Example:
  $(basename "$0") -p argolis-sandbox-1234 -r laminarizeAtGoogle/L200
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
if [[ -z "${PROJECT_ID}" ]]; then
  # Try to read active gcloud project as fallback
  ACTIVE_GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
  if [[ -n "${ACTIVE_GCLOUD_PROJECT}" && "${ACTIVE_GCLOUD_PROJECT}" != "(unset)" ]]; then
    PROJECT_ID="${ACTIVE_GCLOUD_PROJECT}"
    echo "Notice: Using active gcloud project '${PROJECT_ID}'"
  else
    echo "Error: --project <PROJECT_ID> is required." >&2
    usage
    exit 1
  fi
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
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
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
  echo "    Creating OIDC Provider '${PROVIDER_NAME}'..."
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_NAME}" \
    --location="global" \
    --workload-identity-pool="${POOL_NAME}" \
    --display-name="GitHub Actions OIDC Provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
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
echo ""
echo "Tip: You can set these automatically using the GitHub CLI if authenticated:"
echo ""
echo "  gh variable set GCP_PROJECT_ID --body \"${PROJECT_ID}\" --repo \"${REPO}\""
echo "  gh variable set GCP_WORKLOAD_IDENTITY_PROVIDER --body \"${WIF_PROVIDER_FULL}\" --repo \"${REPO}\""
echo "  gh variable set GCP_SERVICE_ACCOUNT --body \"${SA_EMAIL}\" --repo \"${REPO}\""
echo "  gh variable set TF_STATE_BUCKET --body \"${BUCKET_NAME}\" --repo \"${REPO}\""
echo ""
echo "Done."
