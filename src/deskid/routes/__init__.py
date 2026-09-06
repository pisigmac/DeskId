"""Route package."""

from deskid.routes.admin import router as admin_router
from deskid.routes.auth import router as auth_router
from deskid.routes.jwks import router as jwks_router
from deskid.routes.me import router as me_router
from deskid.routes.oauth import router as oauth_router
from deskid.routes.orgs import router as orgs_router

__all__ = ["auth_router", "oauth_router", "orgs_router", "admin_router", "jwks_router", "me_router"]
