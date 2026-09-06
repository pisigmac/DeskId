#!/usr/bin/env bash
# ==============================================================================
# DeskID — Service Startup Utility (start_all.sh)
# ==============================================================================
# Starts all required DeskID services (database, migrations, auth server).
# Supports both Local Python/SQLite mode and Docker Compose mode.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ANSI Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 1. Environment & Keys Validation
if [ ! -f "${ROOT_DIR}/.env" ] && [ -f "${ROOT_DIR}/.env.example" ]; then
    echo -e "${YELLOW}Notice: .env not found. Creating from .env.example...${NC}"
    cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
fi

if [ -f "${ROOT_DIR}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.env"
    set +a
fi

# Default configurations from environment / config file
MODE="auto" # auto | local | docker
RUN_FOREGROUND=false
PORT="${AUTH_PORT:-}"
HOST="${AUTH_HOST:-}"
RATE_LIMIT_ENABLED_OVERRIDE=""
RATE_LIMIT_BACKEND_OVERRIDE=""
REDIS_URL_OVERRIDE=""
PID_FILE="${ROOT_DIR}/.auth.pid"
LOG_FILE="${ROOT_DIR}/auth_service.log"

usage() {
    echo -e "${BOLD}Usage:${NC} $0 [options]"
    echo ""
    echo "Options:"
    echo "  -m, --mode <local|docker>             Execution mode (default: auto-detect)"
    echo "  -f, --foreground                      Run server in foreground (default: background daemon)"
    echo "  -p, --port <port>                     Override HTTP port (from AUTH_PORT in config)"
    echo "  -h, --host <host>                     Override HTTP host (from AUTH_HOST in config)"
    echo "  --rate-limit-backend <memory|db|redis> Storage backend for rate limiting"
    echo "  --rate-limit-enabled <true|false>     Enable/disable rate limiting"
    echo "  --redis-url <url>                     Redis connection URL"
    echo "  --help                                Show this help message"
    exit 0
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -f|--foreground)
            RUN_FOREGROUND=true
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        --rate-limit-backend)
            RATE_LIMIT_BACKEND_OVERRIDE="$2"
            shift 2
            ;;
        --rate-limit-enabled)
            RATE_LIMIT_ENABLED_OVERRIDE="$2"
            shift 2
            ;;
        --redis-url)
            REDIS_URL_OVERRIDE="$2"
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

if [ -z "${HOST}" ] || [ -z "${PORT}" ]; then
    echo -e "${RED}Error: AUTH_HOST and AUTH_PORT must be defined in .env or passed via --host / --port.${NC}"
    exit 1
fi

echo -e "${BLUE}${BOLD}======================================================${NC}"
echo -e "${BLUE}${BOLD}        🚀 Starting DeskID Infrastructure       ${NC}"
echo -e "${BLUE}${BOLD}======================================================${NC}"

# Ensure RSA Keys exist
if [ ! -f "${ROOT_DIR}/private.pem" ] || [ ! -f "${ROOT_DIR}/public.pem" ]; then
    echo -e "${YELLOW}RSA keys missing. Generating new RSA 2048-bit keypair...${NC}"
    bash "${SCRIPT_DIR}/generate_keys.sh" "${ROOT_DIR}/private.pem" "${ROOT_DIR}/public.pem"
fi

# Export required environment variables from config
export AUTH_HOST="${HOST}"
export AUTH_PORT="${PORT}"
export AUTH_DATABASE_URL="${AUTH_DATABASE_URL:-sqlite:///${ROOT_DIR}/auth.db}"
export AUTH_ISSUER="${AUTH_ISSUER:-}"
export AUTH_JWT_PRIVATE_KEY_FILE="${AUTH_JWT_PRIVATE_KEY_FILE:-${ROOT_DIR}/private.pem}"
export AUTH_JWT_PUBLIC_KEY_FILE="${AUTH_JWT_PUBLIC_KEY_FILE:-${ROOT_DIR}/public.pem}"
export AUTH_OPEN_REGISTRATION="${AUTH_OPEN_REGISTRATION:-true}"
export AUTH_CORS_ORIGINS="${AUTH_CORS_ORIGINS:-}"
export AUTH_SPA_CALLBACK_URL="${AUTH_SPA_CALLBACK_URL:-}"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

if [ -n "${RATE_LIMIT_ENABLED_OVERRIDE}" ]; then
    export AUTH_RATE_LIMIT_ENABLED="${RATE_LIMIT_ENABLED_OVERRIDE}"
fi
if [ -n "${RATE_LIMIT_BACKEND_OVERRIDE}" ]; then
    export AUTH_RATE_LIMIT_BACKEND="${RATE_LIMIT_BACKEND_OVERRIDE}"
fi
if [ -n "${REDIS_URL_OVERRIDE}" ]; then
    export AUTH_RATE_LIMIT_REDIS_URL="${REDIS_URL_OVERRIDE}"
fi

