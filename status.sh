#!/usr/bin/env bash
# ==============================================================================
# DeskID — Service Status & Diagnostics Shortcut
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/scripts/status.sh" "$@"
