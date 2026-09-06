"""Admin user and product-grant management."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from deskid.db import get_db
from deskid.middleware import get_request_context
from deskid.models import AuditLogEvent, ProductGrant, ServiceDefinition, User
from deskid.routes.auth import current_user
from deskid.schemas import (
    GrantRequest,
    ServiceCreateRequest,
    ServiceOut,
    ServiceUpdateRequest,
    SetUserActiveRequest,
    UserOut,
)
from deskid.services import emit_audit, set_user_active, user_to_out

logger = logging.getLogger("deskid.admin")
router = APIRouter(prefix="/admin", tags=["admin"])


def service_to_out(svc: ServiceDefinition) -> dict:
    return {
        "id": svc.id,
        "name": svc.name,
        "description": svc.description,
        "allowed_roles": svc.allowed_roles or [],
        "default_role": svc.default_role,
        "created_at": svc.created_at.isoformat() if svc.created_at else "",
        "updated_at": svc.updated_at.isoformat() if svc.updated_at else "",
    }



def require_platform_admin(user: User = Depends(current_user)) -> User:
    if not user.is_platform_admin:
        raise HTTPException(status_code=403, detail="Platform admin required")
    return user


@router.get("/users")
def list_users(
    q: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(User)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(User.email.ilike(term), User.display_name.ilike(term)))
    total = query.count()
    users = query.order_by(User.created_at).offset(offset).limit(limit).all()
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "users": [user_to_out(u) for u in users],
    }


@router.patch("/users/{user_id}/active")
def set_user_active_status(
    user_id: str,
    body: SetUserActiveRequest,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    target = db.query(User).filter(User.id == user_id).one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    set_user_active(db, target, is_active=body.is_active)
    action = "admin.activate_user" if body.is_active else "admin.suspend_user"
    ctx = get_request_context()
    emit_audit(
        db,
        action=action,
        actor_type="admin",
        actor_id=admin.id,
        resource_type="user",
        resource_id=user_id,
        ip_address=ctx.get("ip"),
        user_agent=ctx.get("user_agent"),
    )
    logger.info("%s admin=%s target=%s", action, admin.id, user_id)
    return {"ok": True, "user_id": user_id, "is_active": body.is_active}


@router.post("/grants")
def set_grant(
    body: GrantRequest,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(User).filter(User.id == body.user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    svc = db.query(ServiceDefinition).filter(ServiceDefinition.id == body.audience).one_or_none()
    if svc:
        if body.role not in svc.allowed_roles:
            raise HTTPException(
                status_code=422,
                detail=f"Role '{body.role}' is not allowed for service '{body.audience}'. Allowed roles: {svc.allowed_roles}",
            )
    else:
        if body.role not in {"admin", "operator", "viewer"}:
            raise HTTPException(status_code=400, detail="Invalid role")

    grant = (
        db.query(ProductGrant)
        .filter(
            ProductGrant.user_id == body.user_id,
            ProductGrant.org_id == body.org_id,
            ProductGrant.audience == body.audience,
        )
        .one_or_none()
    )
    if grant:
        grant.role = body.role
    else:
        db.add(ProductGrant(user_id=body.user_id, org_id=body.org_id, audience=body.audience, role=body.role))
    db.commit()
    ctx = get_request_context()
    emit_audit(
        db,
        action="admin.set_grant",
        actor_type="admin",
        actor_id=admin.id,
        resource_type="product_grant",
        resource_id=body.user_id,
        ip_address=ctx.get("ip"),
        user_agent=ctx.get("user_agent"),
        details={"audience": body.audience, "role": body.role, "org_id": body.org_id},
    )
    logger.info("admin.set_grant admin=%s user=%s audience=%s role=%s org=%s", admin.id, body.user_id, body.audience, body.role, body.org_id)
    return {"ok": True, "user_id": body.user_id, "audience": body.audience, "role": body.role}



@router.get("/audit")
def query_audit_log(
    action: str | None = None,
    actor_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    limit: int = 25,
    offset: int = 0,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    query = db.query(AuditLogEvent)
    if action:
        query = query.filter(AuditLogEvent.action == action)
    if actor_id:
        query = query.filter(AuditLogEvent.actor_id == actor_id)
    if resource_type:
        query = query.filter(AuditLogEvent.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLogEvent.resource_id == resource_id)

    total = query.count()
    events = (
        query.order_by(AuditLogEvent.occurred_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "events": [
            {
                "id": e.id,
                "occurred_at": e.occurred_at.isoformat(),
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "previous_hash": e.previous_hash,
                "integrity_hash": e.integrity_hash,
                "details": e.details,
            }
            for e in events
        ],
    }


@router.get("/reconciliation/events")
def reconciliation_events(
    since_id: str | None = None,
    since_timestamp: str | None = None,
    limit: int = 50,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Downstream consumer reconciliation feed (ordered chronologically ASC)."""
    limit = max(1, min(limit, 200))
    query = db.query(AuditLogEvent)

    if since_id:
        cursor_event = db.query(AuditLogEvent).filter(AuditLogEvent.id == since_id).one_or_none()
        if cursor_event:
            query = query.filter(
                (AuditLogEvent.occurred_at > cursor_event.occurred_at)
                | (
                    (AuditLogEvent.occurred_at == cursor_event.occurred_at)
                    & (AuditLogEvent.id > cursor_event.id)
                )
            )
    elif since_timestamp:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(since_timestamp)
            query = query.filter(AuditLogEvent.occurred_at > dt)
        except Exception:
            pass

    events = (
        query.order_by(AuditLogEvent.occurred_at.asc(), AuditLogEvent.id.asc())
        .limit(limit + 1)
        .all()
    )
    has_more = len(events) > limit
    returned_events = events[:limit]
    next_cursor = returned_events[-1].id if returned_events else None

    return {
        "events": [
            {
                "id": e.id,
                "occurred_at": e.occurred_at.isoformat(),
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "previous_hash": e.previous_hash,
                "integrity_hash": e.integrity_hash,
                "details": e.details,
            }
            for e in returned_events
        ],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


# ---------------------------------------------------------------------------
# Service & Custom Role Registry CRUD Endpoints
# ---------------------------------------------------------------------------


@router.post("/services", status_code=201)
def register_service(
    body: ServiceCreateRequest,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    existing = db.query(ServiceDefinition).filter(ServiceDefinition.id == body.id).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Service with id '{body.id}' already exists")

    if body.default_role and body.default_role not in body.allowed_roles:
        raise HTTPException(status_code=422, detail="default_role must be one of allowed_roles")

    svc = ServiceDefinition(
        id=body.id,
        name=body.name,
        description=body.description,
        allowed_roles=body.allowed_roles,
        default_role=body.default_role,
    )
    db.add(svc)
    db.commit()
    db.refresh(svc)

    ctx = get_request_context()
    emit_audit(
        db,
        action="admin.register_service",
        actor_type="admin",
        actor_id=admin.id,
        resource_type="service_definition",
        resource_id=svc.id,
        ip_address=ctx.get("ip"),
        user_agent=ctx.get("user_agent"),
        details={"name": svc.name, "allowed_roles": svc.allowed_roles, "default_role": svc.default_role},
    )
    logger.info("admin.register_service admin=%s service=%s", admin.id, svc.id)
    return service_to_out(svc)


@router.get("/services")
def list_services(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(ServiceDefinition)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(ServiceDefinition.id.ilike(term), ServiceDefinition.name.ilike(term)))
    total = query.count()
    services = query.order_by(ServiceDefinition.id).offset(offset).limit(limit).all()
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "services": [service_to_out(s) for s in services],
    }


@router.get("/services/{service_id}")
def get_service(
    service_id: str,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    svc = db.query(ServiceDefinition).filter(ServiceDefinition.id == service_id).one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return service_to_out(svc)


@router.put("/services/{service_id}")
def update_service(
    service_id: str,
    body: ServiceUpdateRequest,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    svc = db.query(ServiceDefinition).filter(ServiceDefinition.id == service_id).one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    if body.name is not None:
        svc.name = body.name
    if body.description is not None:
        svc.description = body.description
    if body.allowed_roles is not None:
        svc.allowed_roles = body.allowed_roles
    if body.default_role is not None:
        if body.default_role not in svc.allowed_roles:
            raise HTTPException(status_code=422, detail="default_role must be one of allowed_roles")
        svc.default_role = body.default_role

    db.commit()
    db.refresh(svc)

    ctx = get_request_context()
    emit_audit(
        db,
        action="admin.update_service",
        actor_type="admin",
        actor_id=admin.id,
        resource_type="service_definition",
        resource_id=svc.id,
        ip_address=ctx.get("ip"),
        user_agent=ctx.get("user_agent"),
        details={"name": svc.name, "allowed_roles": svc.allowed_roles, "default_role": svc.default_role},
    )
    logger.info("admin.update_service admin=%s service=%s", admin.id, svc.id)
    return service_to_out(svc)


@router.delete("/services/{service_id}")
def delete_service(
    service_id: str,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> dict:
    svc = db.query(ServiceDefinition).filter(ServiceDefinition.id == service_id).one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    db.delete(svc)
    db.commit()

    ctx = get_request_context()
    emit_audit(
        db,
        action="admin.delete_service",
        actor_type="admin",
        actor_id=admin.id,
        resource_type="service_definition",
        resource_id=service_id,
        ip_address=ctx.get("ip"),
        user_agent=ctx.get("user_agent"),
    )
    logger.info("admin.delete_service admin=%s service=%s", admin.id, service_id)
    return {"ok": True, "deleted": True, "service_id": service_id}

