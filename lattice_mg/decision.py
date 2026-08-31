"""Four-way decision function D(R) — Section VI.D.

D(R) in {ALLOW, CONSTRAINED_ALLOW, REVIEW, REFUSE}. An automatic ALLOW
requires every category below its threshold and all gate invariants to
hold (Eq. 2). Otherwise the engine steps down to a constrained allow, a
human review, or a refusal, depending on how far risk exceeds tolerance
and whether the temporal/tool checks are the cause.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .risk import GateInvariants, RiskVector, allow_gate


class Decision(str, Enum):
    ALLOW = "allow"
    CONSTRAINED_ALLOW = "constrained_allow"
    REVIEW = "review"
    REFUSE = "refuse"


@dataclass
class DecisionEngine:
    thresholds: dict[str, float]
    refuse_margin: float = 0.25  # how far above threshold before REFUSE instead of REVIEW

    def decide(
        self,
        risk: RiskVector,
        invariants: GateInvariants,
        r_video_score: float = 0.0,
        video_threshold: float = 0.5,
    ) -> Decision:
        if allow_gate(risk, self.thresholds, invariants) and r_video_score < video_threshold:
            return Decision.ALLOW

        if not invariants.identity or not invariants.tool:
            # Consent/tool-authorization failures are not curable by constraining output.
            return Decision.REFUSE

        violations = risk.exceeds(self.thresholds)
        worst_excess = max(
            (risk.categories[c] - self.thresholds.get(c, 1.0) for c in violations),
            default=0.0,
        )
        video_excess = max(0.0, r_video_score - video_threshold)
        excess = max(worst_excess, video_excess)

        if excess >= self.refuse_margin:
            return Decision.REFUSE
        if excess > 0.0:
            return Decision.REVIEW
        # Only the lineage/inspection invariants failed; content risk itself is low.
        return Decision.CONSTRAINED_ALLOW
