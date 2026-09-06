#!/usr/bin/env python3
"""OpenDesk Auth — JWT Generation, Inspection & Verification Utility.

Provides CLI commands for:
  - Generating custom RS256 JWT access tokens for testing and mock services.
  - Decoding and inspecting JWT payloads, headers, and expiry timestamps.
  - Cryptographically verifying tokens against local PEM keys or remote JWKS.
  - Running live end-to-end JWKS verification and API authorization tests.

Usage:
  python3 scripts/jwt_tool.py generate [--email dev@example.com] [--aud myapp]
  python3 scripts/jwt_tool.py decode <TOKEN>
  python3 scripts/jwt_tool.py verify <TOKEN> [--aud myapp] [--jwks-url http://127.0.0.1:8090/.well-known/jwks.json]
  python3 scripts/jwt_tool.py test [--base-url http://127.0.0.1:8090]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Ensure deskid can be imported from src
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    import httpx
    import jwt
    from cryptography.hazmat.primitives import serialization
except ImportError as err:
    print(f"Error: Missing dependency ({err}). Run: pip install -e '.[dev]'")
    sys.exit(1)


# ANSI Terminal Colors
class Colors:
    GREEN = "\033[0;32m"
    BLUE = "\033[0;34m"
    YELLOW = "\033[0;33m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def load_env_defaults() -> dict[str, str]:
    """Load default values from .env if present."""
    env_path = ROOT_DIR / ".env"
    defaults: dict[str, str] = {}
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                defaults[k.strip()] = v.strip()
    return defaults


def get_keys(priv_path: str | None = None, pub_path: str | None = None) -> tuple[str, str]:
    """Load RSA private and public PEM keys."""
    env_vals = load_env_defaults()

    priv_file = priv_path or os.environ.get("AUTH_JWT_PRIVATE_KEY_FILE") or env_vals.get("AUTH_JWT_PRIVATE_KEY_FILE") or str(ROOT_DIR / "private.pem")
    pub_file = pub_path or os.environ.get("AUTH_JWT_PUBLIC_KEY_FILE") or env_vals.get("AUTH_JWT_PUBLIC_KEY_FILE") or str(ROOT_DIR / "public.pem")

    priv_pem = os.environ.get("AUTH_JWT_PRIVATE_KEY") or env_vals.get("AUTH_JWT_PRIVATE_KEY")
    pub_pem = os.environ.get("AUTH_JWT_PUBLIC_KEY") or env_vals.get("AUTH_JWT_PUBLIC_KEY")

    if not priv_pem and Path(priv_file).is_file():
        priv_pem = Path(priv_file).read_text(encoding="utf-8")
    if not pub_pem and Path(pub_file).is_file():
        pub_pem = Path(pub_file).read_text(encoding="utf-8")

    if not priv_pem or not pub_pem:
        print(f"{Colors.RED}Error: RSA keys not found.{Colors.RESET}")
        print(f"Generate keys using: {Colors.BOLD}./scripts/generate_keys.sh{Colors.RESET}")
        sys.exit(1)

    return priv_pem, pub_pem


def format_ts(ts: int | None) -> str:
    if not ts:
        return "N/A"
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


# ==============================================================================
# Command: Generate
# ==============================================================================
def cmd_generate(args: argparse.Namespace) -> None:
    priv_pem, _, = get_keys(args.priv_key, args.pub_key)
    issuer = args.iss or os.environ.get("AUTH_ISSUER") or env_vals.get("AUTH_ISSUER")
    if not issuer:
        print(f"{Colors.RED}Error: AUTH_ISSUER is not set in environment or .env. Specify --iss or configure AUTH_ISSUER.{Colors.RESET}")
        sys.exit(1)
    kid = args.kid or os.environ.get("AUTH_JWT_KID") or env_vals.get("AUTH_JWT_KID") or "opendesk-auth-1"
    sub = args.sub or str(uuid.uuid4())
    email = args.email or os.environ.get("AUTH_TEST_USER_EMAIL") or env_vals.get("AUTH_TEST_USER_EMAIL") or f"user-{sub[:8]}@auth.local"
    org_id = args.org_id or str(uuid.uuid4())
    workspace_id = args.workspace_id or org_id

    audiences = ["opendesk-auth"]
    if args.aud:
        for a in args.aud.split(","):
            a = a.strip()
            if a and a not in audiences:
                audiences.append(a)

    roles: dict[str, str] = {}
    if args.roles:
        try:
            roles = json.loads(args.roles)
        except Exception:
            for item in args.roles.split(","):
                if ":" in item:
                    k, v = item.split(":", 1)
                    roles[k.strip()] = v.strip()
                elif item.strip():
                    roles[item.strip()] = "operator"

    now = datetime.now(timezone.utc)
    iat = int(now.timestamp())
    exp = int((now + timedelta(minutes=args.exp_minutes)).timestamp())

    payload: dict[str, Any] = {
        "sub": sub,
        "email": email,
        "org_id": org_id,
        "workspace_id": workspace_id,
        "aud": audiences,
        "roles": roles,
        "iss": issuer,
        "iat": iat,
        "exp": exp,
    }

    token = jwt.encode(payload, priv_pem, algorithm="RS256", headers={"kid": kid})

    if args.raw:
        print(token)
        return

    print(f"\n{Colors.BLUE}{Colors.BOLD}=== Generated RS256 JWT Access Token ==={Colors.RESET}\n")
    print(f"{Colors.GREEN}{Colors.BOLD}{token}{Colors.RESET}\n")

    print(f"{Colors.BOLD}Token Metadata:{Colors.RESET}")
    print(f"  Header KID:     {Colors.CYAN}{kid}{Colors.RESET}")
    print(f"  Algorithm:      {Colors.CYAN}RS256{Colors.RESET}")
    print(f"  Subject (sub):  {Colors.CYAN}{sub}{Colors.RESET}")
    print(f"  Email:          {Colors.CYAN}{email}{Colors.RESET}")
    print(f"  Org / WS ID:    {Colors.CYAN}{org_id}{Colors.RESET}")
    print(f"  Audiences:      {Colors.CYAN}{json.dumps(audiences)}{Colors.RESET}")
    print(f"  Roles:          {Colors.CYAN}{json.dumps(roles)}{Colors.RESET}")
    print(f"  Issued At:      {Colors.CYAN}{format_ts(iat)}{Colors.RESET}")
    print(f"  Expires At:     {Colors.CYAN}{format_ts(exp)}{Colors.RESET} ({args.exp_minutes} mins)")
    print(f"  Issuer (iss):   {Colors.CYAN}{issuer}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Usage in HTTP Request:{Colors.RESET}")
    print(f"  Authorization: Bearer {token[:25]}...")
    print(f"  {Colors.DIM}curl -H \"Authorization: Bearer {token}\" {issuer}/v1/auth/me{Colors.RESET}\n")


# ==============================================================================
# Command: Decode / Inspect
# ==============================================================================
def cmd_decode(args: argparse.Namespace) -> None:
    token = args.token.strip().replace("Bearer ", "")
    try:
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(token, options={"verify_signature": False})
    except Exception as exc:
        print(f"{Colors.RED}Error decoding token: {exc}{Colors.RESET}")
        sys.exit(1)

    print(f"\n{Colors.BLUE}{Colors.BOLD}=== Decoded JWT Token ==={Colors.RESET}\n")

    print(f"{Colors.BOLD}[Header]:{Colors.RESET}")
    print(f"  Algorithm:  {Colors.CYAN}{header.get('alg')}{Colors.RESET}")
    print(f"  Key ID:     {Colors.CYAN}{header.get('kid')}{Colors.RESET}")
    print(f"  Type:       {Colors.CYAN}{header.get('typ', 'JWT')}{Colors.RESET}")

    print(f"\n{Colors.BOLD}[Claims / Payload]:{Colors.RESET}")
    print(f"  Subject (sub):    {Colors.CYAN}{payload.get('sub')}{Colors.RESET}")
    print(f"  Email:            {Colors.CYAN}{payload.get('email')}{Colors.RESET}")
    print(f"  Org ID:           {Colors.CYAN}{payload.get('org_id')}{Colors.RESET}")
    print(f"  Workspace ID:     {Colors.CYAN}{payload.get('workspace_id')}{Colors.RESET}")
    print(f"  Audience (aud):   {Colors.CYAN}{json.dumps(payload.get('aud'))}{Colors.RESET}")
    print(f"  Roles:            {Colors.CYAN}{json.dumps(payload.get('roles', {}))}{Colors.RESET}")
    print(f"  Issuer (iss):     {Colors.CYAN}{payload.get('iss')}{Colors.RESET}")
    print(f"  Issued At (iat):  {Colors.CYAN}{format_ts(payload.get('iat'))}{Colors.RESET}")

    exp = payload.get("exp")
    if exp:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        diff = exp - now_ts
        if diff > 0:
            status = f"{Colors.GREEN}VALID (expires in {diff // 60}m {diff % 60}s){Colors.RESET}"
        else:
            status = f"{Colors.RED}EXPIRED ({abs(diff) // 60}m {abs(diff) % 60}s ago){Colors.RESET}"
        print(f"  Expires (exp):    {Colors.CYAN}{format_ts(exp)}{Colors.RESET} → {status}")
    else:
        print(f"  Expires (exp):    {Colors.YELLOW}No expiration set{Colors.RESET}")

    if args.json:
        print(f"\n{Colors.BOLD}[Raw JSON]:{Colors.RESET}")
        print(json.dumps({"header": header, "payload": payload}, indent=2))
    print()


# ==============================================================================
# Command: Verify
# ==============================================================================
def cmd_verify(args: argparse.Namespace) -> None:
    token = args.token.strip().replace("Bearer ", "")
    env_vals = load_env_defaults()
    expected_iss = args.iss or os.environ.get("AUTH_ISSUER") or env_vals.get("AUTH_ISSUER")
    if not expected_iss and not args.skip_iss:
        print(f"{Colors.RED}Error: AUTH_ISSUER is not set. Specify --iss, set AUTH_ISSUER, or pass --skip-iss.{Colors.RESET}")
        sys.exit(1)

    print(f"\n{Colors.BLUE}{Colors.BOLD}=== Cryptographic Token Verification ==={Colors.RESET}\n")

    # Fetch public key from JWKS if requested
    pub_pem: str | bytes = ""
    if args.jwks_url:
        print(f"Fetching public key from JWKS: {Colors.CYAN}{args.jwks_url}{Colors.RESET}...")
        try:
            res = httpx.get(args.jwks_url, timeout=5.0)
            res.raise_for_status()
            jwks = res.json()
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            matching_key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
            if not matching_key:
                print(f"{Colors.RED}Error: No key matching kid '{kid}' found in JWKS.{Colors.RESET}")
                sys.exit(1)
            pub_pem = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(matching_key))
            print(f"{Colors.GREEN}✓ Loaded matching public key for kid: {kid}{Colors.RESET}")
        except Exception as exc:
            print(f"{Colors.RED}Failed to load JWKS: {exc}{Colors.RESET}")
            sys.exit(1)
    else:
        _, pub_pem = get_keys(pub_path=args.pub_key)
        print("Verifying against local public key...")

    options: dict[str, Any] = {
        "verify_aud": args.aud is not None,
        "verify_iss": not args.skip_iss,
    }

    try:
        decoded = jwt.decode(
            token,
            pub_pem,
            algorithms=["RS256"],
            issuer=None if args.skip_iss else expected_iss,
            audience=args.aud,
            options=options,
        )
        print(f"{Colors.GREEN}{Colors.BOLD}✓ VERIFICATION SUCCESSFUL!{Colors.RESET}")
        print(f"  Subject:     {Colors.CYAN}{decoded.get('sub')}{Colors.RESET}")
        print(f"  Email:       {Colors.CYAN}{decoded.get('email')}{Colors.RESET}")
        print(f"  Issuer:      {Colors.CYAN}{decoded.get('iss')}{Colors.RESET}")
        print(f"  Audience:    {Colors.CYAN}{json.dumps(decoded.get('aud'))}{Colors.RESET}")
        print(f"  Signature:   {Colors.GREEN}Valid RS256 Signature{Colors.RESET}")
        print(f"  Status:      {Colors.GREEN}Active & Valid{Colors.RESET}\n")
    except jwt.ExpiredSignatureError:
        print(f"{Colors.RED}{Colors.BOLD}✗ VERIFICATION FAILED: Token has expired.{Colors.RESET}\n")
        sys.exit(1)
    except jwt.InvalidAudienceError:
        print(f"{Colors.RED}{Colors.BOLD}✗ VERIFICATION FAILED: Invalid audience (expected: {args.aud}).{Colors.RESET}\n")
        sys.exit(1)
    except jwt.InvalidIssuerError:
        print(f"{Colors.RED}{Colors.BOLD}✗ VERIFICATION FAILED: Issuer mismatch (expected: {expected_iss}).{Colors.RESET}\n")
        sys.exit(1)
    except jwt.InvalidSignatureError:
        print(f"{Colors.RED}{Colors.BOLD}✗ VERIFICATION FAILED: Invalid cryptographic signature.{Colors.RESET}\n")
        sys.exit(1)
    except Exception as exc:
        print(f"{Colors.RED}{Colors.BOLD}✗ VERIFICATION FAILED: {exc}{Colors.RESET}\n")
        sys.exit(1)


# ==============================================================================
# Command: Test (Live Server + JWKS + API Authentication test)
# ==============================================================================
def cmd_test(args: argparse.Namespace) -> None:
    env_vals = load_env_defaults()
    base_url = (args.base_url or os.environ.get("AUTH_ISSUER") or env_vals.get("AUTH_ISSUER") or "").rstrip("/")
    if not base_url:
        print(f"{Colors.RED}Error: Base URL is not set. Specify --base-url or set AUTH_ISSUER in environment or .env.{Colors.RESET}")
        sys.exit(1)
    print(f"\n{Colors.BLUE}{Colors.BOLD}======================================================{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}        🧪 OpenDesk Auth JWT & JWKS Test Suite        {Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}======================================================{Colors.RESET}\n")

    priv_pem, pub_pem = get_keys()

    # Step 1: Healthcheck
    print(f"{Colors.BOLD}[1] Checking Service Health ({base_url}/health)...{Colors.RESET}")
    try:
        health = httpx.get(f"{base_url}/health", timeout=5.0)
        if health.status_code == 200:
            print(f"    {Colors.GREEN}✓ Server is ONLINE: {health.json()}{Colors.RESET}")
        else:
            print(f"    {Colors.YELLOW}Warning: Server returned status {health.status_code}{Colors.RESET}")
    except Exception as exc:
        print(f"    {Colors.RED}✗ Could not reach server at {base_url}: {exc}{Colors.RESET}")
        print(f"    Start server using: {Colors.BOLD}./start_all.sh{Colors.RESET}\n")
        sys.exit(1)

    # Step 2: Fetch and Validate JWKS
    print(f"\n{Colors.BOLD}[2] Testing JWKS Endpoint ({base_url}/.well-known/jwks.json)...{Colors.RESET}")
    jwks_url = f"{base_url}/.well-known/jwks.json"
    res = httpx.get(jwks_url, timeout=5.0)
    assert res.status_code == 200, f"Expected 200 from JWKS, got {res.status_code}"
    jwks_data = res.json()
    assert "keys" in jwks_data and len(jwks_data["keys"]) > 0, "No keys in JWKS"
    jwk = jwks_data["keys"][0]
    print(f"    {Colors.GREEN}✓ JWKS returned valid RSA key:{Colors.RESET}")
    print(f"      kid: {jwk.get('kid')}, alg: {jwk.get('alg')}, kty: {jwk.get('kty')}")

    # Step 3: Issue Test Token
    print(f"\n{Colors.BOLD}[3] Generating Test Access Token...{Colors.RESET}")
    sub_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub_id,
        "email": "test-jwt-suite@example.com",
        "org_id": org_id,
        "workspace_id": org_id,
        "aud": ["opendesk-auth", "test-product"],
        "roles": {"test-product": "admin"},
        "iss": base_url,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    token = jwt.encode(payload, priv_pem, algorithm="RS256", headers={"kid": jwk.get("kid", "opendesk-auth-1")})
    print(f"    {Colors.GREEN}✓ Token signed with RS256: {token[:35]}...{Colors.RESET}")

    # Step 4: Verify Token against remote JWKS
    print(f"\n{Colors.BOLD}[4] Verifying Token against JWKS Key...{Colors.RESET}")
    remote_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
    decoded = jwt.decode(
        token,
        remote_key,
        algorithms=["RS256"],
        issuer=base_url,
        audience="opendesk-auth",
    )
    assert decoded["sub"] == sub_id
    print(f"    {Colors.GREEN}✓ Token verified against JWKS public key!{Colors.RESET}")

    # Step 5: Test Introspection (if API key available)
    introspect_key = os.environ.get("AUTH_INTROSPECTION_API_KEY") or load_env_defaults().get("AUTH_INTROSPECTION_API_KEY")
    if introspect_key:
        print(f"\n{Colors.BOLD}[5] Testing Token Introspection (/introspect)...{Colors.RESET}")
        try:
            introspect_res = httpx.post(
                f"{base_url}/introspect",
                headers={"Authorization": f"Bearer {introspect_key}"},
                json={"token": token},
                timeout=5.0,
            )
            if introspect_res.status_code == 200:
                print(f"    {Colors.GREEN}✓ Introspection response: {introspect_res.json()}{Colors.RESET}")
            else:
                print(f"    {Colors.YELLOW}Introspect returned {introspect_res.status_code}: {introspect_res.text}{Colors.RESET}")
        except Exception as exc:
            print(f"    {Colors.YELLOW}Introspect test skipped: {exc}{Colors.RESET}")
    else:
        print(f"\n{Colors.BOLD}[5] Introspection Test:{Colors.RESET} {Colors.DIM}(AUTH_INTROSPECTION_API_KEY not set; skipped){Colors.RESET}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}======================================================{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}     ✓ All JWT Generation & Verification Tests PASSED  {Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}======================================================{Colors.RESET}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenDesk Auth JWT Utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. generate
    gen_parser = subparsers.add_parser("generate", aliases=["issue"], help="Generate RS256 JWT access token")
    gen_parser.add_argument("--sub", help="Subject user ID (UUID)")
    gen_parser.add_argument("--email", help="User email address")
    gen_parser.add_argument("--org-id", help="Organization ID (UUID)")
    gen_parser.add_argument("--workspace-id", help="Workspace ID (defaults to org-id)")
    gen_parser.add_argument("--aud", help="Comma-separated product audiences")
    gen_parser.add_argument("--roles", help="JSON string or comma-separated audience:role pairs")
    gen_parser.add_argument("--exp-minutes", type=int, default=60, help="Expiration in minutes (default: 60)")
    gen_parser.add_argument("--kid", help="Key ID header (default: opendesk-auth-1)")
    gen_parser.add_argument("--iss", help="Issuer URL (defaults to AUTH_ISSUER)")
    gen_parser.add_argument("--priv-key", help="Path to private.pem")
    gen_parser.add_argument("--pub-key", help="Path to public.pem")
    gen_parser.add_argument("--raw", action="store_true", help="Output only the raw token string")

    # 2. decode
    dec_parser = subparsers.add_parser("decode", aliases=["inspect"], help="Decode and inspect a JWT token")
    dec_parser.add_argument("token", help="JWT token string")
    dec_parser.add_argument("--json", action="store_true", help="Print raw JSON format")

    # 3. verify
    ver_parser = subparsers.add_parser("verify", aliases=["validate"], help="Cryptographically verify a JWT token")
    ver_parser.add_argument("token", help="JWT token string")
    ver_parser.add_argument("--aud", help="Required audience claim")
    ver_parser.add_argument("--jwks-url", help="URL to JWKS endpoint (e.g. <AUTH_ISSUER>/.well-known/jwks.json)")
    ver_parser.add_argument("--pub-key", help="Path to public.pem")

    # 4. test
    test_parser = subparsers.add_parser("test", help="Run JWT generation, JWKS, and live verification tests")
    test_parser.add_argument("--base-url", default=None, help="Base URL of running Auth service (defaults to AUTH_ISSUER)")

    args = parser.parse_args()

    if args.command in ("generate", "issue"):
        cmd_generate(args)
    elif args.command in ("decode", "inspect"):
        cmd_decode(args)
    elif args.command in ("verify", "validate"):
        cmd_verify(args)
    elif args.command == "test":
        cmd_test(args)


if __name__ == "__main__":
    main()
