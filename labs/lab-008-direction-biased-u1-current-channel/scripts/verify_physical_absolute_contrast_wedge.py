#!/usr/bin/env python3
"""Closed-form square H12 wedge checks; no current enumeration or sampling."""
from __future__ import annotations

import json
from math import cosh, isclose, sqrt, tanh


def row(h: float) -> dict:
    q = (1 + tanh(h)) / 2
    t = sqrt(q * (1 - q))
    sech = 1 / cosh(h)
    pcrit = (1 - sqrt(1 - 4 / (9 * (1 + sech)))) / 2
    pcvx = 1 / (1 + t)
    pcheck = pcrit / 2
    gamma = sqrt(pcheck * (1 - pcheck) * (1 + 2 * t))
    peff = pcheck / (pcheck + (1 - pcheck) * cosh(h))
    return {
        "h": h, "q": q, "t": t, "sech_h": sech,
        "t_identity_error": abs(2 * t - sech),
        "low_p_strict_root": pcrit,
        "convexity_ceiling": pcvx,
        "root_equality_error": abs(9 * pcrit * (1 - pcrit) * (1 + sech) - 1),
        "check_p": pcheck, "check_p_eff": peff,
        "rho_charge_at_check_p": 3 * gamma,
        "convexity_gate": pcheck <= pcvx,
    }


if __name__ == "__main__":
    rows = [row(h) for h in (0.0, 0.5, 1.5)]
    directed_root = (3 - sqrt(5)) / 6
    fair_root = (3 - sqrt(7)) / 6
    high_p_start = (3 + 2 * sqrt(2)) / 6
    rho_binary_at_98 = 6 * sqrt(0.98 * 0.02)
    assert all(r["t_identity_error"] < 1e-14 and r["root_equality_error"] < 1e-14 for r in rows)
    assert all(r["convexity_gate"] and r["rho_charge_at_check_p"] < 1 for r in rows)
    assert isclose(rows[0]["low_p_strict_root"], fair_root, abs_tol=1e-14)
    assert all(fair_root <= r["low_p_strict_root"] < directed_root for r in rows)
    assert high_p_start > 0.5 and rho_binary_at_98 < 1
    print(json.dumps({
        "id": "lab008-physical-absolute-contrast-certified-wedge-2026-09-22",
        "status": "verified_closed_form",
        "new_system_sizes": 0, "new_physical_samples": 0,
        "rows": rows,
        "fair_low_p_root": fair_root,
        "directed_low_p_limit_root": directed_root,
        "parity_high_p_start": high_p_start,
        "rho_binary_at_p_98": rho_binary_at_98,
    }, indent=2, sort_keys=True))
