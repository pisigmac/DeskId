#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — Restart All Services Shortcut
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/scripts/restart_all.sh" "$@"
