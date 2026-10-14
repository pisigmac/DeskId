#!/usr/bin/env bash
# ==============================================================================
# DeskID — Service Shutdown Utility (stop_all.sh)
# ==============================================================================
# Gracefully stops all running DeskID backend processes, frontend dev servers,
# and Docker containers.
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
FRONTEND_PID_FILE="${ROOT_DIR}/.frontend.pid"
STOPPED_ANY=false

echo -e "${BLUE}${BOLD}=== Stopping DeskID Infrastructure ===${NC}"

# 1. Stop local backend PID if tracked
if [ -f "${PID_FILE}" ]; then
    PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [ -n "${PID}" ] && kill -0 "${PID}" 2>/dev/null; then
        echo "Stopping Auth backend process (PID: ${PID})..."
        kill "${PID}" 2>/dev/null || true
        for _ in {1..10}; do
            if ! kill -0 "${PID}" 2>/dev/null; then
                break
            fi
            sleep 0.5
        done
        if kill -0 "${PID}" 2>/dev/null; then
            echo -e "${YELLOW}Force terminating PID: ${PID}...${NC}"
            kill -9 "${PID}" 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ Local backend process ${PID} stopped.${NC}"
        STOPPED_ANY=true
    fi
    rm -f "${PID_FILE}"
fi

# 2. Stop frontend dev server PID if tracked
if [ -f "${FRONTEND_PID_FILE}" ]; then
    FPID="$(cat "${FRONTEND_PID_FILE}" 2>/dev/null || true)"
    if [ -n "${FPID}" ] && kill -0 "${FPID}" 2>/dev/null; then
        echo "Stopping Frontend dev server process (PID: ${FPID})..."
        kill "${FPID}" 2>/dev/null || true
        sleep 0.5
        if kill -0 "${FPID}" 2>/dev/null; then
            kill -9 "${FPID}" 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ Frontend dev process ${FPID} stopped.${NC}"
        STOPPED_ANY=true
    fi
    rm -f "${FRONTEND_PID_FILE}"
fi

# 3. Search for any lingering uvicorn/deskid/vite processes
LINGERING_BACKEND=$(pgrep -f "deskid.app:app" 2>/dev/null || true)
if [ -n "${LINGERING_BACKEND}" ]; then
    echo "Found lingering backend processes (${LINGERING_BACKEND}). Terminating..."
    for p in ${LINGERING_BACKEND}; do
        kill "${p}" 2>/dev/null || true
    done
    sleep 1
    for p in ${LINGERING_BACKEND}; do
        if kill -0 "${p}" 2>/dev/null; then
            kill -9 "${p}" 2>/dev/null || true
        fi
    done
    echo -e "${GREEN}✓ Lingering backend processes terminated.${NC}"
    STOPPED_ANY=true
fi

LINGERING_FRONTEND=$(pgrep -f "vite" 2>/dev/null || true)
if [ -n "${LINGERING_FRONTEND}" ]; then
    echo "Found lingering frontend Vite processes (${LINGERING_FRONTEND}). Terminating..."
    for p in ${LINGERING_FRONTEND}; do
        kill "${p}" 2>/dev/null || true
    done
    echo -e "${GREEN}✓ Lingering frontend processes terminated.${NC}"
    STOPPED_ANY=true
fi

# 4. Stop Docker Compose containers if docker is running
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
    echo -e "\n${GREEN}${BOLD}✓ All DeskID services have been stopped successfully.${NC}"
else
    echo -e "\n${YELLOW}No active DeskID processes or containers were found running.${NC}"
fi
