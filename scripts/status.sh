#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — Service Status & Diagnostics Dashboard (status.sh)
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

# Load environment configuration
if [ -f "${ROOT_DIR}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.env"
    set +a
fi

PORT="${AUTH_PORT:-8090}"
HOST="${AUTH_HOST:-}"
PID_FILE="${ROOT_DIR}/.auth.pid"
BASE_URL="${AUTH_ISSUER:-}"
if [ -z "${BASE_URL}" ] && [ -n "${HOST}" ]; then
    BASE_URL="http://${HOST}:${PORT}"
fi

echo -e "${BLUE}${BOLD}=== OpenDesk Auth Service Status & Diagnostics ===${NC}\n"

# 1. Process & Container Status
echo -e "${BOLD}[1] Process & Container Status:${NC}"
if [ -f "${PID_FILE}" ]; then
    PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [ -n "${PID}" ] && kill -0 "${PID}" 2>/dev/null; then
        echo -e "  Local Process:   ${GREEN}● RUNNING${NC} (PID: ${PID})"
    else
        echo -e "  Local Process:   ${RED}○ STOPPED${NC} (stale PID file)"
    fi
else
    LINGERING_PID="$(pgrep -f "deskid.app:app" 2>/dev/null | head -n 1 || true)"
    if [ -n "${LINGERING_PID}" ]; then
        echo -e "  Local Process:   ${GREEN}● RUNNING${NC} (PID: ${LINGERING_PID})"
    else
        echo -e "  Local Process:   ${YELLOW}○ NOT RUNNING${NC}"
    fi
fi

if command -v docker >/dev/null 2>&1 && [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
    DOCKER_STATUS="$(docker compose -f "${ROOT_DIR}/docker-compose.yml" ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true)"
    if [ -n "${DOCKER_STATUS}" ]; then
        echo -e "\n  Docker Compose Services:\n${DOCKER_STATUS}"
    fi
fi

# 2. Port Binding Check
echo -e "\n${BOLD}[2] Port Binding Check (Port ${PORT}):${NC}"
if command -v lsof >/dev/null 2>&1; then
    PORT_CHECK="$(lsof -i :${PORT} 2>/dev/null || true)"
    if [ -n "${PORT_CHECK}" ]; then
        echo -e "  Port ${PORT}: ${GREEN}LISTENING${NC}\n${PORT_CHECK}"
    else
        echo -e "  Port ${PORT}: ${YELLOW}NOT LISTENING${NC}"
    fi
elif command -v ss >/dev/null 2>&1; then
    if ss -tuln | grep -q ":${PORT} "; then
        echo -e "  Port ${PORT}: ${GREEN}LISTENING${NC}"
    else
        echo -e "  Port ${PORT}: ${YELLOW}NOT LISTENING${NC}"
    fi
fi

# 3. Healthcheck Endpoint
echo -e "\n${BOLD}[3] Deep Health Check (${BASE_URL}/health):${NC}"
HEALTH_RESP="$(curl -s -w "\n%{http_code}" "${BASE_URL}/health" 2>/dev/null || echo -e "{}\n000")"
HTTP_CODE="$(echo "${HEALTH_RESP}" | tail -n 1)"
HEALTH_BODY="$(echo "${HEALTH_RESP}" | sed '$d')"

if [ "${HTTP_CODE}" = "200" ]; then
    echo -e "  HTTP Status:     ${GREEN}200 OK${NC}"
    echo -e "  Health Payload:  ${CYAN}${HEALTH_BODY}${NC}"
else
    echo -e "  HTTP Status:     ${RED}${HTTP_CODE} (Unhealthy / Unreachable)${NC}"
fi

# 4. Rate Limiting Configuration & Distributed Backend Check
echo -e "\n${BOLD}[4] Rate Limiting Status:${NC}"
# Load env if present
if [ -f "${ROOT_DIR}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.env"
    set +a
fi

RL_ENABLED="${AUTH_RATE_LIMIT_ENABLED:-true}"
RL_BACKEND="${AUTH_RATE_LIMIT_BACKEND:-memory}"
RL_REDIS_URL="${AUTH_RATE_LIMIT_REDIS_URL:-}"

if [ "${RL_ENABLED}" = "true" ]; then
    echo -e "  Rate Limiting:   ${GREEN}● ENABLED${NC} (Backend: ${CYAN}${RL_BACKEND}${NC})"
else
    echo -e "  Rate Limiting:   ${YELLOW}○ DISABLED${NC} (Bypassed)"
fi

if [ "${RL_BACKEND}" = "redis" ]; then
    if [ -n "${RL_REDIS_URL}" ]; then
        if python3 -c "import redis; r = redis.Redis.from_url('${RL_REDIS_URL}', socket_timeout=1.0); r.ping()" 2>/dev/null; then
            echo -e "  Redis Server:    ${GREEN}● ONLINE & CONNECTED${NC} (${RL_REDIS_URL})"
        else
            echo -e "  Redis Server:    ${RED}✗ UNREACHABLE${NC} (${RL_REDIS_URL})"
        fi
    else
        echo -e "  Redis Server:    ${YELLOW}AUTH_RATE_LIMIT_REDIS_URL not set${NC}"
    fi
elif [ "${RL_BACKEND}" = "db" ]; then
    echo -e "  Storage Table:   ${CYAN}rate_limit_entries${NC} (Multi-worker synchronized)"
fi

# 5. Metrics Snapshot
echo -e "\n${BOLD}[5] Service Metrics (${BASE_URL}/metrics):${NC}"
METRICS_RESP="$(curl -s "${BASE_URL}/metrics" 2>/dev/null || echo "{}")"
echo -e "  Metrics:         ${CYAN}${METRICS_RESP}${NC}"

echo -e "\n--------------------------------------------------------"

