"""Runs the schema-level coverage simulation and writes results/*.csv.

This does NOT test any live text-to-image/video platform. It tests five
decision-engine *capability profiles* (four reduced-capability baselines
matching Table VI's qualitative claims, plus the full LATTICE-MG profile)
against the synthetic 960-adversarial / 480-benign schema corpus from
Section VII.B. See README.md "What the numbers mean" before citing any
number from this script's output as if it were a measured platform result.

Usage: python experiments/run_evaluation.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lattice_mg.baselines import (
    ALL_PROFILES,
    BENIGN_FALSE_POSITIVE_RATE,
    TOOL_SERVER_ALLOWLIST_PROB,
    CapabilityProfile,
)
from lattice_mg.corpus import CorpusCase, full_corpus
from lattice_mg.metrics import (
    TrialOutcome,
    attack_success_rate,
    benign_preservation_rate,
    coverage_by_family,
)

REPETITIONS = 5  # Section VII.C: minimum 5 repetitions per case for stochastic outcomes
SEED = 2026


def simulate_case(case: CorpusCase, profile: CapabilityProfile, rng: random.Random) -> bool:
    """Returns True if the defense catches (does not silently allow) this case."""
    if case.is_adversarial:
        if case.attack_family == "A8":
            p = profile.detect_probability("tool_binding") if profile.has_tool_operation_binding else 0.0
            if profile.has_tool_server_allowlist and not profile.has_tool_operation_binding:
                p = TOOL_SERVER_ALLOWLIST_PROB
            return rng.random() < p
        p = profile.detect_probability(case.required_channel)
        return rng.random() < p
    # Benign hard negative: "caught" here means wrongly blocked (false positive).
    return rng.random() < BENIGN_FALSE_POSITIVE_RATE[profile.name]


def run() -> dict[str, list[TrialOutcome]]:
    corpus = full_corpus(seed=SEED)
    results: dict[str, list[TrialOutcome]] = {}
    for profile in ALL_PROFILES:
        rng = random.Random(SEED + hash(profile.name) % 10_000)
        outcomes: list[TrialOutcome] = []
        for case in corpus:
            catches = sum(simulate_case(case, profile, rng) for _ in range(REPETITIONS))
            caught = catches > REPETITIONS / 2  # majority vote across repeated stochastic trials
            outcomes.append(
                TrialOutcome(
                    case_id=case.case_id,
                    is_adversarial=case.is_adversarial,
                    attack_family=case.attack_family,
                    category=case.category,
                    caught=caught,
                )
            )
        results[profile.name] = outcomes
    return results


def write_reports(results: dict[str, list[TrialOutcome]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "metrics_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["defense", "attack_success_rate", "benign_preservation_rate"])
        for name, outcomes in results.items():
            writer.writerow([name, f"{attack_success_rate(outcomes):.4f}", f"{benign_preservation_rate(outcomes):.4f}"])

    coverage_path = out_dir / "coverage_by_family.csv"
    families = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]
    with coverage_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["defense", *families])
        for name, outcomes in results.items():
            cov = coverage_by_family(outcomes)
            writer.writerow([name, *[f"{cov.get(fam, 0.0):.4f}" for fam in families]])

    print(f"Wrote {summary_path}")
    print(f"Wrote {coverage_path}")


if __name__ == "__main__":
    results = run()
    write_reports(results, Path(__file__).resolve().parents[1] / "results")
