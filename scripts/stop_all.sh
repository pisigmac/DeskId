#!/usr/bin/env bash
# ==============================================================================
# OpenDesk Auth — Service Shutdown Utility (stop_all.sh)
# ==============================================================================
# Gracefully stops all running OpenDesk Auth processes and Docker containers.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ANSI Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

PID_FILE="${ROOT_DIR}/.auth.pid"
STOPPED_ANY=false

echo -e "${BLUE}${BOLD}=== Stopping OpenDesk Auth Infrastructure ===${NC}"

# 1. Stop local background PID if tracked
if [ -f "${PID_FILE}" ]; then
    PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [ -n "${PID}" ] && kill -0 "${PID}" 2>/dev/null; then
        echo "Stopping Auth process (PID: ${PID})..."
        kill "${PID}" 2>/dev/null || true
        # Wait up to 5 seconds for graceful shutdown
        for _ in {1..10}; do
            if ! kill -0 "${PID}" 2>/dev/null; then
                break
            fi
            sleep 0.5
        done
        # Force kill if still alive
        if kill -0 "${PID}" 2>/dev/null; then
            echo -e "${YELLOW}Force terminating PID: ${PID}...${NC}"
            kill -9 "${PID}" 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ Local process ${PID} stopped.${NC}"
        STOPPED_ANY=true
    fi
    rm -f "${PID_FILE}"
fi

# 2. Search for any lingering uvicorn/opendesk_auth processes
LINGERING_PIDS=$(pgrep -f "opendesk_auth.app:app" 2>/dev/null || true)
if [ -n "${LINGERING_PIDS}" ]; then
    echo "Found lingering uvicorn processes (${LINGERING_PIDS}). Terminating..."
    for p in ${LINGERING_PIDS}; do
        kill "${p}" 2>/dev/null || true
    done
    sleep 1
    for p in ${LINGERING_PIDS}; do
        if kill -0 "${p}" 2>/dev/null; then
            kill -9 "${p}" 2>/dev/null || true
        fi
    done
    echo -e "${GREEN}✓ Lingering processes terminated.${NC}"
    STOPPED_ANY=true
fi

# 3. Stop Docker Compose containers if docker is running
if command -v docker >/dev/null 2>&1; then
    if [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
        CONTAINERS="$(docker compose -f "${ROOT_DIR}/docker-compose.yml" ps -q 2>/dev/null || true)"
        if [ -n "${CONTAINERS}" ]; then
            echo "Stopping Docker Compose containers..."
            docker compose -f "${ROOT_DIR}/docker-compose.yml" down 2>/dev/null || true
            echo -e "${GREEN}✓ Docker Compose containers stopped.${NC}"
            STOPPED_ANY=true
        fi
    fi
fi

if [ "${STOPPED_ANY}" = true ]; then
    echo -e "\n${GREEN}${BOLD}✓ All OpenDesk Auth services have been stopped successfully.${NC}"
else
    echo -e "\n${YELLOW}No active OpenDesk Auth processes or containers were found running.${NC}"
fi
