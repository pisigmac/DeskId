#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — Audit Log Export Utility (export_audit_logs.sh)
# ==============================================================================
# Queries and exports security and audit logs from /v1/admin/audit into
# JSON or CSV format for SOC2 compliance and security auditing.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load environment configuration
if [ -f "${ROOT_DIR}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.env"
    set +a
fi

PORT="${AUTH_PORT:-8090}"
HOST="${AUTH_HOST:-}"
BASE_URL="${AUTH_ISSUER:-}"
if [ -z "${BASE_URL}" ] && [ -n "${HOST}" ]; then
    BASE_URL="http://${HOST}:${PORT}"
fi

OUTPUT_FILE=""
LIMIT=100
ACTION_FILTER=""
TOKEN="${AUTH_BEARER_TOKEN:-}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

usage() {
    echo -e "${BOLD}Usage:${NC} $0 --token <admin_jwt> [options]"
    echo ""
    echo "Options:"
    echo "  -t, --token <jwt>         Admin Bearer JWT token (or set AUTH_BEARER_TOKEN)"
    echo "  -o, --output <file>       Output file path (.json or .csv)"
    echo "  -l, --limit <n>           Max records to fetch (default: 100)"
    echo "  -a, --action <action>     Filter by action (e.g. user.login, admin.set_grant)"
    echo "  --help                    Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--token)
            TOKEN="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -l|--limit)
            LIMIT="$2"
            shift 2
            ;;
        -a|--action)
            ACTION_FILTER="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

if [ -z "${TOKEN}" ]; then
    echo -e "${RED}Error: Admin JWT token is required.${NC}"
    echo "Provide via -t/--token or AUTH_BEARER_TOKEN env variable."
    exit 1
fi

QUERY_URL="${BASE_URL}/v1/admin/audit?limit=${LIMIT}"
if [ -n "${ACTION_FILTER}" ]; then
    QUERY_URL="${QUERY_URL}&action=${ACTION_FILTER}"
fi

echo -e "${BLUE}Fetching audit logs from: ${QUERY_URL}...${NC}"

RESPONSE="$(curl -s -w "\n%{http_code}" -X GET "${QUERY_URL}" \
    -H "Authorization: Bearer ${TOKEN}")"

HTTP_CODE="$(echo "${RESPONSE}" | tail -n 1)"
BODY="$(echo "${RESPONSE}" | sed '$d')"

if [ "${HTTP_CODE}" -ne 200 ]; then
    echo -e "${RED}Failed to query audit logs (HTTP ${HTTP_CODE}):${NC}"
    echo "${BODY}"
    exit 1
fi

if [ -n "${OUTPUT_FILE}" ]; then
    echo "${BODY}" > "${OUTPUT_FILE}"
    echo -e "${GREEN}✓ Exported audit logs to: ${OUTPUT_FILE}${NC}"
else
    echo -e "${GREEN}✓ Audit Log Response:${NC}"
    echo "${BODY}"
fi
