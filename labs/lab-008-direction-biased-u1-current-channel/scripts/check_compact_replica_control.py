"""Fail-closed checks for the conditional compact-Gaussian calibration.

These diagnostics do not fit a continuum model.  They test the two shortcuts
that would be needed to turn the conditional annulus formula into a physical
prediction: bare-curvature stiffness matching and continuation from integer
replicas without a microscopic prescription.
"""
from pathlib import Path
import hashlib
import json
import math

import numpy as np

from current_oracle import LAB, ROOT


def gaussian_risk(A, terms=200):
    n = np.arange(terms, dtype=float)
    return float(0.5 - 2 / np.pi * np.sum(
        (-1.0) ** n / (2 * n + 1) * np.exp(-A * (n + 0.5) ** 2)
    ))


def cumulants(p, q):
    x = np.array([0.0, 1.0, -1.0])
    w = np.array([1 - p, p * q, p * (1 - q)])
    mu = float(w @ x)
    centered = x - mu
    variance = float(w @ centered ** 2)
    k3 = float(w @ centered ** 3)
    k4 = float(w @ centered ** 4 - 3 * variance ** 2)
    return mu, variance, k3, k4


def continuation_witness(R, c=0.1):
    """Term invisible at every admissible integer R>=2, finite at R=1."""
    if abs(R - 1) < 1e-12:
        return c * math.pi
    return c * math.sin(math.pi * (R - 1)) / (R - 1)


def main():
    prior = json.loads((LAB / 'results/replica-boundary-theory-2026-09-18.json').read_text())
    exact = {(r['p'], r['q']): r['LER'] for r in prior['square_sector_checks']}
    rows = []
    for p, q in sorted(exact):
        mu, v0, k3, k4 = cumulants(p, q)
        A_bare = 2 * math.pi ** 2 * v0
        candidate = gaussian_risk(A_bare)
        rows.append({
            'L': 3, 'p': p, 'q': q, 'mu': mu, 'bare_variance_v0': v0,
            'standardized_kappa3': None if v0 == 0 else k3 / v0 ** 1.5,
            'standardized_kappa4': None if v0 == 0 else k4 / v0 ** 2,
            'bare_kappa_gaussian_annulus_LER_rho1': candidate,
            'exact_open_square_LER': exact[(p, q)],
            'absolute_mismatch': abs(candidate - exact[(p, q)]),
            'interpretation': 'Geometry differs, so this is only a rejection test for naive kappa=v0 calibration; it is not a continuum fit.'
        })

    integer_witness = {str(R): continuation_witness(float(R)) for R in range(2, 9)}
    assert max(abs(x) for x in integer_witness.values()) < 1e-15
    limit_at_one = continuation_witness(1.0)
    assert abs(limit_at_one - 0.1 * math.pi) < 1e-15

    source = Path(__file__)
    out = {
        'status': 'passed_rejection',
        'decision': 'Reject the present Gaussian annulus as a quantitatively controlled calibration of the physical square. Retain it only as a conditional continuum benchmark.',
        'bare_stiffness_diagnostic': rows,
        'endpoint_obstruction': {
            'p_to_0': 'K(phi)->1 exactly, so the angle measure is flat rather than localized near the spin-wave saddle.',
            'p_to_1_q1': 'K(phi)=exp(i phi), whose modulus is flat; this solvable endpoint also supplies no spin-wave localization.',
            'consequence': 'No currently used endpoint supplies a small-angle parameter. The local curvature v0 is not a matched renormalized helicity modulus.'
        },
        'vortex_obstruction': {
            'integer_replica_charge_lattice': 'A_(R-1) roots are exact for integer R.',
            'missing_control': 'The physical ternary kernel supplies no demonstrated small core fugacity. For R>=3 it can give complex, species-dependent core weights, while R=2 is the wrong annealed record law.',
            'consequence': 'The formal root marginality kappa=1/pi cannot be converted into a physical p_c without a fugacity calculation and RG matching.'
        },
        'continuation_nonuniqueness_witness': {
            'family': 'C_c(R)=C_0(R)+c*sin(pi*(R-1))/(R-1), with the removable R=1 value c*pi.',
            'c': 0.1,
            'values_at_admissible_integers_R2_to_R8': integer_witness,
            'added_limit_at_R1': limit_at_one,
            'consequence': 'Integer-replica values alone do not determine the physical R->1 limit. A microscopic continuation inherited from the positive finite-lattice observable is required.'
        },
        'next_analytic_alternative': 'Use a direct positive-current defect/polymer expansion with a certified omitted-weight remainder for the low-to-intermediate-p square curve. Treat a critical continuum theory separately, only after deriving a physical stiffness and species-resolved fugacities from the R->1 observable.',
        'claims_prohibited': [
            'No physical p_c or critical LER from kappa=1/pi.',
            'No identification of kappa with v0.',
            'No inference that a physical Gaussian or BKT fixed point is absent; only the present calibration is uncontrolled.'
        ],
        'source_sha256': {
            str(source.relative_to(ROOT)): hashlib.sha256(source.read_bytes()).hexdigest(),
            'labs/lab-008-direction-biased-u1-current-channel/results/replica-boundary-theory-2026-09-18.json': hashlib.sha256((LAB / 'results/replica-boundary-theory-2026-09-18.json').read_bytes()).hexdigest()
        }
    }
    target = LAB / 'results/compact-replica-control-2026-09-18.json'
    target.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({
        'status': out['status'],
        'max_bare_calibration_mismatch': max(r['absolute_mismatch'] for r in rows),
        'min_bare_calibration_mismatch': min(r['absolute_mismatch'] for r in rows),
        'added_R1_continuation_shift': limit_at_one
    }, indent=2))


if __name__ == '__main__':
    main()
