#!/usr/bin/env bash
# ==============================================================================
# Argolis GCP Zero-Privilege Security Boundary Provisioning Script
#
# PURPOSE:
#   Establishes a hard security boundary at the IAM layer so that the local
#   development agent / workstation identity is physically incapable of
#   escalating to admin or performing unauthorized write operations.
#
# PATTERN:
#   Zero-Privilege Base Identity (joshholtz@gcp.altostrat.com)
#   - User identity holds NO direct owner/editor/creator roles.
#   - User identity has permissions ONLY to assume (impersonate) the read-only SA.
#   - Service Account (cloudtop-agent-reader) holds strictly read-only org roles.
#
# EXECUTION:
#   Run this script as Super Admin (e.g., admin@joshholtz.altostrat.com)
#   from Google Cloud Shell or an admin terminal session.
# ==============================================================================

set -euo pipefail

# Default configuration (can be overridden via CLI flags or environment variables)
PROJECT_ID="${PROJECT_ID:-${ARGOLIS_PROJECT_ID:-}}"
USER_IDENTITY="${USER_IDENTITY:-joshholtz@gcp.altostrat.com}"
SA_NAME="${SA_NAME:-cloudtop-agent-reader}"
ORG_ID="${ORG_ID:-}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Provisions the Zero-Privilege IAM boundary in an Argolis GCP environment.

Options:
  -p, --project PROJECT_ID     Target GCP project ID for hosting the Service Account.
                               (Defaults to \$PROJECT_ID or \$ARGOLIS_PROJECT_ID)
  -u, --user USER_IDENTITY     Developer user email to restrict.
                               (Default: ${USER_IDENTITY})
  -s, --sa-name SA_NAME        Name of the read-only Service Account to create.
                               (Default: ${SA_NAME})
  -o, --org-id ORG_ID          Argolis Organization ID (auto-discovered if omitted).
  -h, --help                   Display this help message and exit.

Example:
  $(basename "$0") --project argolis-dev-sandbox-1234
EOF
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project)
      PROJECT_ID="$2"
      shift 2
      ;;
    -u|--user)
      USER_IDENTITY="$2"
      shift 2
      ;;
    -s|--sa-name)
      SA_NAME="$2"
      shift 2
      ;;
    -o|--org-id)
      ORG_ID="$2"
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
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "<YOUR_BOOTSTRAP_OR_MANAGEMENT_PROJECT_ID>" ]]; then
  # Try to read active gcloud project as fallback
  ACTIVE_GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
  if [[ -n "${ACTIVE_GCLOUD_PROJECT}" && "${ACTIVE_GCLOUD_PROJECT}" != "(unset)" ]]; then
    PROJECT_ID="${ACTIVE_GCLOUD_PROJECT}"
    echo "Notice: Using active gcloud project '${PROJECT_ID}'"
  else
    echo "Error: PROJECT_ID is required." >&2
    echo "Provide it with --project <PROJECT_ID> or export PROJECT_ID=<PROJECT_ID>" >&2
    exit 1
  fi
fi

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "================================================================="
echo "Argolis Zero-Privilege IAM Security Boundary Provisioner"
echo "================================================================="
echo "Target Project ID: ${PROJECT_ID}"
echo "User Identity:     ${USER_IDENTITY}"
echo "Service Account:   ${SA_EMAIL}"
echo "================================================================="

# Step 1: Discover / Validate Organization ID
echo "==> 1. Discovering Argolis Organization..."
if [[ -z "${ORG_ID}" ]]; then
  ORG_ID=$(gcloud organizations list --format="value(ID)" 2>/dev/null | head -n 1 || true)
  if [[ -z "${ORG_ID}" ]]; then
    ORG_ID=$(gcloud organizations list --format="value(name)" 2>/dev/null | head -n 1 || true)
  fi
fi

# Clean "organizations/" prefix if returned
ORG_ID="${ORG_ID#organizations/}"

if [[ -z "${ORG_ID}" ]]; then
  echo "Error: Unable to auto-discover Organization ID. Please ensure your active account has org permissions or pass --org-id <ID>." >&2
  exit 1
fi
echo "Discovered Organization ID: ${ORG_ID}"

# Step 2: Ensure required APIs are enabled
echo "==> 2. Ensuring required APIs are enabled in project ${PROJECT_ID}..."
gcloud services enable \
  iamcredentials.googleapis.com \
  cloudasset.googleapis.com \
  --project="${PROJECT_ID}" \
  --quiet

# Step 3: Create Read-Only Service Account
echo "==> 3. Creating Read-Only Service Account (${SA_NAME})..."
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${PROJECT_ID}" \
    --display-name="Cloudtop Dev Agent Reader"
  echo "Service account ${SA_NAME} created."
else
  echo "Service account ${SA_NAME} already exists. Skipping creation."
fi

# Step 4: Bind Read-Only roles to the Service Account at the Org level
echo "==> 4. Binding Read-Only roles to the Service Account at the Org level..."
RO_ROLES=(
  "roles/viewer"
  "roles/browser"
  "roles/iam.securityReviewer"
  "roles/cloudasset.viewer"
)

for role in "${RO_ROLES[@]}"; do
  echo "  - Adding ${role} to serviceAccount:${SA_EMAIL} on Org ${ORG_ID}..."
  gcloud organizations add-iam-policy-binding "${ORG_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${role}" \
    --quiet > /dev/null
done

# Step 5: Grant token creation ONLY on this specific Service Account to USER_IDENTITY
echo "==> 5. Granting token creation ONLY on this specific Service Account to ${USER_IDENTITY}..."
# Bound strictly to the SA resource, NOT org-wide or project-wide
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --member="user:${USER_IDENTITY}" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --quiet > /dev/null

# Step 6: Ensuring USER_IDENTITY has NO direct high-privilege permissions at Org level
echo "==> 6. Ensuring ${USER_IDENTITY} has NO direct write/admin permissions at Org level..."
STRIP_ROLES=(
  "roles/editor"
  "roles/owner"
  "roles/resourcemanager.projectCreator"
)

for role in "${STRIP_ROLES[@]}"; do
  echo "  - Removing ${role} from user:${USER_IDENTITY} on Org ${ORG_ID} (if present)..."
  gcloud organizations remove-iam-policy-binding "${ORG_ID}" \
    --member="user:${USER_IDENTITY}" \
    --role="${role}" \
    --quiet > /dev/null 2>&1 || true
done

echo ""
echo "================================================================="
echo "✅ Hard-bounded Read-Only identity configured successfully!"
echo "================================================================="
echo ""
echo "NEXT STEPS ON CLOUDTOP WORKSTATION:"
echo "1. Log into Cloudtop as '${USER_IDENTITY}'"
echo "2. Configure gcloud to impersonate the read-only Service Account:"
echo "   gcloud config set auth/impersonate_service_account ${SA_EMAIL}"
echo ""
echo "3. For Application Default Credentials (ADC):"
echo "   gcloud auth application-default login"
echo ""
echo "PRIVILEGED TERRAFORM APPLIES:"
echo "• Execute terraform apply in Google Cloud Shell authenticated as your Super Admin"
echo "  (e.g., admin@joshholtz.altostrat.com). Your local Cloudtop never stores admin tokens."
echo "================================================================="

