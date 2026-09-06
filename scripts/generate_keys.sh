#!/usr/bin/env bash
# ==============================================================================
# DeskID — RSA Key & Secret Generator
# ==============================================================================
# Generates 2048-bit RSA private and public key PEM files required for
# token signing and JWKS verification, plus random bootstrap/introspection keys.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

PRIV_KEY="${1:-${ROOT_DIR}/private.pem}"
PUB_KEY="${2:-${ROOT_DIR}/public.pem}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}=== DeskID Key & Secret Generator ===${NC}"

if ! command -v openssl >/dev/null 2>&1; then
    echo -e "${YELLOW}Error: openssl command not found. Please install OpenSSL.${NC}"
    exit 1
fi

# 1. RSA Private & Public Keys
if [ -f "${PRIV_KEY}" ] && [ -f "${PUB_KEY}" ]; then
    echo -e "${GREEN}✓ Existing RSA keys found:${NC}"
    echo "  Private: ${PRIV_KEY}"
    echo "  Public:  ${PUB_KEY}"
else
    echo "Generating 2048-bit RSA keypair..."
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "${PRIV_KEY}"
    chmod 600 "${PRIV_KEY}"
    openssl rsa -in "${PRIV_KEY}" -pubout -out "${PUB_KEY}"
    chmod 644 "${PUB_KEY}"
    echo -e "${GREEN}✓ RSA Keys generated successfully!${NC}"
    echo "  Private: ${PRIV_KEY}"
    echo "  Public:  ${PUB_KEY}"
fi

# 2. Verify Key Pair
if openssl rsa -in "${PRIV_KEY}" -check -noout >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Key pair validation: OK${NC}"
else
    echo -e "${YELLOW}Warning: Key pair validation failed.${NC}"
fi

# 3. Generate Random Secrets for Reference
BOOTSTRAP_TOKEN="$(openssl rand -hex 32)"
INTROSPECT_KEY="$(openssl rand -hex 32)"

echo -e "\n${BLUE}${BOLD}=== Generated Secure Tokens (Optional Reference) ===${NC}"
echo -e "AUTH_BOOTSTRAP_TOKEN=${BOLD}${BOOTSTRAP_TOKEN}${NC}"
echo -e "AUTH_INTROSPECTION_API_KEY=${BOLD}${INTROSPECT_KEY}${NC}"
echo "--------------------------------------------------------"
