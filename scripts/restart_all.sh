#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — Service Restart Utility (restart_all.sh)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Restarting OpenDesk Auth services..."
bash "${SCRIPT_DIR}/stop_all.sh"
sleep 1
bash "${SCRIPT_DIR}/start_all.sh" "$@"
