"""Exact tree-subtraction correction to the connected-path witness bound.

No noise records are sampled.  For two signed paths, the positive bivariate
polynomial in x,y counts the number of locally saturated currents on each
path.  Its edge factors are

    product_e sum_{j compatible} pi(j) x^[j opposes delta_1]
                                      y^[j opposes delta_2].

Only coefficients whose two exact likelihood ratios are at least one enter
the path-event intersection probability.
"""
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
from math import lcm
from pathlib import Path
import hashlib
import json
import sys
import time

import numpy as np

LAB = Path(__file__).resolve().parents[1]
ROOT = LAB.parents[1]
sys.path.insert(0, str(LAB / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from check_connected_current_defects import enumerate_paths
from current_oracle import square_graph


CELLS = ((Fraction(1, 20), Fraction(1, 2)),
         (Fraction(1, 20), Fraction(3, 4)),
         (Fraction(2, 25), Fraction(1, 2)),
         (Fraction(2, 25), Fraction(3, 4)))
CAP = 10_000
RUNTIME_CAP = 120.0


def weights(p, q):
    raw = (1-p, p*q, p*(1-q))
    denominator = lcm(*(x.denominator for x in raw))
    return denominator, tuple(int(x*denominator) for x in raw)


def event_key(delta):
    return tuple((int(e), int(delta[e])) for e in np.flatnonzero(delta))


def signed_events(g):
    _, paths, _ = enumerate_paths(g, retain=True)
    events = []
    for orientation in (1, -1):
        group = []
        for path in paths:
            delta = path * orientation
            key = event_key(delta)
            group.append({"delta": delta, "key": key,
                          "forward": sum(s == 1 for _, s in key),
                          "backward": sum(s == -1 for _, s in key),
                          "orientation": orientation})
        events.extend(sorted(group, key=lambda x: x["key"]))
    for i, event in enumerate(events):
        event["id"] = i
    return events


def frozen_geometric_forest(events):
    """Two orientation forests, frozen before any probability is evaluated.

    A path attaches to the earlier same-orientation path with the most
    same-directed shared edges, then most total shared edges, then the
    lexicographically smallest path.  If no edge is shared it starts a new
    component.  This is geometry-only and is never retuned by cell.
    """
    forest = []
    roots = []
    for orientation in (1, -1):
        group = [event for event in events if event["orientation"] == orientation]
        earlier = []
        for event in group:
            support = {e: s for e, s in event["key"]}
            ranked = []
            for parent in earlier:
                other = {e: s for e, s in parent["key"]}
                shared = set(support) & set(other)
                same = sum(support[e] == other[e] for e in shared)
                if shared:
                    ranked.append((-same, -len(shared), parent["key"], parent))
            if not ranked:
                roots.append(event["id"])
            else:
                parent = min(ranked)[-1]
                forest.append((parent["id"], event["id"]))
            earlier.append(event)
    assert len(forest) == len(events)-len(roots)
    return forest, roots


def factor_signature(first, second):
    support = sorted(set(np.flatnonzero(first["delta"])) |
                     set(np.flatnonzero(second["delta"])))
    return Counter((int(first["delta"][e]), int(second["delta"][e])) for e in support)


def local_terms(d1, d2):
    terms = []
    for j, symbol in ((0, 0), (1, 1), (-1, 2)):
        if (d1 and abs(j+d1) > 1) or (d2 and abs(j+d2) > 1):
            continue
        k1 = int((d1 == 1 and j == -1) or (d1 == -1 and j == 1))
        k2 = int((d2 == 1 and j == -1) or (d2 == -1 and j == 1))
        terms.append((k1, k2, symbol))
    return terms


def wins(event, k, A, B, C):
    F, R = event["forward"], event["backward"]
    # (B/A)^F (C/A)^R (A^2/(BC))^k >= 1, exactly.
    return B**F * C**R * A**(2*k) >= A**(F+R) * B**k * C**k


def polynomial_mass(first, second, p, q):
    denominator, (A, B, C) = weights(p, q)
    signature = factor_signature(first, second)
    table = {(0, 0): 1}
    edge_count = 0
    for (d1, d2), multiplicity in sorted(signature.items()):
        terms = local_terms(d1, d2)
        assert terms, "locally incompatible shared edge"
        for _ in range(multiplicity):
            edge_count += 1
            nxt = defaultdict(int)
            for (u, v), coefficient in table.items():
                for du, dv, symbol in terms:
                    nxt[u+du, v+dv] += coefficient * (A, B, C)[symbol]
            table = nxt
    numerator = sum(coefficient for (u, v), coefficient in table.items()
                    if wins(first, u, A, B, C) and wins(second, v, A, B, C))
    return Fraction(numerator, denominator**edge_count), table, signature


def single_mass(event, p, q):
    denominator, (A, B, C) = weights(p, q)
    table = {0: 1}
    for _, d in event["key"]:
        nxt = defaultdict(int)
        for k, coefficient in table.items():
            for dk, _, symbol in local_terms(d, 0):
                nxt[k+dk] += coefficient * (A, B, C)[symbol]
        table = nxt
    numerator = sum(coefficient for k, coefficient in table.items()
                    if wins(event, k, A, B, C))
    return Fraction(numerator, denominator**len(event["key"]))


def exact_l3_gate():
    g = square_graph(3)
    events = signed_events(g)
    states = np.array(list(product((0, 1, -1), repeat=len(g.edges))), dtype=np.int8)
    cells = CELLS + ((Fraction(1, 3), Fraction(1, 2)),)
    checked = 0
    max_error = 0.0
    saw_opposite_shared = False
    saw_tie = False
    for p, q in cells:
        denominator, (A, B, C) = weights(p, q)
        counts = ((states == 0).sum(axis=1), (states == 1).sum(axis=1),
                  (states == -1).sum(axis=1))
        masses = np.array([A**int(a)*B**int(b)*C**int(c)
                           for a, b, c in zip(*counts)], dtype=object)
        holds = np.zeros((len(states), len(events)), dtype=bool)
        for e, event in enumerate(events):
            shifted = states + event["delta"]
            supported = np.all(np.abs(shifted) <= 1, axis=1)
            shifted_counts = ((shifted == 0).sum(axis=1), (shifted == 1).sum(axis=1),
                              (shifted == -1).sum(axis=1))
            shifted_masses = np.array([A**int(a)*B**int(b)*C**int(c)
                                       for a, b, c in zip(*shifted_counts)], dtype=object)
            holds[:, e] = supported & (shifted_masses >= masses)
            if p == Fraction(1, 3) and q == Fraction(1, 2):
                saw_tie |= bool(np.any(holds[:, e] & (shifted_masses == masses)))
        for i in range(len(events)):
            for j in range(i+1, len(events)):
                signature = factor_signature(events[i], events[j])
                saw_opposite_shared |= any(a == -b and a for a, b in signature)
                predicted, _, _ = polynomial_mass(events[i], events[j], p, q)
                exact = Fraction(sum(int(x) for x in masses[holds[:, i] & holds[:, j]]),
                                 denominator**len(g.edges))
                assert predicted == exact, (p, q, i, j, predicted, exact)
                max_error = max(max_error, abs(float(predicted-exact)))
                checked += 1
    assert saw_opposite_shared and saw_tie
    return {"status": "passed", "states_per_cell": len(states), "events": len(events),
            "cells": len(cells), "pair_cell_checks": checked,
            "opposite_shared_direction_covered": saw_opposite_shared,
            "exact_likelihood_tie_covered": saw_tie,
            "max_absolute_error": max_error}


def main():
    started = time.monotonic()
    gate = exact_l3_gate()
    g = square_graph(5)
    events = signed_events(g)
    forest, roots = frozen_geometric_forest(events)
    assert len(forest) <= CAP

    single_sums = {cell: sum((single_mass(event, *cell) for event in events), Fraction(0))
                   for cell in CELLS}
    intersection_sums = {cell: Fraction(0) for cell in CELLS}
    pair_rows = []
    compatibility = Counter()
    for number, (i, j) in enumerate(forest, 1):
        if number > CAP or time.monotonic()-started > RUNTIME_CAP:
            raise RuntimeError("registered intersection/runtime cap")
        first, second = events[i], events[j]
        signature = factor_signature(first, second)
        same = sum(n for (a, b), n in signature.items() if a == b and a)
        opposite = sum(n for (a, b), n in signature.items() if a == -b and a)
        compatibility["pairs"] += 1
        compatibility["pairs_with_same_direction_shared_edge"] += same > 0
        compatibility["pairs_with_opposite_direction_shared_edge"] += opposite > 0
        values = []
        coefficient_counts = []
        for cell in CELLS:
            value, table, observed_signature = polynomial_mass(first, second, *cell)
            assert observed_signature == signature
            intersection_sums[cell] += value
            values.append({"p": float(cell[0]), "q": float(cell[1]),
                           "exact": f"{value.numerator}/{value.denominator}",
                           "value": float(value)})
            coefficient_counts.append(len(table))
        pair_rows.append({"parent": i, "child": j, "same_direction_shared_edges": same,
                          "opposite_direction_shared_edges": opposite,
                          "factor_signature": {f"{a},{b}": n for (a, b), n in sorted(signature.items())},
                          "positive_coefficient_counts": coefficient_counts,
                          "intersections": values})

    previous = json.loads((LAB / "results/connected-current-defects-2026-09-19.json").read_text())
    activity = {(Fraction(str(r["p"])), Fraction(str(r["q"]))): r
                for r in previous["frozen_activity_comparisons"]}
    results = []
    promoted = False
    for cell in CELLS:
        path_sum = single_sums[cell]
        subtraction = intersection_sums[cell]
        tree_bound = path_sum-subtraction
        assert 0 <= tree_bound <= path_sum
        old = activity[cell]
        strongest = min(Fraction(str(old["combined_upper"])), tree_bound, Fraction(1, 2))
        improves_path = tree_bound < path_sum
        improves_strongest = float(strongest) < old["combined_upper"]-1e-15
        promoted |= improves_strongest
        results.append({"p": float(cell[0]), "q": float(cell[1]),
                        "path_sum": float(path_sum), "tree_subtraction": float(subtraction),
                        "tree_bound": float(tree_bound),
                        "relative_path_bound_improvement": float(subtraction/path_sum),
                        "previous_strongest_upper": old["combined_upper"],
                        "new_strongest_upper": float(strongest),
                        "improves_path_bound": improves_path,
                        "improves_strongest_certified_upper": improves_strongest})

    status = "passed_promoted" if promoted else "passed_not_promoted"
    files = [Path(__file__), LAB/"scripts/check_connected_current_defects.py",
             LAB/"results/connected-current-defects-2026-09-19.json",
             LAB/"manifests/connected-defect-overlap-2026-09-19.json"]
    out = {
        "status": status,
        "scope": "Deterministic L5 tree-subtraction correction; no physical-record sampling, fitting, threshold estimate, or decoder tuning.",
        "theorem": "For any finite event family and any forest T on its indices, P(union_i E_i) <= sum_i P(E_i) - sum_(i,j in T) P(E_i intersection E_j). Pointwise, the active vertices induce a forest with at most k-1 active edges, so k-e >= 1 whenever the union occurs.",
        "positive_bivariate_polynomial": "For paths r,s, G_rs(x,y)=product_e sum_{j compatible} pi(j)x^[j opposes delta_r]y^[j opposes delta_s]. Summing its nonnegative coefficients over the two exact likelihood-winning index sets gives P(E_r intersection E_s).",
        "forest_rule": "Separate + and - orientation groups. In lexicographic path order, attach each path to the earlier path maximizing same-directed shared edges, then total shared edges, then lexicographic priority; start a new component only if there is no shared edge. Frozen before cell probabilities.",
        "exact_l3_gate": gate,
        "L5": {"events": len(events), "forest_edges": len(forest), "roots": roots,
               "intersection_evaluations": len(forest), "cap": CAP,
               "compatibility": dict(compatibility), "cells": results,
               "pairs": pair_rows},
        "acceptance": {"improves_at_least_one_primary_strongest_bound": promoted,
                       "all_primary_cells_reported": len(results) == len(CELLS),
                       "runtime_below_120_seconds": time.monotonic()-started <= RUNTIME_CAP},
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in files},
        "elapsed_seconds": time.monotonic()-started,
    }
    assert out["acceptance"]["runtime_below_120_seconds"]
    (LAB/"results/connected-defect-overlap-2026-09-19.json").write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps({"status": status, "exact_l3_gate": gate, "L5": {k: out["L5"][k]
          for k in ("events", "forest_edges", "intersection_evaluations", "compatibility", "cells")},
          "elapsed_seconds": out["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