# Determine mode if auto
if [ "${MODE}" = "auto" ]; then
    if [ -n "${AUTH_DATABASE_URL:-}" ] && [[ "${AUTH_DATABASE_URL}" == *"postgres"* ]] && command -v docker >/dev/null 2>&1; then
        MODE="docker"
    else
        MODE="local"
    fi
fi

RL_EFF_ENABLED="${AUTH_RATE_LIMIT_ENABLED:-true}"
RL_EFF_BACKEND="${AUTH_RATE_LIMIT_BACKEND:-memory}"

echo -e "Mode: ${CYAN}${BOLD}${MODE}${NC}"
echo -e "Target Database: ${CYAN}${AUTH_DATABASE_URL}${NC}"
echo -e "Target Port: ${CYAN}${PORT}${NC}"
echo -e "Rate Limiting: ${CYAN}${RL_EFF_ENABLED}${NC} (Backend: ${CYAN}${RL_EFF_BACKEND}${NC})"

# 2. Start Services
if [ "${MODE}" = "docker" ]; then
    echo -e "\n${BLUE}Starting Docker Compose environment...${NC}"
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${RED}Error: docker is not installed or not in PATH.${NC}"
        exit 1
    fi
    docker compose -f "${ROOT_DIR}/docker-compose.yml" up -d
    echo -e "${GREEN}✓ Docker containers started.${NC}"
else
    # Check if already running on the port
    if [ -f "${PID_FILE}" ]; then
        EXISTING_PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
        if [ -n "${EXISTING_PID}" ] && kill -0 "${EXISTING_PID}" 2>/dev/null; then
            echo -e "${YELLOW}Warning: DeskID is already running (PID: ${EXISTING_PID}).${NC}"
            echo -e "Use ${BOLD}./stop_all.sh${NC} or ${BOLD}./restart_all.sh${NC} to restart."
            exit 0
        fi
    fi

    # Run Database Migrations
    echo -e "\n${BLUE}Applying database schema & migrations...${NC}"
    bash "${SCRIPT_DIR}/run_migrations.sh" >/dev/null 2>&1 || python3 "${ROOT_DIR}/migrations/run_migrations.py"
    echo -e "${GREEN}✓ Database initialized and migrated.${NC}"

    echo -e "\n${BLUE}Starting DeskID service process...${NC}"
    if [ "${RUN_FOREGROUND}" = true ]; then
        exec python3 -m uvicorn deskid.app:app --host "${HOST}" --port "${PORT}"
    else
        setsid python3 -m uvicorn deskid.app:app --host "${HOST}" --port "${PORT}" >> "${LOG_FILE}" 2>&1 < /dev/null &
        SERVER_PID=$!
        echo "${SERVER_PID}" > "${PID_FILE}"
        echo -e "${GREEN}✓ Process launched in background (PID: ${SERVER_PID}).${NC}"
        echo -e "  Logs: ${LOG_FILE}"
    fi
fi

# 3. Healthcheck polling
echo -e "\n${BLUE}Waiting for service to be healthy...${NC}"
HEALTH_URL="http://${HOST}:${PORT}/health"
MAX_ATTEMPTS=25
ATTEMPT=0
READY=false

while [ ${ATTEMPT} -lt ${MAX_ATTEMPTS} ]; do
    ATTEMPT=$((ATTEMPT + 1))
    HTTP_STATUS="$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" 2>/dev/null || echo "000")"
    if [ "${HTTP_STATUS}" = "200" ]; then
        READY=true
        break
    fi
    sleep 0.4
done

if [ "${READY}" = true ]; then
    echo -e "${GREEN}${BOLD}✓ Service is healthy and ready!${NC}\n"
    echo -e "${BOLD}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}│                   Active Service Endpoints                  │${NC}"
    echo -e "${BOLD}├─────────────────────────────────────────────────────────────┤${NC}"
    echo -e "│  ${CYAN}Public Auth UI:${NC}    http://${HOST}:${PORT}/auth"
    echo -e "│  ${CYAN}Admin Console:${NC}     http://${HOST}:${PORT}/admin/console"
    echo -e "│  ${CYAN}Developer Home:${NC}    http://${HOST}:${PORT}/"
    echo -e "│  ${CYAN}OpenAPI Docs:${NC}      http://${HOST}:${PORT}/docs"
    echo -e "│  ${CYAN}Health Check:${NC}      http://${HOST}:${PORT}/health"
    echo -e "│  ${CYAN}JWKS Endpoint:${NC}     http://${HOST}:${PORT}/.well-known/jwks.json"
    echo -e "${BOLD}└─────────────────────────────────────────────────────────────┘${NC}"
    echo -e "\nTo check service status:  ${BOLD}./scripts/status.sh${NC}"
    echo -e "To stop all services:     ${BOLD}./scripts/stop_all.sh${NC}"
else
    echo -e "${RED}Error: Service did not respond with HTTP 200 within timeout.${NC}"
    if [ -f "${LOG_FILE}" ]; then
        echo -e "${YELLOW}Recent log output:${NC}"
        tail -n 20 "${LOG_FILE}"
    fi
    exit 1
fi
