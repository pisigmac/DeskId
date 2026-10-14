"""Thin client for Mail service with support for service, console, and disabled modes."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from deskid.config import get_settings

logger = logging.getLogger(__name__)

# In-memory buffer of dispatched emails in console/dev mode (accessible by tests/dev tools)
DEV_MAILBOX: list[dict[str, Any]] = []


def clear_dev_mailbox() -> None:
    DEV_MAILBOX.clear()


def build_verification_email(to: str, token: str) -> dict[str, Any]:
    settings = get_settings()
    base_url = settings.spa_callback_url.rsplit("/", 1)[0] if settings.spa_callback_url else "http://localhost:5173"
    link = f"{base_url}/verify-email?token={token}"
    payload: dict[str, Any] = {
        "to": to,
        "subject": "Verify your DeskID account",
        "text": f"Please verify your email by visiting: {link}",
        "html": f'<p>Please <a href="{link}">verify your email</a>.</p>',
        "tags": ["auth", "verify-email"],
    }
    if settings.mail_from_email:
        payload["from"] = (
            f"{settings.mail_from_name} <{settings.mail_from_email}>"
            if settings.mail_from_name
            else settings.mail_from_email
        )
    return payload


def build_password_reset_email(to: str, token: str) -> dict[str, Any]:
    settings = get_settings()
    base_url = settings.spa_callback_url.rsplit("/", 1)[0] if settings.spa_callback_url else "http://localhost:5173"
    link = f"{base_url}/reset-password?token={token}"
    payload: dict[str, Any] = {
        "to": to,
        "subject": "Reset your DeskID password",
        "text": f"Reset your password by visiting: {link}",
        "html": f'<p><a href="{link}">Reset your password</a>.</p>',
        "tags": ["auth", "reset-password"],
    }
    if settings.mail_from_email:
        payload["from"] = (
            f"{settings.mail_from_name} <{settings.mail_from_email}>"
            if settings.mail_from_name
            else settings.mail_from_email
        )
    return payload


def build_magic_link_email(to: str, token: str, otp_code: str) -> dict[str, Any]:
    settings = get_settings()
    base_url = settings.spa_callback_url.rsplit("/", 1)[0] if settings.spa_callback_url else "http://localhost:5173"
    link = f"{base_url}/auth/magic-link?token={token}"
    payload: dict[str, Any] = {
        "to": to,
        "subject": f"Your DeskID Sign-in Code is {otp_code}",
        "text": (
            f"Your one-time 6-digit sign-in code is: {otp_code}\n\n"
            f"Alternatively, sign in instantly using this link:\n{link}\n\n"
            f"This code will expire in {settings.otp_ttl_minutes} minutes."
        ),
        "html": (
            f'<div style="font-family: sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">'
            f'<h2>DeskID Sign In</h2>'
            f'<p>Use this one-time code to sign in to your account:</p>'
            f'<div style="font-size: 32px; font-weight: 700; letter-spacing: 4px; padding: 12px; background: #f1f5f9; border-radius: 8px; text-align: center; color: #4f46e5; margin: 20px 0;">{otp_code}</div>'
            f'<p>Or click below to sign in directly without typing:</p>'
            f'<p><a href="{link}" style="display: inline-block; padding: 10px 20px; background: #4f46e5; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600;">Sign in with 1-Click Link</a></p>'
            f'<p style="color: #64748b; font-size: 12px; margin-top: 24px;">This code expires in {settings.otp_ttl_minutes} minutes. If you did not request this, you can safely ignore this email.</p>'
            f'</div>'
        ),
        "tags": ["auth", "magic-link", "otp"],
        "otp_code": otp_code,
        "token": token,
    }
    if settings.mail_from_email:
        payload["from"] = (
            f"{settings.mail_from_name} <{settings.mail_from_email}>"
            if settings.mail_from_name
            else settings.mail_from_email
        )
    return payload


def send_mail(payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    mode = (settings.mail_mode or "service").lower().strip()

    # 1. Disabled mode
    if mode == "disabled":
        logger.info("mail_mode_disabled skipping delivery to=%s subject=%s", payload.get("to"), payload.get("subject"))
        return {"status": "disabled", "ok": True}

    # 2. Console mode (or fallback when mail credentials are not configured in dev)
    if mode == "console" or (mode == "service" and not (settings.mail_base_url and settings.mail_api_key)):
        logger.info(
            "\n" + "=" * 60 + "\n"
            "[DEV MAIL DISPATCHED]\n"
            "To: %s\n"
            "Subject: %s\n"
            "Body:\n%s\n"
            + "=" * 60,
            payload.get("to"),
            payload.get("subject"),
            payload.get("text"),
        )
        DEV_MAILBOX.append(payload)
        return {"status": "console", "ok": True}

    # 3. Service mode (Production HTTP call)
    base_url = settings.mail_base_url
    api_key = settings.mail_api_key
    if not base_url or not api_key:
        raise RuntimeError("Mail service is not configured (AUTH_MAIL_BASE_URL / AUTH_MAIL_API_KEY)")

    with httpx.Client(timeout=10.0) as client:
        res = client.post(
            f"{base_url}/v1/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        res.raise_for_status()
        return res.json()
