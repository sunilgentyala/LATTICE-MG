"""Risk vector, pre-generation score (Eq. 1), and the ALLOW gate (Eq. 2)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

DEFAULT_WEIGHTS = {
    "text": 1.0,
    "image": 0.9,
    "video": 0.9,
    "audio": 0.6,
    "history": 0.7,
    "tool": 0.8,
}

DEFAULT_GAMMA = 1.2


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class RiskVector:
    """rho(R) = [rho_1, ..., rho_k] per-category risk scores in [0, 1]."""

    categories: dict[str, float] = field(default_factory=dict)

    def max_score(self) -> float:
        return max(self.categories.values(), default=0.0)

    def exceeds(self, thresholds: dict[str, float]) -> list[str]:
        """Categories whose score is >= its threshold (violates Eq. 2's ALLOW clause)."""
        return [c for c, v in self.categories.items() if v >= thresholds.get(c, 1.0)]


def r_pre(
    s_text: float,
    s_image: float,
    s_video: float,
    s_audio: float,
    s_history: float,
    s_tool: float,
    phi: float,
    weights: dict[str, float] | None = None,
    gamma: float = DEFAULT_GAMMA,
) -> float:
    """Eq. 1: r_pre = sigma(w.s + gamma * Phi(G(R))).

    Setting gamma = 0 reproduces the unimodal-failure case described for
    gap G3 (safe-per-modality content that is unsafe in composition).
    """
    w = weights or DEFAULT_WEIGHTS
    linear = (
        w["text"] * s_text
        + w["image"] * s_image
        + w["video"] * s_video
        + w["audio"] * s_audio
        + w["history"] * s_history
        + w["tool"] * s_tool
        + gamma * phi
    )
    return _sigmoid(linear - 3.0)  # bias centers a "all zero" request near r_pre ~ 0.05


@dataclass(frozen=True)
class GateInvariants:
    """C_identity, C_tool, C_lineage, C_inspection from Eq. 2 (True = satisfied)."""

    identity: bool = True
    tool: bool = True
    lineage: bool = True
    inspection: bool = True

    def all_hold(self) -> bool:
        return self.identity and self.tool and self.lineage and self.inspection


def allow_gate(
    risk: RiskVector,
    thresholds: dict[str, float],
    invariants: GateInvariants,
) -> bool:
    """Eq. 2: ALLOW iff (for all j, rho_j < tau_j) AND all invariants hold."""
    below_threshold = all(v < thresholds.get(c, 1.0) for c, v in risk.categories.items())
    return below_threshold and invariants.all_hold()
