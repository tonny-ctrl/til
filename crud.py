#!/usr/bin/env python3
"""Tiny JSON-backed CRUD store with a `daily` command for scheduled commits.

Usage:
  python crud.py create --title "Idea" --body "Build X"
  python crud.py list
  python crud.py get <id>
  python crud.py update <id> --title "New title" --body "New body"
  python crud.py delete <id>
  python crud.py daily            # used by the GitHub Action
"""
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "entries.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load() -> dict:
    if not DATA_FILE.exists():
        return {"entries": []}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save(db: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(DATA_FILE)  # atomic write


def find(db: dict, id_prefix: str) -> dict:
    matches = [e for e in db["entries"] if e["id"].startswith(id_prefix)]
    if not matches:
        sys.exit(f"No entry matches id '{id_prefix}'")
    if len(matches) > 1:
        sys.exit(f"Id prefix '{id_prefix}' is ambiguous ({len(matches)} matches)")
    return matches[0]


# ---- CRUD operations -------------------------------------------------------

def create(title: str, body: str = "", kind: str = "note") -> dict:
    db = load()
    entry = {
        "id": uuid.uuid4().hex[:12],
        "kind": kind,
        "title": title,
        "body": body,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    db["entries"].append(entry)
    save(db)
    return entry


def read_all() -> list:
    return load()["entries"]


def read_one(id_prefix: str) -> dict:
    return find(load(), id_prefix)


def update(id_prefix: str, title: str | None = None, body: str | None = None) -> dict:
    db = load()
    entry = find(db, id_prefix)
    if title is not None:
        entry["title"] = title
    if body is not None:
        entry["body"] = body
    entry["updated_at"] = now_iso()
    save(db)
    return entry


def delete(id_prefix: str) -> dict:
    db = load()
    entry = find(db, id_prefix)
    db["entries"].remove(entry)
    save(db)
    return entry


# ---- Daily job -------------------------------------------------------------

def daily() -> dict:
    """Create today's log entry, or update it if the job already ran today."""
    today = datetime.now(timezone.utc).date().isoformat()
    db = load()
    notes = [e for e in db["entries"] if e["kind"] == "note"]
    summary = f"{len(notes)} note(s) in store."

    existing = next(
        (e for e in db["entries"] if e["kind"] == "daily" and e["title"] == today), None
    )
    if existing:
        return update(existing["id"], body=summary)
    return create(title=today, body=summary, kind="daily")


# ---- CLI -------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="JSON-backed CRUD store")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create")
    c.add_argument("--title", required=True)
    c.add_argument("--body", default="")

    sub.add_parser("list")

    g = sub.add_parser("get")
    g.add_argument("id")

    u = sub.add_parser("update")
    u.add_argument("id")
    u.add_argument("--title")
    u.add_argument("--body")

    d = sub.add_parser("delete")
    d.add_argument("id")

    sub.add_parser("daily")

    args = p.parse_args()
    if args.cmd == "create":
        result = create(args.title, args.body)
    elif args.cmd == "list":
        result = read_all()
    elif args.cmd == "get":
        result = read_one(args.id)
    elif args.cmd == "update":
        result = update(args.id, args.title, args.body)
    elif args.cmd == "delete":
        result = delete(args.id)
    else:
        result = daily()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
