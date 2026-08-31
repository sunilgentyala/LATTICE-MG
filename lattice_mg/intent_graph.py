"""Intent graph G(R) and the cross-modal composition term Phi(G(R))."""

from __future__ import annotations

from dataclasses import dataclass, field

from .request import MediaRequest


@dataclass
class IntentGraph:
    """A minimal typed graph over entities/actions/edges for a request.

    Nodes and edges are abstract labels (never operational prompt text).
    ``composition_flag`` records whether the graph contains a subgraph that
    is individually low-risk per modality but jointly high-risk, matching
    the "harmless object + harmless caption" example in Section VI.A.
    """

    nodes: list[str] = field(default_factory=list)
    edges: list[tuple[str, str, str]] = field(default_factory=list)  # (src, relation, dst)
    composition_flag: bool = False

    @classmethod
    def from_request(cls, request: MediaRequest) -> "IntentGraph":
        nodes = [f"entity:{i}" for i in range(len(request.images) + (1 if request.video else 0))]
        edges: list[tuple[str, str, str]] = []
        if request.images and request.text:
            edges.append(("text", "depicts", "image"))
        if request.video:
            edges.append(("image", "transforms-into", "video"))
        composition_flag = request.signal("cross_modal") > 0.0
        return cls(nodes=nodes, edges=edges, composition_flag=composition_flag)


def composition_score(graph: IntentGraph, request: MediaRequest) -> float:
    """Phi(G(R)) in Eq. 1: cross-modal composition risk in [0, 1].

    Uses the request's ``cross_modal`` evidence channel when the intent
    graph flags a jointly-risky subgraph; otherwise returns 0, reproducing
    the unimodal-failure case (G3) when gamma = 0 in Eq. 1.
    """
    if not graph.composition_flag:
        return 0.0
    return min(1.0, request.signal("cross_modal"))
