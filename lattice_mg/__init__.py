"""LATTICE-MG: reference decision-engine implementation.

Implements the architecture described in "LATTICE-MG: Cross-Modal, Temporal,
and Agent-Delegation Defenses Against Jailbreaks in Text-to-Image and
Text-to-Video Generation" (Gentyala & Darisi, 2026): the Cross-Modal Safety
Contract (CMSC), the Tool Authorization Manifest (TAM), the pre-generation
risk score and decision rule (Eq. 1-2), and the Temporal Risk Lattice
(Eq. 3).

This package contains no jailbreak payloads, bypass strings, or automation
for evading a named provider. The evaluation corpus (lattice_mg.corpus) is
schema-level: it encodes which detection *channels* a case requires, not
operational prompts.
"""

from .request import MediaRequest
from .intent_graph import IntentGraph, composition_score
from .risk import RiskVector, r_pre, allow_gate
from .cmsc import CrossModalSafetyContract, build_cmsc
from .tam import ToolAuthorizationManifest, ToolCall, check_tool_call
from .temporal import Window, Transition, TemporalRiskLattice, r_video
from .decision import Decision, DecisionEngine
from .evidence import EvidenceReceipt

__all__ = [
    "MediaRequest",
    "IntentGraph",
    "composition_score",
    "RiskVector",
    "r_pre",
    "allow_gate",
    "CrossModalSafetyContract",
    "build_cmsc",
    "ToolAuthorizationManifest",
    "ToolCall",
    "check_tool_call",
    "Window",
    "Transition",
    "TemporalRiskLattice",
    "r_video",
    "Decision",
    "DecisionEngine",
    "EvidenceReceipt",
]

__version__ = "0.1.0"
