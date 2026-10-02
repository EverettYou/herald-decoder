"""Exact conservative posterior certificate for the frozen J8V collision pairs."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time


LAB = Path(__file__).resolve().parents[1]
CONTRACT = LAB / "manifests/j8w-same-flux-posterior-certificate-2026-09-28.json"
RESULT = LAB / "results/j8w-same-flux-posterior-certificate-2026-09-28.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    started = time.process_time()
    contract = json.loads(CONTRACT.read_text())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    previous = json.loads((LAB / contract["source_result"]).read_text())
    assert previous["status"] == "equal_prior_collision_second_law_matrix_verified"
    assert previous["physical_prior"] == {"p_X": "1/10", "p_Z": "0", "red_edges": 36}
    assert previous["selected_strata"] == ["1", "1/2", "1/4"]
    assert len(previous["rows"]) == 3
    single_error_prior = Fraction(9 ** 33, 10 ** 36)
    rows = []
    for source in previous["rows"]:
        stratum = source["base_first_likelihood_stratum"]
        pair = source["pair_rows"]
        assert len(pair) == 2
        assert all(len(item["error_edges_private"]) == 3 for item in pair)
        assert len({tuple(item["error_edges_private"]) for item in pair}) == 2
        q = Fraction(stratum)
        assert all(Fraction(item["first_public_mass"]) == q for item in pair)
        sector_prior = Fraction(source["sector_prior_mass"])
        pair_joint = 2 * single_error_prior * q
        omitted_prior = sector_prior - 2 * single_error_prior
        assert omitted_prior >= 0
        # All omitted first-record likelihoods are in [0,1].  The flux bits
        # exclude errors outside this sector, so this is an exhaustive bound.
        first_record_upper = pair_joint + omitted_prior
        pair_posterior_lower = pair_joint / first_record_upper
        omitted_posterior_upper = omitted_prior / first_record_upper
        assert pair_posterior_lower + omitted_posterior_upper == 1
        action_rows = []
        assert len(source["paired_action_differences"]) == 2
        for difference in source["paired_action_differences"]:
            tv = Fraction(difference["conditional_second_total_variation"])
            assert 0 <= tv <= 1
            # For the binary event E=a versus E!=a, the latter law is a
            # mixture of the other selected error and all omitted errors.
            # Reverse triangle inequality gives this distribution-free bound.
            numerator = single_error_prior * q * tv - omitted_prior
            complement_tv_lower = max(Fraction(), numerator / (single_error_prior * q + omitted_prior))
            action_rows.append({"public_action_red_edges": difference["public_action_red_edges"],
                                "selected_pair_second_total_variation": str(tv),
                                "selected_error_vs_full_complement_tv_lower": str(complement_tv_lower)})
        rows.append({"base_first_likelihood_stratum": stratum,
                     "first_flux_mask": source["first_flux_mask"],
                     "selected_error_edges_private": [item["error_edges_private"] for item in pair],
                     "sector_prior_mass": str(sector_prior),
                     "each_selected_error_prior_mass": str(single_error_prior),
                     "each_selected_error_first_likelihood": str(q),
                     "selected_pair_joint_first_mass": str(pair_joint),
                     "omitted_same_flux_prior_mass": str(omitted_prior),
                     "first_record_mass_upper": str(first_record_upper),
                     "selected_pair_posterior_lower": str(pair_posterior_lower),
                     "omitted_error_posterior_upper": str(omitted_posterior_upper),
                     "action_rows": action_rows})
    assert all(sha(LAB / path) == digest for path, digest in contract["pinned_inputs"].items())
    assert sha(Path(__file__)) == contract["runner_sha256_before_execution"]
    elapsed = time.process_time() - started
    assert elapsed <= contract["budget"]["max_cpu_seconds"]
    return {"schema_version": 1, "id": contract["id"],
            "status": "same_flux_posterior_bounds_verified",
            "contract_sha256": sha(CONTRACT), "runner_sha256": sha(Path(__file__)),
            "rows": rows, "cpu_seconds": round(elapsed, 6),
            "counters": {"new_born_terms": 0, "histories": 0, "schedule_arms": 0, "bootstraps": 0},
            "claim_boundary": "Distribution-free exact bounds for three selected same-flux, same-complete-first-record error pairs only. Unknown omitted first/second laws remain unevaluated; no full-IID information/risk, logical decoding, noisy JIT, size scaling or threshold claim."}


if __name__ == "__main__":
    assert not RESULT.exists(), "Refuse to overwrite existing result"
    result = run()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "cpu_seconds": result["cpu_seconds"]}))
