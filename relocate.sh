#!/usr/bin/env bash
# ==============================================================================
# L200 Workspace Relocation & Activation Helper
# Run this script whenever the workspace directory is moved or extracted.
# ==============================================================================
set -e

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "==> Relocating workspace to: ${WORKSPACE_DIR}"

# 1. Update .env paths
if [ -f "${WORKSPACE_DIR}/.env" ]; then
  sed -i -E \
    -e "s|^CLOUDSDK_CONFIG=.*|CLOUDSDK_CONFIG=${WORKSPACE_DIR}/.gcloud|" \
    -e "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=${WORKSPACE_DIR}/.gcloud/application_default_credentials.json|" \
    -e "s|^PATH=.*|PATH=${WORKSPACE_DIR}/bin:\$PATH|" \
    -e "s|^UV_PYTHON_INSTALL_DIR=.*|UV_PYTHON_INSTALL_DIR=${WORKSPACE_DIR}/.python|" \
    "${WORKSPACE_DIR}/.env"
  echo "  ✓ Updated .env paths"
fi

# 2. Update .venv configuration if .venv exists
if [ -f "${WORKSPACE_DIR}/.venv/pyvenv.cfg" ]; then
  PYTHON_BIN_DIR="$(find "${WORKSPACE_DIR}/.python" -type d -name "bin" 2>/dev/null | head -n 1)"
  if [ -n "${PYTHON_BIN_DIR}" ]; then
    sed -i -E "s|^home = .*|home = ${PYTHON_BIN_DIR}|" "${WORKSPACE_DIR}/.venv/pyvenv.cfg"
  fi
  # Update VIRTUAL_ENV in activate script
  if [ -f "${WORKSPACE_DIR}/.venv/bin/activate" ]; then
    sed -i -E "s|^VIRTUAL_ENV=.*|VIRTUAL_ENV=\"${WORKSPACE_DIR}/.venv\"|" "${WORKSPACE_DIR}/.venv/bin/activate"
  fi
  # Fix shebangs in .venv/bin
  if [ -d "${WORKSPACE_DIR}/.venv/bin" ]; then
    find "${WORKSPACE_DIR}/.venv/bin" -maxdepth 1 -type f -exec sed -i -E "1s|^#!.*/\.venv/bin/python.*|#!${WORKSPACE_DIR}/.venv/bin/python|" {} + 2>/dev/null || true
  fi
  echo "  ✓ Relocated Python virtualenv (.venv/)"
fi

# 3. Verify environment
echo "==> Verifying environment..."
if [ -x "${WORKSPACE_DIR}/bin/uv" ]; then
  "${WORKSPACE_DIR}/bin/uv" run --env-file "${WORKSPACE_DIR}/.env" python "${WORKSPACE_DIR}/main.py"
fi

echo ""
echo "==> Workspace successfully relocated and verified!"
echo "To activate:"
echo "  source .env"
echo "  source .venv/bin/activate"
