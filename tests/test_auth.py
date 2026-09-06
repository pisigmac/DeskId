"""Auth service tests."""

from __future__ import annotations

import os

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ["AUTH_DATABASE_URL"] = "sqlite+pysqlite:////tmp/deskid_test.db"
os.environ["AUTH_ISSUER"] = "https://auth.test.local"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "auth.db"
    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_ISSUER", "https://auth.test.local")
    # Deployment-style default audiences (not hardcoded in Auth source)
    monkeypatch.setenv("AUTH_DEFAULT_AUDIENCES", "demo-app")
    # Most existing tests register + login in one flow; disable verification for them.
    # Dedicated tests below exercise the verification gate explicitly.
    monkeypatch.setenv("AUTH_REQUIRE_EMAIL_VERIFICATION", "false")
    # Source-level default is closed; tests that do not explicitly exercise the
    # bootstrap gate run with open registration enabled for convenience.
    monkeypatch.setenv("AUTH_OPEN_REGISTRATION", "true")
    monkeypatch.setenv("AUTH_BOOTSTRAP_TOKEN", "test-bootstrap-token")

    # Generate a fresh RSA key pair for each test run
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    monkeypatch.setenv("AUTH_JWT_PRIVATE_KEY", priv_pem)
    monkeypatch.setenv("AUTH_JWT_PUBLIC_KEY", pub_pem)

    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    from deskid.db import init_db, reset_engine
    from deskid.app import create_app

    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()
    init_db()
    app = create_app()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()


def test_register_login_me_jwks(client: TestClient):
    r = client.post(
        "/v1/auth/register",
        json={"email": "admin@example.com", "password": "password123", "display_name": "Admin"},
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "admin@example.com"
    assert body["is_platform_admin"] is True
    assert any(g["audience"] == "demo-app" for g in body["grants"])

    jwks = client.get("/.well-known/jwks.json")
    assert jwks.status_code == 200
    keys = jwks.json()["keys"]
    assert keys[0]["kty"] == "RSA"
    assert keys[0]["kid"]

    from deskid.crypto import get_key_material

    _, pub, _ = get_key_material()
    claims = jwt.decode(
        tokens["access_token"],
        pub,
        algorithms=["RS256"],
        issuer="https://auth.test.local",
        options={"verify_aud": False},
    )
    assert claims["email"] == "admin@example.com"
    assert "demo-app" in claims["aud"]
    assert claims["roles"]["demo-app"] == "admin"

    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )
    assert login.status_code == 200

    refresh = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    new_refresh = refresh.json()["refresh_token"]
    again = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert again.status_code == 401

    logout = client.post("/v1/auth/logout", json={"refresh_token": new_refresh})
    assert logout.status_code == 200


