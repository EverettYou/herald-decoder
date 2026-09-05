#!/usr/bin/env python3
"""Maintain the Herald Decoder's append-only discussion mailbox."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

AUTHORS = {"agent", "user"}
PRIORITIES = {"blocking", "high", "normal", "low"}
CATEGORIES = {"checkpoint", "scientific", "scope", "interpretation", "resource", "task", "other"}


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def path_for(project: str) -> Path:
    return Path(project).resolve() / "discussion" / "threads.json"


def load(project: str) -> tuple[Path, dict]:
    path = path_for(project)
    if not path.is_file():
        raise ValueError("discussion/threads.json not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("threads"), list):
        raise ValueError("discussion/threads.json must contain a threads list")
    return path, data


def save(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def valid_lab(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,100}", value):
        raise ValueError(f"invalid lab id: {value}")
    return value


def thread_for(data: dict, thread_id: str) -> dict:
    thread = next((item for item in data["threads"] if item.get("id") == thread_id), None)
    if thread is None:
        raise ValueError(f"unknown thread: {thread_id}")
    return thread


def public(thread: dict) -> dict:
    last = thread.get("messages", [])[-1] if thread.get("messages") else None
    return {"id": thread["id"], "status": thread["status"], "title": thread["title"],
            "awaiting": None if thread["status"] != "open" or not last else ("user" if last["author"] == "agent" else "agent"),
            "updated": thread["updated"]}


def open_thread(args: argparse.Namespace) -> dict:
    if args.author not in AUTHORS or args.priority not in PRIORITIES or args.category not in CATEGORIES:
        raise ValueError("invalid author, priority, or category")
    title, message = args.title.strip(), args.message.strip()
    if not title or len(title) > 160 or not message or len(message) > 12000:
        raise ValueError("title and message are required within dashboard limits")
    path, data = load(args.project)
    duplicate = next((item for item in data["threads"] if item.get("status") == "open" and item.get("title", "").casefold() == title.casefold()), None)
    if duplicate:
        return {"duplicate": True, "thread": public(duplicate)}
    number = 1
    used = {item.get("id") for item in data["threads"]}
    while f"thread-{number:03d}" in used:
        number += 1
    now = stamp()
    thread = {"id": f"thread-{number:03d}", "title": title, "category": args.category,
              "priority": args.priority, "status": "open", "related_labs": [valid_lab(x) for x in args.lab],
              "created": now, "updated": now,
              "messages": [{"id": "msg-001", "author": args.author, "type": args.type, "created": now, "content": message}]}
    data["threads"].append(thread)
    save(path, data)
    return {"duplicate": False, "thread": public(thread)}


def reply(args: argparse.Namespace) -> dict:
    if args.author not in AUTHORS:
        raise ValueError("invalid author")
    message = args.message.strip()
    if not message or len(message) > 12000:
        raise ValueError("message is required within dashboard limits")
    path, data = load(args.project)
    thread = thread_for(data, args.thread_id)
    if thread.get("status") != "open":
        raise ValueError("cannot reply to a closed thread")
    now = stamp()
    thread["messages"].append({"id": f"msg-{len(thread['messages']) + 1:03d}", "author": args.author,
                               "type": args.type, "created": now, "content": message})
    thread["updated"] = now
    save(path, data)
    return {"thread": public(thread)}


def listing(args: argparse.Namespace) -> dict:
    _, data = load(args.project)
    threads = [public(thread) for thread in data["threads"] if not args.open_only or thread.get("status") == "open"]
    return {"threads": sorted(threads, key=lambda item: item["updated"], reverse=True)}


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    opening = commands.add_parser("open")
    opening.add_argument("project")
    opening.add_argument("--author", choices=sorted(AUTHORS), required=True)
    opening.add_argument("--title", required=True)
    opening.add_argument("--message", required=True)
    opening.add_argument("--category", choices=sorted(CATEGORIES), default="scientific")
    opening.add_argument("--priority", choices=sorted(PRIORITIES), default="normal")
    opening.add_argument("--lab", action="append", default=[])
    opening.add_argument("--type", default="question")
    replying = commands.add_parser("reply")
    replying.add_argument("project")
    replying.add_argument("thread_id")
    replying.add_argument("--author", choices=sorted(AUTHORS), required=True)
    replying.add_argument("--message", required=True)
    replying.add_argument("--type", default="response")
    listing_parser = commands.add_parser("list")
    listing_parser.add_argument("project")
    listing_parser.add_argument("--open-only", action="store_true")
    args = parser.parse_args()
    result = open_thread(args) if args.command == "open" else reply(args) if args.command == "reply" else listing(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
