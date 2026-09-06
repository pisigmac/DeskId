"""RS256 key management and JWT helpers."""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization

from deskid.config import Settings, get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_urlsafe_token(length: int = 48) -> str:
    return secrets.token_urlsafe(length)


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def _b64url_uint(val: int) -> str:
    length = (val.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(val.to_bytes(length, "big")).rstrip(b"=").decode("ascii")


@lru_cache
def _ensure_keys(settings_fingerprint: str) -> tuple[str, str, str]:
    """Return (private_pem, public_pem, kid). Fails if keys are not configured."""
    settings = get_settings()
    priv = settings.private_key_pem()
    pub = settings.public_key_pem()
    if priv and pub:
        return priv, pub, settings.jwt_kid
    raise RuntimeError(
        "JWT signing keys are not configured. "
        "Set AUTH_JWT_PRIVATE_KEY and AUTH_JWT_PUBLIC_KEY, "
        "or AUTH_JWT_PRIVATE_KEY_FILE and AUTH_JWT_PUBLIC_KEY_FILE."
    )


def get_key_material(settings: Settings | None = None) -> tuple[str, str, str]:
    settings = settings or get_settings()
    fingerprint = f"{settings.jwt_private_key_file}:{settings.jwt_public_key_file}:{bool(settings.jwt_private_key)}"
    return _ensure_keys(fingerprint)


def pem_to_jwk(pub_pem: str, kid: str) -> dict[str, Any]:
    pub = serialization.load_pem_public_key(pub_pem.encode("utf-8"))
    numbers = pub.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _b64url_uint(numbers.n),
        "e": _b64url_uint(numbers.e),
    }


def public_jwk(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    _, pub_pem, kid = get_key_material(settings)
    return pem_to_jwk(pub_pem, kid)


def public_jwks(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    keys = [public_jwk(settings)]
    for kid, pem in settings.previous_public_keys():
        try:
            keys.append(pem_to_jwk(pem, kid))
        except Exception:
            pass
    return keys


def issue_access_token(
    *,
    sub: str,
    email: str,
    org_id: str | None,
    workspace_id: str | None,
    audiences: list[str],
    roles: dict[str, str],
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    priv, _, kid = get_key_material(settings)
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": sub,
        "email": email,
        "org_id": org_id,
        "workspace_id": workspace_id,
        # Always include the Auth service itself as an audience so Auth endpoints can
        # verify tokens locally without depending on product-specific audiences.
        "aud": ["deskid", *audiences],
        "roles": roles,
        "iss": settings.issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
    }
    return jwt.encode(payload, priv, algorithm="RS256", headers={"kid": kid})


def decode_access_token(token: str, audience: str | None = None, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    _, current_pub, current_kid = get_key_material(settings)
    options: dict[str, Any] = {"verify_aud": audience is not None}

    # Extract kid from unverified token header if present
    target_kid = None
    try:
        header = jwt.get_unverified_header(token)
        target_kid = header.get("kid")
    except Exception:
        pass

    # Build list of candidate public keys: [(kid, pem)]
    candidate_keys: list[tuple[str, str]] = [(current_kid, current_pub)]
    for prev_kid, prev_pem in settings.previous_public_keys():
        candidate_keys.append((prev_kid, prev_pem))

    # If target_kid matches one of the candidates, prioritize it
    if target_kid:
        candidate_keys.sort(key=lambda item: 0 if item[0] == target_kid else 1)

    last_exc: Exception | None = None
    for _, pem in candidate_keys:
        try:
            return jwt.decode(
                token,
                pem,
                algorithms=["RS256"],
                issuer=settings.issuer,
                audience=audience,
                options=options,
            )
        except jwt.InvalidTokenError as exc:
            last_exc = exc
            continue

    if last_exc:
        raise last_exc
    raise jwt.InvalidTokenError("Could not decode token")
