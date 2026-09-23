#!/usr/bin/env bash
# ==============================================================================
# DeskID — Migration Runner Wrapper
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load .env if present and AUTH_DATABASE_URL not explicitly set
if [ -z "${AUTH_DATABASE_URL:-}" ] && [ -f "${ROOT_DIR}/.env" ]; then
    # export non-comment lines
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.env"
    set +a
fi

export AUTH_DATABASE_URL="${AUTH_DATABASE_URL:-postgresql+psycopg://auth:auth@localhost:5433/auth}"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

echo "Running migrations against: ${AUTH_DATABASE_URL}"
python3 "${ROOT_DIR}/migrations/run_migrations.py"
echo "Migrations completed."
