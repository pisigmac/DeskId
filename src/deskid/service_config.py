from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deskid.config import Settings, get_settings
from deskid.models import ServiceDefinition


def build_service_env_content(svc: ServiceDefinition, settings: Settings) -> str:
    issuer = settings.issuer.rstrip("/")
    jwks_url = f"{issuer}/.well-known/jwks.json"
    allowed_roles = ",".join(svc.allowed_roles or [])
    default_role = svc.default_role or ""

    return (
        f"# ==============================================================================\n"
        f"# DeskID Integration Configuration for Service: {svc.name} ({svc.id})\n"
        f"# Generated automatically by DeskID on {datetime.now(timezone.utc).isoformat()}\n"
        f"# ==============================================================================\n\n"
        f"AUTH_MODE=deskid\n"
        f"DESKID_ISSUER={issuer}\n"
        f"DESKID_JWKS_URL={jwks_url}\n"
        f"DESKID_AUDIENCE={svc.id}\n"
        f"DESKID_ALLOWED_ROLES={allowed_roles}\n"
        f"DESKID_DEFAULT_ROLE={default_role}\n"
    )


def build_service_json_content(svc: ServiceDefinition, settings: Settings) -> dict[str, Any]:
    issuer = settings.issuer.rstrip("/")
    return {
        "service_id": svc.id,
        "name": svc.name,
        "description": svc.description or "",
        "issuer": issuer,
        "jwks_url": f"{issuer}/.well-known/jwks.json",
        "audience": svc.id,
        "allowed_roles": svc.allowed_roles or [],
        "default_role": svc.default_role or "",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def save_service_integration_files(
    svc: ServiceDefinition,
    settings: Settings | None = None,
) -> dict[str, Any]:
    if settings is None:
        settings = get_settings()

    integrations_dir = getattr(settings, "integrations_dir", "integrations")
    export_dir = Path(integrations_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    env_path = export_dir / f"{svc.id}.env"
    json_path = export_dir / f"{svc.id}.json"

    env_content = build_service_env_content(svc, settings)
    json_data = build_service_json_content(svc, settings)

    env_path.write_text(env_content, encoding="utf-8")
    json_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")

    return {
        "env_path": str(env_path),
        "json_path": str(json_path),
        "env_content": env_content,
        "json_content": json_data,
    }
