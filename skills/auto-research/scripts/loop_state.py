#!/usr/bin/env python3
"""Small durable state store for the project-level auto-research loop."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def state_path(project):
    return Path(project).resolve() / ".auto-research" / "state.json"


def default_state():
    return {
        "status": "paused",
        "updated": None,
        "quiet_supervisor_ticks": 0,
        "pending_human_thread_id": None,
        "active_deliverable_contract": None,
        "last_acceptance_item": None,
        "next_acceptance_item": None,
        "last_action": None,
    }


def read(project):
    path = state_path(project)
    if path.is_file():
        state = json.loads(path.read_text())
        for key, value in default_state().items():
            state.setdefault(key, value)
        return path, state
    return path, default_state()


def contract_path(project, value):
    root = Path(project).resolve()
    file_part = value.split("#", 1)[0]
    target = (root / file_part).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError("deliverable contract must be inside the project") from error
    if not target.is_file():
        raise ValueError(f"deliverable contract not found: {file_part}")
    return value


def write(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status"):
        commands.add_parser(name).add_argument("project")
    transition = commands.add_parser("set-status")
    transition.add_argument("project"); transition.add_argument("status", choices=["active", "paused", "complete"])
    pending = commands.add_parser("set-pending-human")
    pending.add_argument("project"); pending.add_argument("thread_id", nargs="?", default=None)
    contract = commands.add_parser("set-contract")
    contract.add_argument("project"); contract.add_argument("contract")
    contract.add_argument("--next-item", required=True)
    commands.add_parser("clear-contract").add_argument("project")
    action = commands.add_parser("record-action")
    action.add_argument("project"); action.add_argument("action"); action.add_argument("--quiet", action="store_true")
    action.add_argument("--acceptance-item"); action.add_argument("--next-item")
    frontier = commands.add_parser("update-frontier-job")
    frontier.add_argument("project"); frontier.add_argument("job_id")
    frontier.add_argument("--status", required=True)
    frontier.add_argument("--next-operation", required=True)
    frontier.add_argument("--lab-result")
    frontier.add_argument("--lab-next-operation")
    args = parser.parse_args()
    path, state = read(args.project)
    if args.command == "init":
        pass
    elif args.command == "set-status": state["status"] = args.status
    elif args.command == "set-pending-human": state["pending_human_thread_id"] = args.thread_id
    elif args.command == "set-contract":
        next_contract = contract_path(args.project, args.contract)
        previous_contract = state.get("active_deliverable_contract")
        if previous_contract != next_contract:
            state["previous_active_deliverable_contract"] = previous_contract
        state["active_deliverable_contract"] = next_contract
        state["last_acceptance_item"] = None
        state["next_acceptance_item"] = args.next_item
    elif args.command == "clear-contract":
        state["active_deliverable_contract"] = None
        state["last_acceptance_item"] = None
        state["next_acceptance_item"] = None
    elif args.command == "record-action":
        state["last_action"] = args.action
        if args.acceptance_item is not None:
            state["last_acceptance_item"] = args.acceptance_item
        if args.next_item is not None:
            state["next_acceptance_item"] = args.next_item
        state["quiet_supervisor_ticks"] = state.get("quiet_supervisor_ticks", 0) + 1 if args.quiet else 0
    elif args.command == "update-frontier-job":
        matches = [
            (frontier, job)
            for frontier in state.get("other_research_frontiers", [])
            for job in frontier.get("registered_jobs", [])
            if job.get("id") == args.job_id
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one frontier job for {args.job_id}, found {len(matches)}")
        owning_frontier, job = matches[0]
        job["status"] = args.status
        job["next_operation"] = args.next_operation
        if args.lab_result is not None:
            owning_frontier["last_result"] = args.lab_result
        if args.lab_next_operation is not None:
            owning_frontier["next_operation"] = args.lab_next_operation
    if args.command != "status":
        state["updated"] = now(); write(path, state)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
