"""Evidence receipt, Section VI.F.

Internal record binding the CMSC digest, TAM digest, provider request id,
output hash, detector results, reviewer actions, and policy version. Kept
separate from provenance (a well-labeled unsafe output remains unsafe).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceReceipt:
    cmsc_digest: str
    tam_digest: str | None
    provider_request_id: str | None
    output_hash: str | None
    detector_results: dict[str, Any] = field(default_factory=dict)
    reviewer_action: str | None = None
    policy_version: str = "default-v1"
    created_at: float = field(default_factory=time.time)

    def is_complete(self) -> bool:
        """Evidence Completeness metric (Table V-B): full version/lineage/detector record."""
        return bool(self.cmsc_digest and self.provider_request_id and self.detector_results)
