"""First-record-aware public E2 adapter for one pinned ideal D4 path.

The lookup is deliberately not the general five-round D4 history generator.
Only J6O public-law rows are consumed; the private operator diagnostics are
never returned to a decoder.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j6p-first-record-aware-e2-adapter-2026-09-25.json"
LAW = LAB / "results/j6o-full-binary-sequential-public-record-2026-09-25.json"


def digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_record(record: Mapping[str, Any]) -> dict[str, list[int]]:
    if not isinstance(record, Mapping) or set(record) != {"flux", "charge", "vacuum"}:
        raise ValueError("first public record must contain exactly flux/charge/vacuum")
    rows = {}
    for name in ("flux", "charge", "vacuum"):
        values = record[name]
        if not isinstance(values, (list, tuple)) or len(values) != 24:
            raise ValueError("public record arrays must each have 24 sites")
        if any(type(bit) is not int or bit not in (0, 1) for bit in values):
            raise ValueError("public record arrays must be strict binary integers")
        rows[name] = list(values)
    if rows["vacuum"] != [1 - bit for bit in rows["charge"]]:
        raise ValueError("public vacuum/charge membership convention changed")
    if any(f and c for f, c in zip(rows["flux"], rows["charge"])):
        raise ValueError("unmeasured flux sites cannot report charge")
    return rows


def first_prefix_digest(trial_id: str, decision_round: int,
                        first_public: Mapping[str, Any]) -> str:
    if not isinstance(trial_id, str) or not trial_id or decision_round != 0:
        raise ValueError("fixed-path first record requires trial ID and round zero")
    return digest({"trial_id": trial_id, "decision_round": decision_round,
                   "first_public": _canonical_record(first_public)})


def bound_action_digest(trial_id: str, decision_round: int,
                        prefix_digest: str, correction_edges: tuple[int, ...]) -> str:
    if not isinstance(prefix_digest, str) or len(prefix_digest) != 64:
        raise ValueError("first prefix digest must be SHA-256 shaped")
    if correction_edges not in ((), (0,), (0, 4)):
        raise ValueError("unsupported correction action for fixed-path law")
    return digest({"trial_id": trial_id, "decision_round": decision_round,
                   "first_prefix_digest": prefix_digest,
                   "correction_edges": list(correction_edges)})


def provide_fixed_path_e2(
    *, trial_id: str, decision_round: int,
    first_public: Mapping[str, Any], first_digest: str,
    correction_edges: tuple[int, ...], action_digest: str,
    second_exogenous_bit: int,
) -> dict[str, Any]:
    """Return only bound public fields; reject every input outside J6O support."""
    if type(second_exogenous_bit) is not int or second_exogenous_bit not in (0, 1):
        raise ValueError("second exogenous bit must be 0 or 1")
    first = _canonical_record(first_public)
    if first_prefix_digest(trial_id, decision_round, first) != first_digest:
        raise ValueError("first record is not bound to its causal prefix digest")
    if bound_action_digest(trial_id, decision_round, first_digest,
                           correction_edges) != action_digest:
        raise ValueError("correction action is not bound to this first record")
    contract = json.loads(CONTRACT.read_text())
    if hashlib.sha256(LAW.read_bytes()).hexdigest() != \
            contract["pinned_inputs"]["j6o_result_sha256"]:
        raise ValueError("pinned physical public-law result drifted")
    law = json.loads(LAW.read_text())
    if law["status"] != "passed_exact_one_geometry_full_binary_joint_record_only":
        raise ValueError("fixed-path public law is not accepted")
    action = {(): "defer", (0,): "partial", (0, 4): "matched"}[correction_edges]
    rows = [row for row in law["public_law_rows"]
            if row["action"] == action and row["first_public"] == first
            and row["public_action_red_edge_ids"] == list(correction_edges)]
    if action == "defer":
        if len(rows) != 1 or rows[0]["second_public"] is not None:
            raise ValueError("defer public-law support drifted")
        second = None
    else:
        positive = [row for row in rows
                    if row["second_public"] is not None
                    and row["second_conditional_probability"] > 0]
        if len(positive) != 2 or any(row["second_conditional_probability"] != 0.5
                                     for row in positive):
            raise ValueError("conditional public-law support drifted")
        positive.sort(key=lambda row: tuple(row["second_public"]["charge"]))
        second = _canonical_record(positive[second_exogenous_bit]["second_public"])
    public = {
        "trial_id": trial_id,
        "decision_round": decision_round,
        "first_prefix_digest": first_digest,
        "public_action_red_edge_ids": list(correction_edges),
        "action_digest": action_digest,
        "second_public": second,
    }
    return {**public, "completion_digest": digest(public)}
