#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — JWT Token Generator & Verification CLI
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

python3 "${SCRIPT_DIR}/jwt_tool.py" "$@"
