#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — JWT Token Generator & Verification CLI
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/scripts/jwt_tool.sh" "$@"
