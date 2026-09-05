"""Source-bounded phenomenological repeated D4 projector instrument.

This module deliberately separates three objects that the primary sources do
not identify with one another:

* a hidden mutually-exclusive projector outcome and state update (E1A);
* a later classical false-negative/false-positive report channel (E1B); and
* Jing et al.'s localized quasi-stabilizer time-like-herald example (E1C).

It is not an ancilla extraction circuit and generates no performance data.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isclose
from typing import Any, Iterable, Mapping

from d4_spatial_policy import (
    D4FluxActionV1,
    D4PostFluxObservationV1,
    D4SpatialCommitRequestV1,
    canonical_digest,
    paper_periodic_honeycomb,
)


SCHEMA_VERSION = 1
VACUUM = "vacuum"
FLUX = "m_flux"
CHARGE = "e_charge"
REGISTERED_LABELS = (VACUUM, FLUX, CHARGE)
NONVACUUM_LABELS = (FLUX, CHARGE)
ZERO_DIGEST = "0" * 64


def _sorted_unique(values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(sorted(str(value) for value in values))
    if result != tuple(sorted(set(result))):
        raise ValueError("reported labels must be unique")
    if any(value not in NONVACUUM_LABELS for value in result):
        raise ValueError("reported labels must be registered non-vacuum species")
    return result


def _validate_true_labels(labels: Mapping[int, str]) -> tuple[tuple[int, str], ...]:
    result = tuple(sorted((int(site), str(label)) for site, label in labels.items()))
    if tuple(site for site, _ in result) != tuple(sorted(set(site for site, _ in result))):
        raise ValueError("projector sites must be unique")
    if any(site < 0 or label not in REGISTERED_LABELS for site, label in result):
        raise ValueError("invalid site or true projector label")
    return result


@dataclass(frozen=True)
class HiddenProjectorStateV1:
    """Private true outcome and state-update binding for one round."""

    schema_version: int
    trial_id: str
    round: int
    true_labels: tuple[tuple[int, str], ...]
    previous_state_digest: str
    bound_action_digest: str | None
    state_update_digest: str

    def private_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trial_id": self.trial_id,
            "round": self.round,
            "true_labels": [
                {"site": site, "label": label} for site, label in self.true_labels
            ],
            "previous_state_digest": self.previous_state_digest,
            "bound_action_digest": self.bound_action_digest,
            "state_update_digest": self.state_update_digest,
        }


def project_hidden_state(
    *,
    trial_id: str,
    round: int,
    true_labels: Mapping[int, str],
    previous: HiddenProjectorStateV1 | None = None,
    bound_action_digest: str | None = None,
) -> HiddenProjectorStateV1:
    """Apply one abstract Lüders-projector update to the private trajectory.

    The true label is exactly one member of the registered projector partition
    at each supplied site.  Hardware/ancilla dynamics are intentionally absent.
    """

    if not trial_id or round < 0:
        raise ValueError("trial_id must be nonempty and round nonnegative")
    labels = _validate_true_labels(true_labels)
    if previous is not None:
        if previous.trial_id != trial_id or round != previous.round + 1:
            raise ValueError("projector histories must advance by one round")
        previous_digest = previous.state_update_digest
    else:
        previous_digest = ZERO_DIGEST
    if bound_action_digest is not None and len(bound_action_digest) != 64:
        raise ValueError("bound action digest must be SHA-256 shaped")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "trial_id": trial_id,
        "round": round,
        "true_labels": [{"site": site, "label": label} for site, label in labels],
        "previous_state_digest": previous_digest,
        "bound_action_digest": bound_action_digest,
    }
    return HiddenProjectorStateV1(
        schema_version=SCHEMA_VERSION,
        trial_id=trial_id,
        round=round,
        true_labels=labels,
        previous_state_digest=previous_digest,
        bound_action_digest=bound_action_digest,
        state_update_digest=canonical_digest(payload),
    )


def project_post_action_charge_state(
    *,
    trial_id: str,
    round: int,
    charge_labels: Mapping[int, str],
    bound_action_digest: str | None,
    previous: HiddenProjectorStateV1 | None = None,
) -> HiddenProjectorStateV1:
    """Project the charge-only record that exists after a bound flux action."""

    if bound_action_digest is None:
        raise ValueError("post-action charge projection requires bound flux action")
    if any(label not in (VACUUM, CHARGE) for label in charge_labels.values()):
        raise ValueError("post-action charge projector accepts only charge/vacuum labels")
    return project_hidden_state(
        trial_id=trial_id,
        round=round,
        true_labels=charge_labels,
        previous=previous,
        bound_action_digest=bound_action_digest,
    )


@dataclass(frozen=True)
class PublicReportedRecordV1:
    """Truth-free public reports produced after a private projector update."""

    schema_version: int
    trial_id: str
    round: int
    reported_labels: tuple[tuple[int, tuple[str, ...]], ...]
    bound_action_digest: str | None
    report_digest: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trial_id": self.trial_id,
            "round": self.round,
            "reported_labels": [
                {"site": site, "labels": list(labels)}
                for site, labels in self.reported_labels
            ],
            "bound_action_digest": self.bound_action_digest,
            "report_digest": self.report_digest,
        }


def report_from_hidden(
    hidden: HiddenProjectorStateV1,
    reported_labels: Mapping[int, Iterable[str]],
) -> PublicReportedRecordV1:
    """Attach a declared classical report without changing hidden state."""

    expected_sites = tuple(site for site, _ in hidden.true_labels)
    if tuple(sorted(int(site) for site in reported_labels)) != expected_sites:
        raise ValueError("reports must cover exactly the projected sites")
    reports = tuple(
        sorted(
            (int(site), _sorted_unique(values))
            for site, values in reported_labels.items()
        )
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "trial_id": hidden.trial_id,
        "round": hidden.round,
        "reported_labels": [
            {"site": site, "labels": list(labels)} for site, labels in reports
        ],
        "bound_action_digest": hidden.bound_action_digest,
    }
    return PublicReportedRecordV1(
        schema_version=SCHEMA_VERSION,
        trial_id=hidden.trial_id,
        round=hidden.round,
        reported_labels=reports,
        bound_action_digest=hidden.bound_action_digest,
        report_digest=canonical_digest(payload),
    )


def perfect_report(hidden: HiddenProjectorStateV1) -> PublicReportedRecordV1:
    return report_from_hidden(
        hidden,
        {
            site: (() if label == VACUUM else (label,))
            for site, label in hidden.true_labels
        },
    )


def report_distribution(
    true_label: str,
    *,
    false_negative: float,
    false_positive: Mapping[str, float],
) -> dict[tuple[str, ...], float]:
    """Enumerate the exact independent source-bounded classical report law."""

    if true_label not in REGISTERED_LABELS:
        raise ValueError("invalid true projector label")
    if not 0.0 <= false_negative <= 1.0:
        raise ValueError("false_negative must lie in [0,1]")
    if set(false_positive) != set(NONVACUUM_LABELS):
        raise ValueError("false_positive must cover each registered species")
    if any(not 0.0 <= float(value) <= 1.0 for value in false_positive.values()):
        raise ValueError("false-positive rates must lie in [0,1]")

    probabilities: dict[tuple[str, ...], float] = {}
    for bits in product((0, 1), repeat=len(NONVACUUM_LABELS)):
        report: list[str] = []
        probability = 1.0
        for species, bit in zip(NONVACUUM_LABELS, bits, strict=True):
            if species == true_label:
                keep_probability = 1.0 - false_negative
            else:
                keep_probability = float(false_positive[species])
            probability *= keep_probability if bit else 1.0 - keep_probability
            if bit:
                report.append(species)
        key = tuple(sorted(report))
        if probability > 0.0:
            probabilities[key] = probabilities.get(key, 0.0) + probability
    if not isclose(sum(probabilities.values()), 1.0, abs_tol=1e-12):
        raise AssertionError("report distribution failed normalization")
    return probabilities


class TranslationRequired(ValueError):
    """The typed noisy record cannot enter the current binary policy API."""


def restricted_record_to_commit_request(
    record: PublicReportedRecordV1,
    *,
    request_id: str,
    size: int,
    mode: str,
    causal_prefix_digest: str,
) -> D4SpatialCommitRequestV1:
    """Translate only singleton/empty reports into the existing E0 API."""

    if mode not in ("syndrome_only", "heralded"):
        raise ValueError("unsupported public decoder mode")
    flux_vertices: list[int] = []
    charge_measurements: list[dict[str, int]] = []
    for site, labels in record.reported_labels:
        if len(labels) > 1:
            raise TranslationRequired("multi-label report requires a new typed adapter")
        label = VACUUM if not labels else labels[0]
        if label == FLUX:
            flux_vertices.append(site)
        elif mode == "heralded":
            charge_measurements.append(
                {"vertex": site, "outcome": int(label == CHARGE)}
            )
    payload = {
        "schema_version": 1,
        "request_id": request_id,
        "model_id": "paper_periodic_coloured_honeycomb_d4",
        "size": size,
        "mode": mode,
        "decision_round": record.round,
        "committed_through_round": record.round,
        "flux_syndrome_vertices": flux_vertices,
        "initial_charge_measurements": charge_measurements,
        "causal_prefix_digest": causal_prefix_digest,
    }
    return D4SpatialCommitRequestV1.from_dict(payload)


def typed_record_to_commit_request(
    record: PublicReportedRecordV1,
    *,
    request_id: str,
    size: int,
    mode: str,
    scheduler_prefix_digest: str,
) -> D4SpatialCommitRequestV1:
    """Factor public membership bits into the two existing policy fields.

    ``syndrome_only`` deliberately projects away charge membership.  The
    ``heralded`` mode retains both membership bits, including when both are
    reported at one site.  The policy request remains bound to both the
    scheduler prefix and the exact E1 report without exposing private state.
    """

    if mode not in ("syndrome_only", "heralded"):
        raise ValueError("unsupported public decoder mode")
    if (
        len(scheduler_prefix_digest) != 64
        or any(character not in "0123456789abcdef" for character in scheduler_prefix_digest)
    ):
        raise ValueError("scheduler prefix must be a lowercase SHA-256 digest")
    flux_vertices = [
        site for site, labels in record.reported_labels if FLUX in labels
    ]
    charge_measurements = (
        []
        if mode == "syndrome_only"
        else [
            {"vertex": site, "outcome": int(CHARGE in labels)}
            for site, labels in record.reported_labels
        ]
    )
    translated_prefix_digest = canonical_digest(
        {
            "schema_version": SCHEMA_VERSION,
            "scheduler_prefix_digest": scheduler_prefix_digest,
            "e1_report_digest": record.report_digest,
            "mode": mode,
        }
    )
    payload = {
        "schema_version": 1,
        "request_id": request_id,
        "model_id": "paper_periodic_coloured_honeycomb_d4",
        "size": size,
        "mode": mode,
        "decision_round": record.round,
        "committed_through_round": record.round,
        "flux_syndrome_vertices": flux_vertices,
        "initial_charge_measurements": charge_measurements,
        "causal_prefix_digest": translated_prefix_digest,
    }
    return D4SpatialCommitRequestV1.from_dict(payload)


def typed_postflux_record_to_observation(
    record: PublicReportedRecordV1,
    *,
    request: D4SpatialCommitRequestV1,
    flux_action: D4FluxActionV1,
    active_vertices: Iterable[int],
    entanglement_pairs: Iterable[tuple[int, int]],
) -> D4PostFluxObservationV1:
    """Bind a public charge/vacuum report to one completed flux action.

    The caller supplies the physical post-action measurement layout.  This
    adapter checks only public identities and labels; it cannot construct a
    report from a hidden projector state or physical error.
    """

    request.validate()
    lattice = paper_periodic_honeycomb(request.size)
    flux_action.validate(edge_count=lattice.edge_count)
    if flux_action.request_id != request.request_id:
        raise ValueError("post-flux action belongs to another request")
    if record.bound_action_digest != flux_action.action_digest:
        raise ValueError("post-flux report is not bound to the exact flux action")
    if record.round < request.decision_round:
        raise ValueError("post-flux report predates the committed flux action")

    active = tuple(int(vertex) for vertex in active_vertices)
    pairs = tuple(tuple(int(vertex) for vertex in pair) for pair in entanglement_pairs)
    report_sites = tuple(site for site, _ in record.reported_labels)
    if report_sites != active:
        raise ValueError("post-flux report must cover exactly the active vertices")

    measurements: list[dict[str, int]] = []
    for site, labels in record.reported_labels:
        if labels not in ((), (CHARGE,)):
            raise ValueError("post-flux reports may contain only charge/vacuum labels")
        measurements.append({"vertex": site, "outcome": int(labels == (CHARGE,))})

    unsigned = {
        "request_id": request.request_id,
        "action_digest": flux_action.action_digest,
        "observation_round": record.round,
        "measurement_layout": {
            "active_vertices": list(active),
            "entanglement_pairs": [list(pair) for pair in pairs],
        },
        "charge_measurements": measurements,
    }
    return D4PostFluxObservationV1.from_dict(
        {**unsigned, "observation_digest": canonical_digest(unsigned)},
        vertex_count=lattice.vertex_count,
    )


@dataclass(frozen=True)
class QuasiStabilizerExampleV1:
    """Localized reproduction of Jing 2025 Supplemental Appendix D."""

    semantic: str
    localized_fixture_only: bool
    rounds: tuple[tuple[int, tuple[str, ...]], ...]


def jing_five_star_false_negative_example() -> QuasiStabilizerExampleV1:
    vacuum = VACUUM
    m = FLUX
    e = CHARGE
    return QuasiStabilizerExampleV1(
        semantic="quasi_stabilizer_time_like_herald",
        localized_fixture_only=True,
        rounds=(
            (0, (m, vacuum, e, vacuum, m)),
            (1, (m, vacuum, e, vacuum, m)),
            (2, (m, vacuum, e, e, vacuum)),
            (3, (m, vacuum, e, e, m)),
            (4, (m, vacuum, e, e, m)),
        ),
    )


def quasi_stabilizer_likelihoods(
    *, measurement_error: float, flux_pair_error: float, charge_pair_error: float
) -> dict[str, float | bool]:
    for value in (measurement_error, flux_pair_error, charge_pair_error):
        if not 0.0 <= value <= 1.0:
            raise ValueError("source probabilities must lie in [0,1]")
    single = float(measurement_error)
    three_flux = float(flux_pair_error**3)
    two_flux_charge = float(flux_pair_error**2 * charge_pair_error)
    return {
        "single_false_negative": single,
        "three_flux_pair_errors": three_flux,
        "two_flux_plus_charge_pair_errors": two_flux_charge,
        "single_is_strictly_most_likely": single > max(three_flux, two_flux_charge),
    }