def test_org_and_grant(client: TestClient):
    admin = client.post(
        "/v1/auth/register",
        json={"email": "boss@example.com", "password": "password123"},
    ).json()
    user = client.post(
        "/v1/auth/register",
        json={"email": "dev@example.com", "password": "password123"},
    ).json()
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {user['access_token']}"}).json()
    user_id = me["id"]

    org = client.post(
        "/v1/orgs",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"name": "Acme"},
    )
    assert org.status_code == 200

    grant = client.post(
        "/v1/admin/grants",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"user_id": user_id, "audience": "other-product", "role": "viewer"},
    )
    assert grant.status_code == 200

    users = client.get(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert users.status_code == 200
    listed = users.json()
    assert listed["total"] >= 2
    assert len(listed["users"]) >= 2


def test_oauth_unconfigured(client: TestClient):
    r = client.get("/v1/oauth/google/start", follow_redirects=False)
    assert r.status_code == 501


def test_introspect(client: TestClient, monkeypatch):
    # Configure introspection API key
    monkeypatch.setenv("AUTH_INTROSPECTION_API_KEY", "test-introspect-key")
    from deskid.config import get_settings
    get_settings.cache_clear()

    tokens = client.post(
        "/v1/auth/register",
        json={"email": "x@example.com", "password": "password123"},
    ).json()
    ok = client.post(
        "/introspect",
        json={"token": tokens["access_token"]},
        headers={"Authorization": "Bearer test-introspect-key"},
    )
    assert ok.status_code == 200
    assert ok.json()["active"] is True

    bad = client.post(
        "/introspect",
        json={"token": "nope"},
        headers={"Authorization": "Bearer test-introspect-key"},
    )
    assert bad.json()["active"] is False

    no_auth = client.post("/introspect", json={"token": tokens["access_token"]})
    assert no_auth.status_code == 401 or no_auth.status_code == 503


def test_no_product_coupling_in_defaults(client: TestClient, monkeypatch, tmp_path):
    """With empty AUTH_DEFAULT_AUDIENCES, signup creates no product grants."""
    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    from deskid.db import init_db, reset_engine
    from deskid.app import create_app

    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'bare.db'}")
    monkeypatch.setenv("AUTH_DEFAULT_AUDIENCES", "")
    # Keys are already set by the client fixture via monkeypatch
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()
    init_db()
    with TestClient(create_app()) as c:
        tokens = c.post(
            "/v1/auth/register",
            json={"email": "bare@example.com", "password": "password123"},
        ).json()
        me = c.get("/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
        assert me["grants"] == []
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()


def test_email_verification_token_model(client):
    from deskid.models import EmailVerificationToken

    assert EmailVerificationToken.__tablename__ == "email_verification_tokens"


# ---------------------------------------------------------------------------
# Task 1 / 2 / 3 — model presence
# ---------------------------------------------------------------------------

def test_password_reset_token_model(client):
    from deskid.models import PasswordResetToken
    assert PasswordResetToken.__tablename__ == "password_reset_tokens"


def test_audit_log_event_model(client):
    from deskid.models import AuditLogEvent
    assert AuditLogEvent.__tablename__ == "audit_log_events"


# ---------------------------------------------------------------------------
# Task 4 — crypto helpers and fail-closed key behaviour
# ---------------------------------------------------------------------------

def test_generate_urlsafe_token():
    from deskid.crypto import generate_urlsafe_token, hash_token
    token = generate_urlsafe_token()
    assert len(token) >= 48
    assert hash_token(token) != token


def test_ensure_keys_fails_when_not_configured(monkeypatch):
    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    monkeypatch.delenv("AUTH_JWT_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("AUTH_JWT_PUBLIC_KEY", raising=False)
    monkeypatch.setenv("AUTH_JWT_PRIVATE_KEY_FILE", "")
    monkeypatch.setenv("AUTH_JWT_PUBLIC_KEY_FILE", "")
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="JWT signing keys are not configured"):
            _ensure_keys("no-keys")
    finally:
        get_settings.cache_clear()
        _ensure_keys.cache_clear()


# ---------------------------------------------------------------------------
# Task 5 — new schemas
# ---------------------------------------------------------------------------

def test_new_schemas_exist():
    from deskid.schemas import (
        AuditLogQueryParams,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        UserExportResponse,
        VerifyEmailRequest,
    )
    assert VerifyEmailRequest(token="abc").token == "abc"
    assert ForgotPasswordRequest(email="a@b.com").email == "a@b.com"
    assert ResetPasswordRequest(token="abc", password="12345678").password == "12345678"


# ---------------------------------------------------------------------------
# Task 6 — mail client helpers
# ---------------------------------------------------------------------------

def test_mail_client_builds_verification_payload():
    from deskid.mail_client import build_verification_email
    payload = build_verification_email("user@example.com", "verify_abc123")
    assert payload["to"] == "user@example.com"
    assert "verify_abc123" in payload["html"]


def test_mail_client_builds_reset_payload():
    from deskid.mail_client import build_password_reset_email
    payload = build_password_reset_email("user@example.com", "reset_xyz")
    assert payload["to"] == "user@example.com"
    assert "reset_xyz" in payload["html"]


# ---------------------------------------------------------------------------
# Task 7 — verification and reset token services
# ---------------------------------------------------------------------------

def test_verification_token_lifecycle(client):
    from deskid.db import get_db
    from deskid.models import User
    from deskid.services import create_verification_token, verify_email_token

    db = next(get_db())
    # Create user directly via service
    from deskid.services import create_user_with_password
    user = create_user_with_password(db, email="verifytest@example.com", password="password123")

    raw = create_verification_token(db, user)
    assert len(raw) > 20

    verified = verify_email_token(db, raw)
    assert verified is not None
    assert verified.id == user.id

    # Token should be consumed — second use returns None
    assert verify_email_token(db, raw) is None


def test_password_reset_token_lifecycle(client):
    from deskid.db import get_db
    from deskid.services import (
        consume_password_reset_token,
        create_password_reset_token,
        create_user_with_password,
        reset_user_password,
    )
    from deskid.crypto import verify_password

    db = next(get_db())
    user = create_user_with_password(db, email="resettest@example.com", password="old_pass123")
    raw = create_password_reset_token(db, user)
    assert len(raw) > 20

    claimed = consume_password_reset_token(db, raw)
    assert claimed is not None
    assert claimed.id == user.id

    reset_user_password(db, user, "new_pass456")
    assert verify_password("new_pass456", user.password_hash)

    # Token consumed — second use returns None
    assert consume_password_reset_token(db, raw) is None


# ---------------------------------------------------------------------------
# Task 8 — rate limiter
# ---------------------------------------------------------------------------

def test_rate_limiter_allows_and_blocks():
    from deskid.config import get_settings
    from deskid.rate_limit import RateLimiter
    settings = get_settings()
    limiter = RateLimiter(settings)
    for _ in range(settings.rate_limit_login):
        assert limiter.is_allowed("192.0.2.1", "login") is True
    assert limiter.is_allowed("192.0.2.1", "login") is False
    # Different IP is unaffected
    assert limiter.is_allowed("192.0.2.2", "login") is True


def test_rate_limiter_flag_disabled(client, monkeypatch):
    from deskid.config import get_settings
    from deskid.rate_limit import RateLimiter

    monkeypatch.setenv("AUTH_RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()
    settings = get_settings()
    limiter = RateLimiter(settings)

    # When disabled, requests far exceeding the limit are always allowed
    for _ in range(50):
        assert limiter.is_allowed("192.0.2.1", "login") is True

    get_settings.cache_clear()


def test_db_backed_rate_limiter_multi_worker_consistency(client, monkeypatch):
    from deskid.config import get_settings
    from deskid.rate_limit import RateLimiter

    monkeypatch.setenv("AUTH_RATE_LIMIT_BACKEND", "db")
    get_settings.cache_clear()
    settings = get_settings()

    # Simulate Worker 1 and Worker 2 as distinct process instances sharing DB
    worker1 = RateLimiter(settings)
    worker2 = RateLimiter(settings)

    # Worker 1 takes half the quota
    for _ in range(settings.rate_limit_login // 2):
        assert worker1.is_allowed("198.51.100.1", "login") is True

    # Worker 2 takes the remaining half
    remaining = settings.rate_limit_login - (settings.rate_limit_login // 2)
    for _ in range(remaining):
        assert worker2.is_allowed("198.51.100.1", "login") is True

    # Next attempt from either worker must be blocked because DB state is shared
    assert worker1.is_allowed("198.51.100.1", "login") is False
    assert worker2.is_allowed("198.51.100.1", "login") is False

    get_settings.cache_clear()


def test_redis_backed_rate_limiter_allows_and_blocks(monkeypatch):
    import os
    import uuid
    from datetime import datetime, timezone
    import redis
    from deskid.config import get_settings
    from deskid.rate_limit import RateLimiter

    redis_url = os.environ.get("AUTH_RATE_LIMIT_REDIS_URL") or "redis://127.0.0.1:6379/0"
    try:
        r = redis.Redis.from_url(redis_url, socket_timeout=1.0)
        r.ping()
    except Exception:
        # If redis is not reachable in this test runner environment, skip
        import pytest
        pytest.skip("Local redis server not reachable")

    test_ip = f"client-id-{uuid.uuid4().hex[:8]}"
    r.delete(f"rl:login:{test_ip}")

    monkeypatch.setenv("AUTH_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("AUTH_RATE_LIMIT_REDIS_URL", redis_url)
    get_settings.cache_clear()
    settings = get_settings()

    worker1 = RateLimiter(settings)
    worker2 = RateLimiter(settings)

    # Worker 1 consumes first half
    for _ in range(settings.rate_limit_login // 2):
        assert worker1.is_allowed(test_ip, "login") is True

    # Worker 2 consumes remaining quota
    remaining = settings.rate_limit_login - (settings.rate_limit_login // 2)
    for _ in range(remaining):
        assert worker2.is_allowed(test_ip, "login") is True

    # Limit reached across workers: both must be blocked
    assert worker1.is_allowed(test_ip, "login") is False
    assert worker2.is_allowed(test_ip, "login") is False

    # Clean up test key
    r.delete(f"rl:login:{test_ip}")
    get_settings.cache_clear()


def test_rate_limiter_fail_closed_mode(monkeypatch):
    from deskid.config import get_settings
    from deskid.rate_limit import RateLimiter

    monkeypatch.setenv("AUTH_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("AUTH_ISSUER", "https://auth.test.local")
    monkeypatch.setenv("AUTH_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("AUTH_RATE_LIMIT_REDIS_URL", "redis://127.0.0.1:1/0")  # unreachable port / connection failure
    monkeypatch.setenv("AUTH_RATE_LIMIT_FAIL_CLOSED", "true")
    get_settings.cache_clear()
    settings = get_settings()

    limiter = RateLimiter(settings)
    # When fail-closed is True, an unreachable redis backend should reject/block the request
    assert limiter.is_allowed("192.168.1.1", "login") is False

    # When fail-closed is False, fallback to memory should allow initial requests
    monkeypatch.setenv("AUTH_RATE_LIMIT_FAIL_CLOSED", "false")
    get_settings.cache_clear()
    settings_fail_open = get_settings()
    limiter_open = RateLimiter(settings_fail_open)
    assert limiter_open.is_allowed("192.168.1.1", "login") is True
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Task 9 — email verification endpoint
# ---------------------------------------------------------------------------

def test_register_sends_verification_email(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "deskid.routes.auth.send_mail",
        lambda payload: sent.append(payload) or {"id": "msg_1", "status": "sent"},
    )
    r = client.post("/v1/auth/register", json={
        "email": "verifyflow@example.com",
        "password": "password123",
    })
    assert r.status_code == 200
    assert len(sent) == 1
    assert sent[0]["to"] == "verifyflow@example.com"


def test_verify_email_endpoint(client, monkeypatch):
    monkeypatch.setattr("deskid.routes.auth.send_mail", lambda p: {"id": "x"})
    client.post("/v1/auth/register", json={"email": "ev2@example.com", "password": "password123"})

    from deskid.db import get_db
    from deskid.models import User
    from deskid.services import create_verification_token

    db = next(get_db())
    user = db.query(User).filter(User.email == "ev2@example.com").one()
    token = create_verification_token(db, user)

    r = client.post("/v1/auth/verify-email", json={"token": token})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Reuse should fail
    r2 = client.post("/v1/auth/verify-email", json={"token": token})
    assert r2.status_code == 400


# ---------------------------------------------------------------------------
# Task 10 — password reset endpoints
# ---------------------------------------------------------------------------

def test_password_reset_flow(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "deskid.routes.auth.send_mail",
        lambda payload: sent.append(payload) or {"id": "msg_1"},
    )
    client.post("/v1/auth/register", json={"email": "reset@example.com", "password": "password123"})

    r = client.post("/v1/auth/forgot-password", json={"email": "reset@example.com"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert len(sent) >= 1  # verification + reset emails

    from deskid.db import get_db
    from deskid.models import User
    from deskid.services import create_password_reset_token

    db = next(get_db())
    user = db.query(User).filter(User.email == "reset@example.com").one()
    token = create_password_reset_token(db, user)

    r = client.post("/v1/auth/reset-password", json={"token": token, "password": "newpass123"})
    assert r.status_code == 200

    login = client.post("/v1/auth/login", json={"email": "reset@example.com", "password": "newpass123"})
    assert login.status_code == 200


def test_forgot_password_nonexistent_email_returns_ok(client):
    """Should not reveal whether email exists."""
    r = client.post("/v1/auth/forgot-password", json={"email": "ghost@example.com"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ---------------------------------------------------------------------------
# Task 11 — rate limiting on endpoints
# ---------------------------------------------------------------------------

def test_login_rate_limit(client):
    for _ in range(11):
        r = client.post("/v1/auth/login", json={"email": "x@example.com", "password": "wrong"})
    assert r.status_code == 429


def test_register_rate_limit(client):
    for i in range(11):
        r = client.post("/v1/auth/register", json={
            "email": f"rl{i}@example.com",
            "password": "password123",
        })
    assert r.status_code == 429


# ---------------------------------------------------------------------------
# Task 12 — JWT audience verification
# ---------------------------------------------------------------------------

def test_decode_access_token_supports_audience_param(client):
    from deskid.crypto import decode_access_token, issue_access_token
    from deskid.config import get_settings
    settings = get_settings()
    token = issue_access_token(
        sub="u1", email="a@b.com", org_id=None, workspace_id=None,
        audiences=["my-product"], roles={"my-product": "admin"}, settings=settings,
    )
    # Correct audience passes
    claims = decode_access_token(token, audience="my-product", settings=settings)
    assert claims["sub"] == "u1"

    # Wrong audience raises
    with pytest.raises(Exception):
        decode_access_token(token, audience="other-product", settings=settings)


# ---------------------------------------------------------------------------
# Task 13 — request-id middleware
# ---------------------------------------------------------------------------

def test_request_id_header_returned(client):
    r = client.get("/health")
    assert "x-request-id" in r.headers


def test_custom_request_id_is_echoed(client):
    r = client.get("/health", headers={"x-request-id": "my-trace-123"})
    assert r.headers["x-request-id"] == "my-trace-123"


# ---------------------------------------------------------------------------
# Task 14 — audit events emitted
# ---------------------------------------------------------------------------

def test_login_emits_audit_event(client):
    from deskid.db import get_db
    from deskid.models import AuditLogEvent

    client.post("/v1/auth/register", json={"email": "audtest@example.com", "password": "password123"})
    client.post("/v1/auth/login", json={"email": "audtest@example.com", "password": "password123"})

    db = next(get_db())
    event = db.query(AuditLogEvent).filter(AuditLogEvent.action == "user.login").first()
    assert event is not None
    assert event.actor_type == "user"


def test_register_emits_audit_event(client):
    from deskid.db import get_db
    from deskid.models import AuditLogEvent

    client.post("/v1/auth/register", json={"email": "audreg@example.com", "password": "password123"})

    db = next(get_db())
    event = db.query(AuditLogEvent).filter(AuditLogEvent.action == "user.register").first()
    assert event is not None


# ---------------------------------------------------------------------------
# Task 15 — audit log query endpoint
# ---------------------------------------------------------------------------

def test_admin_can_query_audit_log(client):
    admin_tokens = client.post("/v1/auth/register", json={
        "email": "audadmin@example.com",
        "password": "password123",
    }).json()
    client.post("/v1/auth/login", json={"email": "audadmin@example.com", "password": "password123"})

    r = client.get(
        "/v1/admin/audit?limit=10",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "events" in body
    assert "total" in body
    assert len(body["events"]) > 0


def test_non_admin_cannot_query_audit_log(client):
    client.post("/v1/auth/register", json={"email": "admin1@example.com", "password": "p123456789"})
    user_tokens = client.post("/v1/auth/register", json={
        "email": "regular@example.com",
        "password": "password123",
    }).json()
    r = client.get(
        "/v1/admin/audit",
        headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Task 16 — user data export
# ---------------------------------------------------------------------------

def test_user_can_export_own_data(client):
    tokens = client.post("/v1/auth/register", json={
        "email": "export@example.com",
        "password": "password123",
    }).json()
    r = client.get("/v1/me/export", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["email"] == "export@example.com"
    assert "identities" in data
    assert "memberships" in data
    assert "grants" in data
    assert "refresh_tokens" in data
    assert "audit_events" in data


# ---------------------------------------------------------------------------
# Task 17 — user account deletion
# ---------------------------------------------------------------------------

def test_user_can_delete_own_account(client):
    from deskid.db import get_engine
    from deskid.models import Org
    from sqlalchemy.orm import Session
    from deskid.crypto import decode_access_token

    tokens = client.post("/v1/auth/register", json={
        "email": "delete@example.com",
        "password": "password123",
    }).json()
    org_id = decode_access_token(tokens["access_token"])["org_id"]

    r = client.post("/v1/me/delete", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    login = client.post("/v1/auth/login", json={"email": "delete@example.com", "password": "password123"})
    assert login.status_code == 401

    # Check that the orphan org was also deleted from DB
    session = Session(get_engine())
    assert session.get(Org, org_id) is None
    session.close()


# ---------------------------------------------------------------------------
# Task 18 — introspect requires auth
# ---------------------------------------------------------------------------

def test_introspect_requires_auth_key(client):
    tokens = client.post("/v1/auth/register", json={
        "email": "itest@example.com",
        "password": "password123",
    }).json()
    # No auth header — should be 503 (not configured) or 401
    r = client.post("/introspect", json={"token": tokens["access_token"]})
    assert r.status_code in (401, 503)


def test_introspect_with_valid_key(client, monkeypatch):
    monkeypatch.setenv("AUTH_INTROSPECTION_API_KEY", "secret-key")
    from deskid.config import get_settings
    get_settings.cache_clear()

    tokens = client.post("/v1/auth/register", json={
        "email": "itest2@example.com",
        "password": "password123",
    }).json()
    r = client.post(
        "/introspect",
        json={"token": tokens["access_token"]},
        headers={"Authorization": "Bearer secret-key"},
    )
    assert r.status_code == 200
    assert r.json()["active"] is True
    get_settings.cache_clear()


def test_introspect_returns_inactive_for_suspended_or_deleted_user(client, monkeypatch):
    monkeypatch.setenv("AUTH_INTROSPECTION_API_KEY", "secret-key")
    from deskid.config import get_settings
    get_settings.cache_clear()

    admin = client.post("/v1/auth/register", json={
        "email": "introspect_admin@example.com",
        "password": "password123",
    }).json()
    user = client.post("/v1/auth/register", json={
        "email": "to_suspend@example.com",
        "password": "password123",
    }).json()

    # Active user token is active
    r1 = client.post(
        "/introspect",
        json={"token": user["access_token"]},
        headers={"Authorization": "Bearer secret-key"},
    )
    assert r1.status_code == 200
    assert r1.json()["active"] is True

    # Suspend user via admin endpoint
    user_id = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    ).json()["id"]

    client.patch(
        f"/v1/admin/users/{user_id}/active",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"is_active": False},
    )

    # Introspect should now report active: false immediately
    r2 = client.post(
        "/introspect",
        json={"token": user["access_token"]},
        headers={"Authorization": "Bearer secret-key"},
    )
    assert r2.status_code == 200
    assert r2.json()["active"] is False
    assert r2.json()["claims"] is None
    get_settings.cache_clear()



# ---------------------------------------------------------------------------
# P1 hardening — audience verification, refresh rate limit, proxy IP, mail logging
# ---------------------------------------------------------------------------


def test_access_token_includes_auth_service_audience(client):
    """Tokens issued by DeskID must include 'deskid' so DeskID endpoints can verify audience."""
    from deskid.crypto import decode_access_token

    tokens = client.post(
        "/v1/auth/register",
        json={"email": "audauth@example.com", "password": "password123"},
    ).json()
    claims = decode_access_token(tokens["access_token"], audience="deskid")
    assert "deskid" in claims["aud"]


def test_me_rejects_token_without_auth_audience(client):
    """A token issued for a product audience only must not work on Auth endpoints."""
    from deskid.config import get_settings
    from deskid.crypto import issue_access_token

    settings = get_settings()
    # Issue a token that does NOT include 'deskid'
    bad_token = issue_access_token(
        sub="u1",
        email="a@b.com",
        org_id=None,
        workspace_id=None,
        audiences=["other-product"],
        roles={"other-product": "admin"},
        settings=settings,
    )
    r = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert r.status_code == 401


def test_refresh_rate_limit(client):
    tokens = client.post(
        "/v1/auth/register",
        json={"email": "refreshrl@example.com", "password": "password123"},
    ).json()
    # Default rate limit refresh is 20 per 60s; exceed it.
    last_status = 200
    for _ in range(21):
        r = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        last_status = r.status_code
        if r.status_code == 200:
            tokens["refresh_token"] = r.json()["refresh_token"]
    assert last_status == 429


def test_rate_limiter_uses_x_forwarded_for_when_proxy_trusted(client, monkeypatch):
    from deskid.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_RATE_LIMIT_TRUST_PROXY", "true")
    settings = get_settings()
    assert settings.rate_limit_trust_proxy is True

    # Two different IPs behind the same proxy should be tracked separately.
    for _ in range(10):
        r = client.post(
            "/v1/auth/login",
            json={"email": "proxy1@example.com", "password": "wrong"},
            headers={"X-Forwarded-For": "203.0.113.1"},
        )
    r = client.post(
        "/v1/auth/login",
        json={"email": "proxy1@example.com", "password": "wrong"},
        headers={"X-Forwarded-For": "203.0.113.1"},
    )
    assert r.status_code == 429

    # A different forwarded IP should not be blocked.
    r2 = client.post(
        "/v1/auth/login",
        json={"email": "proxy1@example.com", "password": "wrong"},
        headers={"X-Forwarded-For": "203.0.113.2"},
    )
    assert r2.status_code == 401  # not 429


def test_rate_limiter_ignores_x_forwarded_for_when_proxy_untrusted(client, monkeypatch):
    from deskid.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("AUTH_RATE_LIMIT_TRUST_PROXY", "false")
    settings = get_settings()
    assert settings.rate_limit_trust_proxy is False

    # The TestClient always uses 127.0.0.1 as transport IP, so the forwarded header
    # should be ignored and the request should be rate-limited based on 127.0.0.1.
    for _ in range(10):
        r = client.post(
            "/v1/auth/login",
            json={"email": "untrusted@example.com", "password": "wrong"},
            headers={"X-Forwarded-For": "203.0.113.99"},
        )
    r = client.post(
        "/v1/auth/login",
        json={"email": "untrusted@example.com", "password": "wrong"},
        headers={"X-Forwarded-For": "203.0.113.99"},
    )
    assert r.status_code == 429


def test_register_logs_mail_failure(client, monkeypatch, caplog):
    from deskid.routes import auth

    def _raise(*args, **kwargs):
        raise RuntimeError("mail down")

    monkeypatch.setattr(auth, "send_mail", _raise)

    with caplog.at_level("WARNING", logger="deskid.auth"):
        r = client.post(
            "/v1/auth/register",
            json={"email": "mailfail@example.com", "password": "password123"},
        )
    assert r.status_code == 200
    assert "register_mail_failed" in caplog.text
    assert "mail down" in caplog.text



# ---------------------------------------------------------------------------
# H1 + H2 — email verification gate and account lockout
# ---------------------------------------------------------------------------


def _verify_email_for_test(client, email: str) -> None:
    """Create and consume a verification token for the given user (test helper)."""
    from deskid.db import get_db
    from deskid.models import User
    from deskid.services import create_verification_token

    db = next(get_db())
    user = db.query(User).filter(User.email == email).one()
    token = create_verification_token(db, user)
    r = client.post("/v1/auth/verify-email", json={"token": token})
    assert r.status_code == 200


def test_login_blocked_without_email_verification(client, monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRE_EMAIL_VERIFICATION", "true")
    from deskid.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/v1/auth/register",
        json={"email": "unverified@example.com", "password": "password123"},
    )
    r = client.post(
        "/v1/auth/login",
        json={"email": "unverified@example.com", "password": "password123"},
    )
    assert r.status_code == 401


def test_login_succeeds_after_email_verification(client, monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRE_EMAIL_VERIFICATION", "true")
    from deskid.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/v1/auth/register",
        json={"email": "verified@example.com", "password": "password123"},
    )
    _verify_email_for_test(client, "verified@example.com")
    r = client.post(
        "/v1/auth/login",
        json={"email": "verified@example.com", "password": "password123"},
    )
    assert r.status_code == 200


def test_account_lockout_after_failed_logins(client, monkeypatch):
    monkeypatch.setenv("AUTH_ACCOUNT_LOCKOUT_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AUTH_ACCOUNT_LOCKOUT_DURATION_SECONDS", "60")
    from deskid.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/v1/auth/register",
        json={"email": "lockme@example.com", "password": "password123"},
    )

    # Three failed attempts.
    for _ in range(3):
        r = client.post(
            "/v1/auth/login",
            json={"email": "lockme@example.com", "password": "wrong"},
        )
        assert r.status_code == 401

    # Even the correct password should now be rejected (account locked).
    r = client.post(
        "/v1/auth/login",
        json={"email": "lockme@example.com", "password": "password123"},
    )
    assert r.status_code == 401


def test_successful_login_resets_failed_attempts(client, monkeypatch):
    monkeypatch.setenv("AUTH_ACCOUNT_LOCKOUT_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AUTH_ACCOUNT_LOCKOUT_DURATION_SECONDS", "60")
    from deskid.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/v1/auth/register",
        json={"email": "resetattempts@example.com", "password": "password123"},
    )

    # Two failed attempts.
    for _ in range(2):
        client.post(
            "/v1/auth/login",
            json={"email": "resetattempts@example.com", "password": "wrong"},
        )

    # Successful login resets the counter.
    r = client.post(
        "/v1/auth/login",
        json={"email": "resetattempts@example.com", "password": "password123"},
    )
    assert r.status_code == 200

    # Two more failed attempts should NOT lock because counter was reset.
    for _ in range(2):
        client.post(
            "/v1/auth/login",
            json={"email": "resetattempts@example.com", "password": "wrong"},
        )

    r = client.post(
        "/v1/auth/login",
        json={"email": "resetattempts@example.com", "password": "password123"},
    )
    assert r.status_code == 200



def test_account_lockout_expires(client, monkeypatch):
    monkeypatch.setenv("AUTH_ACCOUNT_LOCKOUT_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("AUTH_ACCOUNT_LOCKOUT_DURATION_SECONDS", "1")
    from deskid.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/v1/auth/register",
        json={"email": "expirelock@example.com", "password": "password123"},
    )

    # Lock the account.
    for _ in range(2):
        client.post(
            "/v1/auth/login",
            json={"email": "expirelock@example.com", "password": "wrong"},
        )
    r = client.post(
        "/v1/auth/login",
        json={"email": "expirelock@example.com", "password": "password123"},
    )
    assert r.status_code == 401

    import time

    time.sleep(1.1)

    # After lockout duration, login should succeed.
    r = client.post(
        "/v1/auth/login",
        json={"email": "expirelock@example.com", "password": "password123"},
    )
    assert r.status_code == 200



# ---------------------------------------------------------------------------
# Operator / business-user persona tests
# ---------------------------------------------------------------------------


def test_operator_can_query_audit_log_with_filters(client):
    """Platform admin can filter audit events by action and actor."""
    admin_tokens = client.post(
        "/v1/auth/register",
        json={"email": "opadmin@example.com", "password": "password123"},
    ).json()
    client.post("/v1/auth/login", json={"email": "opadmin@example.com", "password": "password123"})

    r = client.get(
        "/v1/admin/audit?action=user.login&limit=5",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert all(e["action"] == "user.login" for e in body["events"])


def test_operator_grant_action_appears_in_audit_log(client):
    """Assigning a product grant emits an auditable admin event."""
    admin = client.post(
        "/v1/auth/register",
        json={"email": "opgrantadmin@example.com", "password": "password123"},
    ).json()
    user = client.post(
        "/v1/auth/register",
        json={"email": "opgrantuser@example.com", "password": "password123"},
    ).json()
    user_id = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    ).json()["id"]

    r = client.post(
        "/v1/admin/grants",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"user_id": user_id, "audience": "operator-product", "role": "viewer"},
    )
    assert r.status_code == 200

    from deskid.db import get_db
    from deskid.models import AuditLogEvent

    db = next(get_db())
    event = db.query(AuditLogEvent).filter(AuditLogEvent.action == "admin.set_grant").first()
    assert event is not None
    assert event.actor_type == "admin"
    assert event.details is not None


def test_operator_can_suspend_and_activate_user(client):
    """Platform admin can suspend and re-activate a user account."""
    admin = client.post(
        "/v1/auth/register",
        json={"email": "opsuspendadmin@example.com", "password": "password123"},
    ).json()
    user = client.post(
        "/v1/auth/register",
        json={"email": "opsuspenduser@example.com", "password": "password123"},
    ).json()
    user_id = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    ).json()["id"]

    r = client.patch(
        f"/v1/admin/users/{user_id}/active",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"is_active": False},
    )
    assert r.status_code == 200

    # Suspended user cannot log in.
    r = client.post(
        "/v1/auth/login",
        json={"email": "opsuspenduser@example.com", "password": "password123"},
    )
    assert r.status_code == 401

    # Re-activate.
    r = client.patch(
        f"/v1/admin/users/{user_id}/active",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"is_active": True},
    )
    assert r.status_code == 200

    r = client.post(
        "/v1/auth/login",
        json={"email": "opsuspenduser@example.com", "password": "password123"},
    )
    assert r.status_code == 200


def test_gdpr_export_contains_expected_data(client):
    """User data export contains all personal data categories for compliance review."""
    tokens = client.post(
        "/v1/auth/register",
        json={"email": "gdpr@example.com", "password": "password123", "display_name": "GDPR User"},
    ).json()
    r = client.get(
        "/v1/me/export",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["email"] == "gdpr@example.com"
    assert data["user"]["display_name"] == "GDPR User"
    assert "identities" in data
    assert "memberships" in data
    assert "grants" in data
    assert "refresh_tokens" in data
    assert "audit_events" in data


def test_config_rejects_missing_required_values(monkeypatch):
    """The service fails closed when required deployment values are missing."""
    from deskid.config import Settings, get_settings

    get_settings.cache_clear()
    # Set to empty strings so they override any .env file values.
    monkeypatch.setenv("AUTH_DATABASE_URL", "")
    monkeypatch.setenv("AUTH_ISSUER", "")

    with pytest.raises(ValueError, match="AUTH_DATABASE_URL is required"):
        Settings()

    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Blocker fixes — additional security behavior tests
# ---------------------------------------------------------------------------


def test_registration_closed_by_default(client, monkeypatch, tmp_path):
    """With open_registration=False and no bootstrap token, registration is rejected."""
    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    from deskid.db import init_db, reset_engine
    from deskid.app import create_app

    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'closed.db'}")
    monkeypatch.setenv("AUTH_OPEN_REGISTRATION", "false")
    monkeypatch.setenv("AUTH_BOOTSTRAP_TOKEN", "")
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()
    init_db()

    with TestClient(create_app()) as c:
        r = c.post("/v1/auth/register", json={
            "email": "closed@example.com",
            "password": "password123",
        })
        assert r.status_code == 403
        assert "closed" in r.json()["error"].lower()

    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()


def test_first_registration_requires_bootstrap_token(client, monkeypatch, tmp_path):
    """Closed registration allows the first user only with a valid bootstrap token."""
    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    from deskid.db import init_db, reset_engine
    from deskid.app import create_app

    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'bootstrap.db'}")
    monkeypatch.setenv("AUTH_OPEN_REGISTRATION", "false")
    monkeypatch.setenv("AUTH_BOOTSTRAP_TOKEN", "secret-bootstrap-123")
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()
    init_db()

    with TestClient(create_app()) as c:
        # Missing bootstrap token is rejected.
        r = c.post("/v1/auth/register", json={
            "email": "nobootstrap@example.com",
            "password": "password123",
        })
        assert r.status_code == 403

        # Wrong bootstrap token is rejected.
        r = c.post("/v1/auth/register", json={
            "email": "wrongbootstrap@example.com",
            "password": "password123",
            "bootstrap_token": "wrong",
        })
        assert r.status_code == 403

        # Correct bootstrap token creates the first admin and issues tokens.
        r = c.post("/v1/auth/register", json={
            "email": "admin@example.com",
            "password": "password123",
            "bootstrap_token": "secret-bootstrap-123",
        })
        assert r.status_code == 200
        tokens = r.json()
        assert tokens["access_token"]
        me = c.get("/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert me.json()["is_platform_admin"] is True

        # Subsequent registrations remain closed.
        r2 = c.post("/v1/auth/register", json={
            "email": "second@example.com",
            "password": "password123",
        })
        assert r2.status_code == 403

    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()


def test_registration_does_not_issue_tokens_when_verification_required(client, monkeypatch, tmp_path):
    """When require_email_verification is true, signup returns no product-scoped tokens."""
    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    from deskid.db import init_db, reset_engine
    from deskid.app import create_app

    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'verify.db'}")
    monkeypatch.setenv("AUTH_REQUIRE_EMAIL_VERIFICATION", "true")
    monkeypatch.setenv("AUTH_OPEN_REGISTRATION", "true")
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()
    init_db()

    with TestClient(create_app()) as c:
        r = c.post("/v1/auth/register", json={
            "email": "verifygate@example.com",
            "password": "password123",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["verification_required"] is True
        assert body.get("access_token") is None
        assert body.get("refresh_token") is None

        # The user cannot use Auth endpoints until verified.
        me = c.get("/v1/auth/me", headers={"Authorization": f"Bearer {body.get('access_token', 'x')}"})
        assert me.status_code == 401

    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()


def test_oauth_cannot_take_over_unverified_password_account(client, monkeypatch, tmp_path):
    """OAuth sign-in with the same email as an unverified password account is rejected."""
    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    from deskid.db import init_db, reset_engine
    from deskid.app import create_app
    from deskid.services import find_or_create_oauth_user

    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'oauth.db'}")
    monkeypatch.setenv("AUTH_OPEN_REGISTRATION", "true")
    monkeypatch.setenv("AUTH_REQUIRE_EMAIL_VERIFICATION", "true")
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()
    init_db()

    with TestClient(create_app()) as c:
        c.post("/v1/auth/register", json={
            "email": "shared@example.com",
            "password": "password123",
        })

    from deskid.db import get_db
    from deskid.models import User

    db = next(get_db())
    password_user = db.query(User).filter(User.email == "shared@example.com").one()
    assert password_user.email_verified_at is None

    # OAuth must not be able to link to or replace an unverified password account.
    with pytest.raises(ValueError, match="not verified"):
        find_or_create_oauth_user(
            db,
            provider="google",
            provider_subject="oauth-subject-123",
            email="shared@example.com",
            display_name="OAuth User",
        )

    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()


def test_refresh_blocked_for_suspended_user(client):
    """A suspended user cannot rotate refresh tokens to extend their session."""
    admin = client.post("/v1/auth/register", json={
        "email": "refreshadmin@example.com",
        "password": "password123",
    }).json()
    user = client.post("/v1/auth/register", json={
        "email": "refreshsuspend@example.com",
        "password": "password123",
    }).json()
    user_id = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    ).json()["id"]

    # Suspend the user.
    r = client.patch(
        f"/v1/admin/users/{user_id}/active",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"is_active": False},
    )
    assert r.status_code == 200

    # Refresh should now fail.
    refresh = client.post("/v1/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert refresh.status_code == 401


def test_verify_email_rate_limit(client, monkeypatch):
    """The verify-email endpoint is rate-limited per IP."""
    monkeypatch.setattr("deskid.routes.auth.send_mail", lambda p: {"id": "x"})
    client.post("/v1/auth/register", json={
        "email": "verifyrl@example.com",
        "password": "password123",
    })

    limit = 10
    last_status = 200
    for i in range(limit + 1):
        r = client.post("/v1/auth/verify-email", json={"token": f"invalid-{i}"})
        last_status = r.status_code
    assert last_status == 429


def test_reset_password_rate_limit(client):
    """The reset-password endpoint is rate-limited per IP."""
    last_status = 200
    for i in range(6):
        r = client.post("/v1/auth/reset-password", json={
            "token": f"invalid-{i}",
            "password": "password123",
        })
        last_status = r.status_code
    assert last_status == 429


def test_landing_page_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"DeskID" in r.content


def test_seo_endpoints_served(client):
    r_robots = client.get("/robots.txt")
    assert r_robots.status_code == 200
    assert b"User-agent:" in r_robots.content

    r_sitemap = client.get("/sitemap.xml")
    assert r_sitemap.status_code == 200
    assert b"<urlset" in r_sitemap.content


def test_admin_console_served(client):
    r = client.get("/admin/console")
    assert r.status_code == 200
    assert b"DeskID" in r.content


def test_health_returns_503_when_keys_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'h.db'}")
    monkeypatch.setenv("AUTH_ISSUER", "https://auth.test.local")
    monkeypatch.setenv("AUTH_OPEN_REGISTRATION", "true")
    monkeypatch.setenv("AUTH_REQUIRE_EMAIL_VERIFICATION", "false")
    monkeypatch.setenv("AUTH_JWT_PRIVATE_KEY", "")
    monkeypatch.setenv("AUTH_JWT_PUBLIC_KEY", "")
    monkeypatch.setenv("AUTH_JWT_PRIVATE_KEY_FILE", "")
    monkeypatch.setenv("AUTH_JWT_PUBLIC_KEY_FILE", "")
    from deskid.config import get_settings
    from deskid.crypto import _ensure_keys
    from deskid.db import init_db, reset_engine
    from deskid.app import create_app
    from fastapi.testclient import TestClient

    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()
    init_db()
    with TestClient(create_app()) as c:
        r = c.get("/health")
    assert r.status_code == 503
    assert r.json()["status"] == "degraded"
    get_settings.cache_clear()
    _ensure_keys.cache_clear()
    reset_engine()


def test_email_change_requires_reverification(client, monkeypatch):
    monkeypatch.setattr("deskid.routes.auth.send_mail", lambda p: {"id": "x"})
    tokens = client.post("/v1/auth/register", json={
        "email": "oldaddr@example.com",
        "password": "password123",
    }).json()
    r = client.patch(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"email": "newaddr@example.com"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "newaddr@example.com"
    from deskid.config import get_settings
    monkeypatch.setenv("AUTH_REQUIRE_EMAIL_VERIFICATION", "true")
    get_settings.cache_clear()
    denied = client.post("/v1/auth/login", json={"email": "newaddr@example.com", "password": "password123"})
    assert denied.status_code == 401
    get_settings.cache_clear()


def test_password_reset_revokes_refresh_tokens(client, monkeypatch):
    import re

    captured: dict = {}

    def fake_send(payload):
        captured["html"] = payload.get("html", "")
        return {"id": "x"}

    monkeypatch.setattr("deskid.routes.auth.send_mail", fake_send)
    tokens = client.post("/v1/auth/register", json={
        "email": "resetrev@example.com",
        "password": "password123",
    }).json()
    assert client.post("/v1/auth/forgot-password", json={"email": "resetrev@example.com"}).status_code == 200
    match = re.search(r"token=([^\"&]+)", captured.get("html", ""))
    assert match
    reset = client.post("/v1/auth/reset-password", json={"token": match.group(1), "password": "newpass123"})
    assert reset.status_code == 200
    refresh = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 401


def test_admin_user_search_and_pagination(client):
    admin = client.post("/v1/auth/register", json={"email": "pager@example.com", "password": "password123"}).json()
    client.post("/v1/auth/register", json={"email": "findme@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {admin['access_token']}"}
    r = client.get("/v1/admin/users?q=findme&limit=10", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert any(u["email"] == "findme@example.com" for u in body["users"])


def test_org_members_and_delete(client):
    owner = client.post("/v1/auth/register", json={"email": "orgown@example.com", "password": "password123"}).json()
    member = client.post("/v1/auth/register", json={"email": "orgmem@example.com", "password": "password123"}).json()
    member_id = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {member['access_token']}"}).json()["id"]
    org = client.post("/v1/orgs", headers={"Authorization": f"Bearer {owner['access_token']}"}, json={"name": "Team"}).json()
    added = client.post(
        f"/v1/orgs/{org['id']}/members",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
        json={"user_id": member_id, "role": "member"},
    )
    assert added.status_code == 200
    listed = client.get(f"/v1/orgs/{org['id']}/members", headers={"Authorization": f"Bearer {owner['access_token']}"})
    assert listed.status_code == 200
    assert len(listed.json()["members"]) == 2
    removed = client.delete(
        f"/v1/orgs/{org['id']}/members/{member_id}",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    assert removed.status_code == 200
    gone = client.delete(f"/v1/orgs/{org['id']}", headers={"Authorization": f"Bearer {owner['access_token']}"})
    assert gone.status_code == 200


def test_auth_ui_routes(client):
    r1 = client.get("/auth")
    assert r1.status_code == 200
    assert "DeskID" in r1.text
    assert "view-login" in r1.text

    r2 = client.get("/auth/ui")
    assert r2.status_code == 200
    assert "DeskID" in r2.text



def test_metrics_counts_register(client):
    client.post("/v1/auth/register", json={"email": "metric@example.com", "password": "password123"})
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.json()["counters"].get("auth_register", 0) >= 1


def test_audit_is_append_only_and_hashed(client):
    from deskid.db import get_engine
    from deskid.models import AuditLogEvent
    from sqlalchemy.orm import Session

    admin = client.post("/v1/auth/register", json={"email": "audhash@example.com", "password": "password123"}).json()
    # Trigger another audit event by logging in
    client.post(
        "/v1/auth/login",
        json={"email": "audhash@example.com", "password": "password123"},
    )

    r = client.get("/v1/admin/audit?limit=10", headers={"Authorization": f"Bearer {admin['access_token']}"})
    assert r.status_code == 200
    events = r.json()["events"]
    assert len(events) >= 2
    # events are ordered desc by occurred_at, so events[0] is newest and events[1] is older
    assert events[0]["integrity_hash"]
    assert events[0]["previous_hash"] == events[1]["integrity_hash"]

    session = Session(get_engine())
    row = session.get(AuditLogEvent, events[0]["id"])
    try:
        row.action = "tamper"
        session.commit()
        raise AssertionError("update should be blocked")
    except RuntimeError as exc:
        assert "append-only" in str(exc)
        session.rollback()
    finally:
        session.close()


def test_jwks_rotation_and_historical_keys(monkeypatch):
    import json
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from deskid.config import get_settings
    from deskid.crypto import decode_access_token, public_jwks, _ensure_keys
    from fastapi.testclient import TestClient
    from deskid.app import create_app

    # Generate old key pair
    old_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    old_priv_pem = old_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    old_pub_pem = old_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    # Generate current key pair
    new_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    new_priv_pem = new_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    new_pub_pem = new_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    # Configure server with new active key and old key in previous_keys
    prev_keys_json = json.dumps([{"kid": "deskid-old-1", "public_key": old_pub_pem}])
    monkeypatch.setenv("AUTH_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("AUTH_ISSUER", "https://auth.test.local")
    monkeypatch.setenv("AUTH_JWT_PRIVATE_KEY", new_priv_pem)
    monkeypatch.setenv("AUTH_JWT_PUBLIC_KEY", new_pub_pem)
    monkeypatch.setenv("AUTH_JWT_KID", "deskid-new-2")
    monkeypatch.setenv("AUTH_JWT_PREVIOUS_PUBLIC_KEYS", prev_keys_json)
    get_settings.cache_clear()
    _ensure_keys.cache_clear()

    # Sign a token with the OLD private key and kid deskid-old-1
    old_token = jwt.encode(
        {"sub": "user_old", "email": "old@example.com", "iss": "https://auth.test.local", "aud": ["deskid"]},
        old_priv_pem,
        algorithm="RS256",
        headers={"kid": "deskid-old-1"},
    )

    # Server should successfully decode the old token
    decoded = decode_access_token(old_token)
    assert decoded["sub"] == "user_old"

    # JWKS endpoint should advertise both keys
    app = create_app()
    with TestClient(app) as test_client:
        jwks_resp = test_client.get("/.well-known/jwks.json")
        assert jwks_resp.status_code == 200
        keys = jwks_resp.json()["keys"]
        assert len(keys) == 2
        kids = [k["kid"] for k in keys]
        assert "deskid-new-2" in kids
        assert "deskid-old-1" in kids

    get_settings.cache_clear()
    _ensure_keys.cache_clear()


def test_switch_org_scoping_and_forbidden(client):
    from deskid.crypto import decode_access_token

    # 1. Register user
    reg = client.post(
        "/v1/auth/register",
        json={"email": "orgswitcher@example.com", "password": "password123"},
    ).json()
    token_1 = reg["access_token"]
    claims_1 = decode_access_token(token_1)
    org_1_id = claims_1["org_id"]
    assert org_1_id is not None

    # 2. Create second org
    org_2_resp = client.post(
        "/v1/orgs",
        json={"name": "Second Org", "slug": "second-org"},
        headers={"Authorization": f"Bearer {token_1}"},
    )
    assert org_2_resp.status_code == 200
    org_2_id = org_2_resp.json()["id"]
    assert org_2_id != org_1_id

    # 3. Switch org to second org
    switch_resp = client.post(
        "/v1/auth/switch-org",
        json={"org_id": org_2_id},
        headers={"Authorization": f"Bearer {token_1}"},
    )
    assert switch_resp.status_code == 200
    token_2 = switch_resp.json()["access_token"]
    claims_2 = decode_access_token(token_2)
    assert claims_2["org_id"] == org_2_id
    assert claims_2["workspace_id"] == org_2_id

    # 4. Attempt to switch to an unauthorized random org ID
    unauth_resp = client.post(
        "/v1/auth/switch-org",
        json={"org_id": "00000000-0000-0000-0000-000000000000"},
        headers={"Authorization": f"Bearer {token_2}"},
    )
    assert unauth_resp.status_code == 403


def test_org_scoped_product_grants(client):
    from deskid.crypto import decode_access_token

    # 1. Register admin
    admin = client.post(
        "/v1/auth/register",
        json={"email": "grantadmin@example.com", "password": "password123"},
    ).json()
    admin_token = admin["access_token"]

    # 2. Register target user
    user = client.post(
        "/v1/auth/register",
        json={"email": "targetuser@example.com", "password": "password123"},
    ).json()
    user_token = user["access_token"]
    user_claims = decode_access_token(user_token)
    org_1_id = user_claims["org_id"]

    # 3. Create second org for target user
    org_2_resp = client.post(
        "/v1/orgs",
        json={"name": "Org Beta"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    org_2_id = org_2_resp.json()["id"]

    # 4. Admin grants user role "admin" on "keppler" in org_1, and role "viewer" on "keppler" in org_2
    g1 = client.post(
        "/v1/admin/grants",
        json={"user_id": user_claims["sub"], "audience": "keppler", "role": "admin", "org_id": org_1_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert g1.status_code == 200

    g2 = client.post(
        "/v1/admin/grants",
        json={"user_id": user_claims["sub"], "audience": "keppler", "role": "viewer", "org_id": org_2_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert g2.status_code == 200

    # 5. Switch to Org 1 -> token roles["keppler"] must be "admin"
    t1_resp = client.post(
        "/v1/auth/switch-org",
        json={"org_id": org_1_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert t1_resp.status_code == 200
    claims_org1 = decode_access_token(t1_resp.json()["access_token"])
    assert claims_org1["roles"]["keppler"] == "admin"

    # 6. Switch to Org 2 -> token roles["keppler"] must be "viewer"
    t2_resp = client.post(
        "/v1/auth/switch-org",
        json={"org_id": org_2_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert t2_resp.status_code == 200
    claims_org2 = decode_access_token(t2_resp.json()["access_token"])
    assert claims_org2["roles"]["keppler"] == "viewer"


def test_token_version_invalidation_on_password_change(client, monkeypatch):
    monkeypatch.setenv("AUTH_INTROSPECTION_API_KEY", "secret-key")
    from deskid.config import get_settings
    get_settings.cache_clear()

    # 1. Register user
    reg = client.post(
        "/v1/auth/register",
        json={"email": "versionuser@example.com", "password": "oldpassword123"},
    ).json()
    old_token = reg["access_token"]

    # 2. Introspect old token -> active
    intro1 = client.post(
        "/introspect",
        json={"token": old_token},
        headers={"Authorization": "Bearer secret-key"},
    )
    assert intro1.status_code == 200
    assert intro1.json()["active"] is True

    # 3. User changes password (bumps token_version)
    chg = client.post(
        "/v1/auth/me/change-password",
        json={"current_password": "oldpassword123", "new_password": "newpassword123"},
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert chg.status_code == 200

    # 4. Old token introspect -> active: False due to token_version mismatch
    intro2 = client.post(
        "/introspect",
        json={"token": old_token},
        headers={"Authorization": "Bearer secret-key"},
    )
    assert intro2.status_code == 200
    assert intro2.json()["active"] is False


def test_reconciliation_events_feed(client):
    # 1. Register admin
    admin = client.post(
        "/v1/auth/register",
        json={"email": "feedadmin@example.com", "password": "password123"},
    ).json()
    admin_token = admin["access_token"]

    # 2. Create org
    client.post(
        "/v1/orgs",
        json={"name": "Recon Org"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 3. Query reconciliation feed
    resp = client.get(
        "/v1/admin/reconciliation/events?limit=50",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert len(data["events"]) >= 2
    actions = [e["action"] for e in data["events"]]
    assert "user.register" in actions
    assert "org.create" in actions


def test_audit_chain_verifier_script(client):
    import subprocess
    from deskid.db import get_engine

    # 1. Register admin to populate audit events
    admin = client.post(
        "/v1/auth/register",
        json={"email": "verifier@example.com", "password": "password123"},
    ).json()
    client.post(
        "/v1/orgs",
        json={"name": "Verified Org"},
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )

    # 2. Export audit log to JSON
    events_resp = client.get(
        "/v1/admin/reconciliation/events",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )
    assert events_resp.status_code == 200

    import tempfile
    with tempfile.NamedTemporaryFile("w+", suffix=".json") as tmp:
        import json
        json.dump(events_resp.json()["events"], tmp)
        tmp.flush()

        res = subprocess.run(
            ["python3", "scripts/verify_audit_chain.py", "--file", tmp.name],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        assert "VERIFICATION SUCCESS" in res.stdout


def test_service_definition_crud(client):
    admin = client.post(
        "/v1/auth/register",
        json={"email": "svcadmin@example.com", "password": "password123"},
    ).json()
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    regular_user = client.post(
        "/v1/auth/register",
        json={"email": "regular@example.com", "password": "password123"},
    ).json()
    user_headers = {"Authorization": f"Bearer {regular_user['access_token']}"}

    # 1. Non-admin cannot register service (403)
    non_admin_reg = client.post(
        "/v1/admin/services",
        json={"id": "service-alpha", "name": "Service Alpha", "allowed_roles": ["admin", "viewer"]},
        headers=user_headers,
    )
    assert non_admin_reg.status_code == 403

    # 2. Admin registers service
    reg_resp = client.post(
        "/v1/admin/services",
        json={
            "id": "service-alpha",
            "name": "Service Alpha",
            "description": "Alpha description",
            "allowed_roles": ["catalog-admin", "schema-manager", "data-reader"],
            "default_role": "data-reader",
        },
        headers=admin_headers,
    )
    assert reg_resp.status_code == 201
    svc_data = reg_resp.json()
    assert svc_data["id"] == "service-alpha"
    assert svc_data["name"] == "Service Alpha"
    assert svc_data["allowed_roles"] == ["catalog-admin", "schema-manager", "data-reader"]
    assert svc_data["default_role"] == "data-reader"

    # Duplicate registration returns 409
    dup_resp = client.post(
        "/v1/admin/services",
        json={"id": "service-alpha", "name": "Duplicate", "allowed_roles": ["admin"]},
        headers=admin_headers,
    )
    assert dup_resp.status_code == 409

    # Invalid default_role returns 422
    inv_def = client.post(
        "/v1/admin/services",
        json={"id": "service-beta", "name": "Beta", "allowed_roles": ["admin"], "default_role": "nonexistent"},
        headers=admin_headers,
    )
    assert inv_def.status_code == 422

    # 3. List services
    list_resp = client.get("/v1/admin/services", headers=admin_headers)
    assert list_resp.status_code == 200
    services = list_resp.json()["services"]
    assert any(s["id"] == "service-alpha" for s in services)

    # 4. Get service by ID
    get_resp = client.get("/v1/admin/services/service-alpha", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Service Alpha"

    # 5. Update service
    upd_resp = client.put(
        "/v1/admin/services/service-alpha",
        json={"name": "Service Alpha Updated", "allowed_roles": ["catalog-admin", "data-reader", "curator"]},
        headers=admin_headers,
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["name"] == "Service Alpha Updated"
    assert "curator" in upd_resp.json()["allowed_roles"]

    # 6. Delete service
    del_resp = client.delete("/v1/admin/services/service-alpha", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    # Confirm deletion
    get_del = client.get("/v1/admin/services/service-alpha", headers=admin_headers)
    assert get_del.status_code == 404


def test_custom_roles_grant_validation_and_token_embedding(client):
    from deskid.crypto import decode_access_token

    # 1. Admin setup
    admin = client.post(
        "/v1/auth/register",
        json={"email": "customroleadmin@example.com", "password": "password123"},
    ).json()
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    # 2. Register two distinct services with bespoke role taxonomies
    s1 = client.post(
        "/v1/admin/services",
        json={
            "id": "service-catalog",
            "name": "Data Catalog Service",
            "allowed_roles": ["catalog-admin", "curator", "consumer"],
            "default_role": "consumer",
        },
        headers=admin_headers,
    )
    assert s1.status_code == 201

    s2 = client.post(
        "/v1/admin/services",
        json={
            "id": "service-compute",
            "name": "Distributed Compute Engine",
            "allowed_roles": ["cluster-admin", "job-runner", "metrics-viewer"],
            "default_role": "metrics-viewer",
        },
        headers=admin_headers,
    )
    assert s2.status_code == 201

    # 3. Register target user
    user = client.post(
        "/v1/auth/register",
        json={"email": "grantee@example.com", "password": "password123"},
    ).json()
    user_token = user["access_token"]
    user_claims = decode_access_token(user_token)
    user_id = user_claims["sub"]
    org_1_id = user_claims["org_id"]

    # 4. Attempt to grant an invalid role for service-catalog (422)
    inv_grant = client.post(
        "/v1/admin/grants",
        json={"user_id": user_id, "audience": "service-catalog", "role": "unsupported-role"},
        headers=admin_headers,
    )
    assert inv_grant.status_code == 422
    assert "not allowed for service" in inv_grant.json()["error"]

    # 5. Grant valid custom role 'curator' globally (org_id=None) on service-catalog
    g1 = client.post(
        "/v1/admin/grants",
        json={"user_id": user_id, "audience": "service-catalog", "role": "curator"},
        headers=admin_headers,
    )
    assert g1.status_code == 200

    # 6. Grant valid custom role 'job-runner' in org_1 on service-compute
    g2 = client.post(
        "/v1/admin/grants",
        json={"user_id": user_id, "audience": "service-compute", "role": "job-runner", "org_id": org_1_id},
        headers=admin_headers,
    )
    assert g2.status_code == 200

    # 7. User switches into org_1 -> issued token contains custom roles for both audiences
    switch_resp = client.post(
        "/v1/auth/switch-org",
        json={"org_id": org_1_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert switch_resp.status_code == 200
    token_claims = decode_access_token(switch_resp.json()["access_token"])

    # Verify audience aggregation and specific custom roles
    assert "deskid" in token_claims["aud"]
    assert "service-catalog" in token_claims["aud"]
    assert "service-compute" in token_claims["aud"]

    assert token_claims["roles"]["service-catalog"] == "curator"
    assert token_claims["roles"]["service-compute"] == "job-runner"



