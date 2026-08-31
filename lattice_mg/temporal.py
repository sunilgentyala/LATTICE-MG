"""Temporal Risk Lattice — Section VI.E, Eq. 3.

Partitions a video into overlapping windows with adaptive density and
scores transitions between boundary states, so a violation that exists
only in the infill between two benign samples is not hidden by sparse
sampling (gaps G4-G5; families A6-A7).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Window:
    start_s: float
    end_s: float
    p: float  # window-level risk probability


@dataclass
class Transition:
    start_window: int
    end_window: int
    q: float  # transition/trajectory risk probability


@dataclass
class TemporalRiskLattice:
    windows: list[Window] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)
    boundary_pair_risk: float = 0.0  # b(start, end) in Eq. 3

    def cumulative_window_risk(self) -> float:
        """1 - product_t(1 - p_t): catches repeated moderate evidence."""
        product = 1.0
        for w in self.windows:
            product *= (1.0 - w.p)
        return 1.0 - product


def r_video(lattice: TemporalRiskLattice) -> float:
    """Eq. 3: r_video = max(max_t p_t, max_t q_t, cumulative, b(start,end))."""
    max_p = max((w.p for w in lattice.windows), default=0.0)
    max_q = max((t.q for t in lattice.transitions), default=0.0)
    cumulative = lattice.cumulative_window_risk()
    return max(max_p, max_q, cumulative, lattice.boundary_pair_risk)


def adaptive_windows(
    duration_s: float,
    base_window_s: float,
    motion_events_s: list[float],
    dense_window_s: float | None = None,
) -> list[tuple[float, float]]:
    """Denser sampling around motion/scene-cut/identity-change timestamps.

    Returns (start, end) spans covering the clip: base_window_s spacing by
    default, narrowed to dense_window_s within one base_window_s of any
    event timestamp (rapid motion, scene cuts, identity changes, detected
    text/audio events, or category uncertainty per Section VI.E).
    """
    dense = dense_window_s or (base_window_s / 4.0)
    spans: list[tuple[float, float]] = []
    t = 0.0
    while t < duration_s:
        near_event = any(abs(t - e) <= base_window_s for e in motion_events_s)
        step = dense if near_event else base_window_s
        spans.append((t, min(t + step, duration_s)))
        t += step
    return spans
