"""Capability profiles for the coverage-simulation harness (experiments/).

Table VI in the paper is a qualitative, analytical statement: "explicit
coverage" vs. "partial or absent coverage" per defense per attack family --
not a measured attack-success rate. This module turns that qualitative
table into a *parametrized, runnable* capability model so the coverage
claim can be checked against the synthetic schema corpus (citadel corpus)
instead of only asserted in prose.

Every probability below is an illustrative default, not a measurement
from a live platform. They are grouped here, in one place, specifically
so a reader can inspect, contest, or replace them; see README.md
"What the numbers mean" for that caveat.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .corpus import ATTACK_FAMILIES, FAMILY_CHANNEL

# p_detect[channel] = (detection prob when channel is available,
#                       detection prob when channel is absent -- the
#                       "generic heuristic catches it by luck" floor)
CHANNEL_DETECT_PROB: dict[str, tuple[float, float]] = {
    "text": (0.97, 0.05),
    "text_semantic": (0.85, 0.10),
    "cross_modal": (0.88, 0.05),
    "history": (0.83, 0.04),
    "lineage": (0.86, 0.05),
    "temporal_transition": (0.80, 0.06),
    "dense_sampling": (0.78, 0.07),
    "tool_binding": (0.90, 0.15),
}

# Weaker, server-level-only signal used by "tool allowlist only" for A8.
TOOL_SERVER_ALLOWLIST_PROB = 0.35

# False-positive (over-block) rate on benign hard negatives, per defense.
BENIGN_FALSE_POSITIVE_RATE = {
    "prompt_only": 0.24,
    "prompt_plus_image": 0.17,
    "prompt_plus_sparse_video": 0.16,
    "tool_allowlist_only": 0.02,  # never inspects content, so rarely over-blocks
    "lattice_mg": 0.06,
}


@dataclass(frozen=True)
class CapabilityProfile:
    """Which channels a defense variant can observe, and at what strength.

    ``channel_scale`` multiplies CHANNEL_DETECT_PROB's "available" branch:
    1.0 = full-strength access, values in (0, 1) = partial coverage as
    described qualitatively in Table VI, 0.0 = channel entirely absent.
    """

    name: str
    channel_scale: dict[str, float] = field(default_factory=dict)
    has_tool_operation_binding: bool = False
    has_tool_server_allowlist: bool = False

    def detect_probability(self, channel: str) -> float:
        p_with, p_without = CHANNEL_DETECT_PROB[channel]
        scale = self.channel_scale.get(channel, 0.0)
        if scale <= 0.0:
            return p_without
        return p_without + scale * (p_with - p_without)


PROMPT_ONLY = CapabilityProfile(
    name="prompt_only",
    channel_scale={"text": 1.0},
)

PROMPT_PLUS_IMAGE = CapabilityProfile(
    name="prompt_plus_image",
    channel_scale={
        "text": 1.0, "text_semantic": 0.4, "cross_modal": 0.5,
        "lineage": 0.4, "temporal_transition": 0.3, "dense_sampling": 0.2,
    },
)

PROMPT_PLUS_SPARSE_VIDEO = CapabilityProfile(
    name="prompt_plus_sparse_video",
    channel_scale={
        "text": 1.0, "text_semantic": 0.4, "cross_modal": 0.4,
        "lineage": 0.3, "temporal_transition": 0.45, "dense_sampling": 0.15,
    },
)

TOOL_ALLOWLIST_ONLY = CapabilityProfile(
    name="tool_allowlist_only",
    channel_scale={},
    has_tool_server_allowlist=True,
)

LATTICE_MG = CapabilityProfile(
    name="lattice_mg",
    channel_scale={c: 1.0 for c in CHANNEL_DETECT_PROB},
    has_tool_operation_binding=True,
    has_tool_server_allowlist=True,
)

ALL_PROFILES = [PROMPT_ONLY, PROMPT_PLUS_IMAGE, PROMPT_PLUS_SPARSE_VIDEO, TOOL_ALLOWLIST_ONLY, LATTICE_MG]

assert set(FAMILY_CHANNEL[f] for f in ATTACK_FAMILIES) <= set(CHANNEL_DETECT_PROB)
