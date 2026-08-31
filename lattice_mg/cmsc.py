"""Cross-Modal Safety Contract (CMSC), Section VI.B, Table IV-A/B."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .request import MediaRequest
from .risk import RiskVector


def _digest(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass
class CrossModalSafetyContract:
    """Canonical, integrity-protected record binding a request to a decision.

    Field names follow Table IV-A (binding) and Table IV-B (enforcement).
    ``signature`` is an HMAC-SHA256 over the contract body, standing in for
    "digitally signed or otherwise integrity-protected by the enforcement
    service" (Section VI.B). A downstream tool that changes the operation
    invalidates the signature.
    """

    request_digest: str
    surface_id: str
    intent_graph_digest: str
    risk_vector: dict[str, float]
    identity_consent: dict[str, Any]
    operation_limits: dict[str, Any]
    inspection_plan: list[str]
    decision_and_expiry: dict[str, Any]
    provenance_policy: dict[str, Any]
    issued_at: float = field(default_factory=time.time)
    signature: str = ""

    def body(self) -> dict[str, Any]:
        return {
            "request_digest": self.request_digest,
            "surface_id": self.surface_id,
            "intent_graph_digest": self.intent_graph_digest,
            "risk_vector": self.risk_vector,
            "identity_consent": self.identity_consent,
            "operation_limits": self.operation_limits,
            "inspection_plan": self.inspection_plan,
            "decision_and_expiry": self.decision_and_expiry,
            "provenance_policy": self.provenance_policy,
            "issued_at": self.issued_at,
        }

    def sign(self, key: bytes) -> None:
        blob = json.dumps(self.body(), sort_keys=True, default=str).encode("utf-8")
        self.signature = hmac.new(key, blob, hashlib.sha256).hexdigest()

    def verify(self, key: bytes) -> bool:
        blob = json.dumps(self.body(), sort_keys=True, default=str).encode("utf-8")
        expected = hmac.new(key, blob, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, self.signature)


def build_cmsc(
    request: MediaRequest,
    intent_graph_digest: str,
    risk: RiskVector,
    surface_id: str,
    decision: str,
    key: bytes,
    identity_consent: dict[str, Any] | None = None,
    operation_limits: dict[str, Any] | None = None,
    inspection_plan: list[str] | None = None,
    provenance_policy: dict[str, Any] | None = None,
    expiry_seconds: float = 300.0,
) -> CrossModalSafetyContract:
    request_digest = _digest(
        {"text": request.text, "images": request.images, "video": request.video,
         "audio": request.audio, "history": request.history}
    )
    contract = CrossModalSafetyContract(
        request_digest=request_digest,
        surface_id=surface_id,
        intent_graph_digest=intent_graph_digest,
        risk_vector=dict(risk.categories),
        identity_consent=identity_consent or {"subject": None, "scope": None, "proof": None},
        operation_limits=operation_limits or {},
        inspection_plan=inspection_plan or [],
        decision_and_expiry={
            "decision": decision,
            "expires_at": time.time() + expiry_seconds,
        },
        provenance_policy=provenance_policy or {"manifest_required": True},
    )
    contract.sign(key)
    return contract
