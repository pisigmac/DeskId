#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — Admin Bootstrap & User Seeding Utility (seed_admin.sh)
# ==============================================================================
# Registers the initial platform administrator account and verifies login.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

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

ADMIN_EMAIL=""
ADMIN_PASSWORD=""
BOOTSTRAP_TOKEN=""

usage() {
    echo -e "${BOLD}Usage:${NC} $0 [options]"
    echo ""
    echo "Options:"
    echo "  -e, --email <email>       Admin email (default: prompts if not given)"
    echo "  -p, --password <password> Admin password (min 8 chars)"
    echo "  -t, --token <token>       Bootstrap token (if registration is closed)"
    echo "  --help                    Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -e|--email)
            ADMIN_EMAIL="$2"
            shift 2
            ;;
        -p|--password)
            ADMIN_PASSWORD="$2"
            shift 2
            ;;
        -t|--token)
            BOOTSTRAP_TOKEN="$2"
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

# Check if server is running
if ! curl -s "${BASE_URL}/health" >/dev/null 2>&1; then
    echo -e "${RED}Error: OpenDesk Auth service is not responding at ${BASE_URL}.${NC}"
    echo "Please start the service first using ./start_all.sh"
    exit 1
fi

echo -e "${BLUE}${BOLD}=== OpenDesk Auth Platform Admin Setup ===${NC}\n"

# Prompt for values if not passed
if [ -z "${ADMIN_EMAIL}" ]; then
    read -rp "Enter Admin Email: " ADMIN_EMAIL
    if [ -z "${ADMIN_EMAIL}" ]; then
        echo -e "${RED}Error: Admin email is required.${NC}"
        exit 1
    fi
fi

if [ -z "${ADMIN_PASSWORD}" ]; then
    read -rsp "Enter Admin Password (min 8 chars): " ADMIN_PASSWORD
    echo ""
    if [ ${#ADMIN_PASSWORD} -lt 8 ]; then
        echo -e "${RED}Error: Password must be at least 8 characters.${NC}"
        exit 1
    fi
fi

# Construct JSON payload
PAYLOAD="{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\""
if [ -n "${BOOTSTRAP_TOKEN}" ]; then
    PAYLOAD="${PAYLOAD},\"bootstrap_token\":\"${BOOTSTRAP_TOKEN}\""
elif [ -n "${AUTH_BOOTSTRAP_TOKEN:-}" ]; then
    PAYLOAD="${PAYLOAD},\"bootstrap_token\":\"${AUTH_BOOTSTRAP_TOKEN}\""
fi
PAYLOAD="${PAYLOAD}}"

echo -e "Attempting registration for ${CYAN}${ADMIN_EMAIL}${NC}..."
REG_RESP="$(curl -s -X POST "${BASE_URL}/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}")"

if echo "${REG_RESP}" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Admin account registered successfully!${NC}"
elif echo "${REG_RESP}" | grep -q "verification_required"; then
    echo -e "${YELLOW}Notice: Email verification is required by server policy.${NC}"
    # Auto-verify local dev SQLite database
    if [ -f "${ROOT_DIR}/auth.db" ] && command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "${ROOT_DIR}/auth.db" "UPDATE users SET email_verified_at = CURRENT_TIMESTAMP WHERE email = '${ADMIN_EMAIL}';" 2>/dev/null || true
        echo -e "${GREEN}✓ Auto-verified admin email in local database.${NC}"
    fi
elif echo "${REG_RESP}" | grep -q "Email already registered"; then
    echo -e "${YELLOW}Notice: Account already exists. Attempting login verification...${NC}"
else
    echo -e "${RED}Registration failed: ${REG_RESP}${NC}"
fi

# Verify Login & Admin Status
echo -e "\nVerifying login credentials..."
LOGIN_RESP="$(curl -s -X POST "${BASE_URL}/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")"

ACCESS_TOKEN="$(echo "${LOGIN_RESP}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4 || true)"

if [ -z "${ACCESS_TOKEN}" ] && [ -f "${ROOT_DIR}/auth.db" ] && command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "${ROOT_DIR}/auth.db" "UPDATE users SET email_verified_at = CURRENT_TIMESTAMP WHERE email = '${ADMIN_EMAIL}';" 2>/dev/null || true
    LOGIN_RESP="$(curl -s -X POST "${BASE_URL}/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")"
    ACCESS_TOKEN="$(echo "${LOGIN_RESP}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4 || true)"
fi

if [ -n "${ACCESS_TOKEN}" ]; then
    echo -e "${GREEN}✓ Login successful!${NC}"
    
    ME_RESP="$(curl -s -X GET "${BASE_URL}/v1/auth/me" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")"
    
    echo -e "\n${BOLD}User Profile & Admin Status:${NC}"
    echo -e "${CYAN}${ME_RESP}${NC}"
    
    echo -e "\n${GREEN}${BOLD}You can now log into the Admin Console at:${NC}"
    echo -e "${CYAN}http://${HOST}:${PORT}/admin/console${NC}"
    echo -e "JWT Access Token: ${ACCESS_TOKEN:0:30}..."
else
    echo -e "${RED}Login verification failed: ${LOGIN_RESP}${NC}"
    exit 1
fi
