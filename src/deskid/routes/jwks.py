"""JWKS and token introspection."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from deskid.config import get_settings
from deskid.crypto import decode_access_token, public_jwk
from deskid.db import get_db
from deskid.models import User
from deskid.schemas import IntrospectRequest, IntrospectResponse

router = APIRouter(tags=["jwks"])
bearer = HTTPBearer(auto_error=False)


def _require_introspection_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> None:
    settings = get_settings()
    expected = settings.introspection_api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token introspection is not configured on this server",
        )
    if not creds or creds.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid introspection credentials",
        )


@router.get("/.well-known/jwks.json")
def jwks() -> dict:
    return {"keys": [public_jwk()]}


@router.post("/introspect", response_model=IntrospectResponse)
def introspect(
    body: IntrospectRequest,
    _: None = Depends(_require_introspection_auth),
    db: Session = Depends(get_db),
) -> IntrospectResponse:
    try:
        claims = decode_access_token(body.token)
        sub = claims.get("sub")
        if sub:
            user = db.query(User).filter(User.id == sub).one_or_none()
            if not user or not user.is_active or user.deleted_at is not None:
                return IntrospectResponse(active=False, claims=None)
        return IntrospectResponse(active=True, claims=claims)
    except Exception:
        return IntrospectResponse(active=False, claims=None)
