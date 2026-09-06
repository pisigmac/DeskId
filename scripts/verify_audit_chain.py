#!/usr/bin/env python3
"""Cryptographic Audit Chain Integrity Verifier for DeskID.

Usage:
    # Verify from live database:
    AUTH_DATABASE_URL="sqlite+pysqlite:////tmp/deskid.db" python3 scripts/verify_audit_chain.py

    # Verify from exported JSON file:
    python3 scripts/verify_audit_chain.py --file audit_export.json
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def compute_event_hash(
    previous_hash: str | None,
    action: str,
    actor_type: str,
    actor_id: str | None,
    resource_type: str,
    resource_id: str | None,
    details: str | None,
) -> str:
    payload = "|".join(
        [
            previous_hash or "GENESIS",
            action,
            actor_type,
            actor_id or "",
            resource_type,
            resource_id or "",
            details or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_events(events: list[dict]) -> tuple[bool, str, int]:
    if not events:
        return True, "No audit events found.", 0

    # Sort events ascending by occurred_at / sequence
    sorted_events = sorted(events, key=lambda e: (e.get("occurred_at", ""), e.get("id", "")))
    expected_prev_hash = "GENESIS"

    for idx, e in enumerate(sorted_events):
        event_id = e.get("id")
        actual_prev = e.get("previous_hash") or "GENESIS"
        actual_hash = e.get("integrity_hash")

        if actual_prev != expected_prev_hash and idx != 0:
            return (
                False,
                f"Chain broken at event #{idx} (id={event_id}): expected previous_hash={expected_prev_hash}, got {actual_prev}",
                idx,
            )

        details_val = e.get("details")
        if isinstance(details_val, dict):
            details_str = json.dumps(details_val)
        else:
            details_str = details_val

        computed = compute_event_hash(
            previous_hash=actual_prev,
            action=e.get("action", ""),
            actor_type=e.get("actor_type", ""),
            actor_id=e.get("actor_id"),
            resource_type=e.get("resource_type", ""),
            resource_id=e.get("resource_id"),
            details=details_str,
        )

        if computed != actual_hash:
            return (
                False,
                f"Tampered record at event #{idx} (id={event_id}): recorded integrity_hash={actual_hash}, computed={computed}",
                idx,
            )

        expected_prev_hash = actual_hash

    return True, f"All {len(sorted_events)} events successfully verified with intact cryptographic chain.", len(sorted_events)


def main():
    parser = argparse.ArgumentParser(description="Verify DeskID audit log cryptographic chain integrity")
    parser.add_argument("--file", help="Path to exported JSON audit log file")
    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File {args.file} does not exist.")
            sys.exit(1)
        data = json.loads(file_path.read_text(encoding="utf-8"))
        events = data if isinstance(data, list) else data.get("events", [])
    else:
        db_url = os.environ.get("AUTH_DATABASE_URL")
        if not db_url:
            print("Error: Specify --file or set AUTH_DATABASE_URL.")
            sys.exit(1)
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, occurred_at, actor_type, actor_id, action, resource_type, resource_id, details, previous_hash, integrity_hash FROM audit_log_events ORDER BY occurred_at ASC, id ASC")).mappings().all()
            events = [dict(r) for r in rows]

    ok, msg, count = verify_events(events)
    if ok:
        print(f"✅ VERIFICATION SUCCESS: {msg}")
        sys.exit(0)
    else:
        print(f"❌ INTEGRITY VIOLATION: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
