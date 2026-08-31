"""Request representation R = (H, T, I, V, A, M, P) from Section VI.A."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaRequest:
    """Normalized generation request.

    Fields mirror the paper's R = (H, T, I, V, A, M, P):
      H: relevant conversation / transformation history
      T: text
      I: input or reference images
      V: input video
      A: audio
      M: tool and model context
      P: active policy bundle

    ``signals`` carries schema-level evidence channels used by the reference
    decision engine and the evaluation harness (see lattice_mg.corpus). It is
    intentionally abstract: it never stores operational bypass content.
    """

    request_id: str
    history: list[str] = field(default_factory=list)
    text: str = ""
    images: list[str] = field(default_factory=list)
    video: str | None = None
    audio: str | None = None
    tool_context: dict[str, Any] = field(default_factory=dict)
    policy_bundle: str = "default-v1"
    signals: dict[str, float] = field(default_factory=dict)

    def signal(self, name: str) -> float:
        return float(self.signals.get(name, 0.0))
