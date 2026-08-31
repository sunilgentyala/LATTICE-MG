"""Tool Authorization Manifest (TAM) — Section VI.C.

Authorizes an exact operation (provider, endpoint, model family, account,
region, action, parameter ceilings), not merely a server. This is the
control that closes the confused-deputy gap described for A8 / G9-G10.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolAuthorizationManifest:
    provider: str
    endpoint: str
    model_family: str
    account: str
    region: str
    allowed_actions: frozenset[str]
    max_duration_s: float | None = None
    max_resolution_px: int | None = None
    input_source_allowlist: frozenset[str] = field(default_factory=frozenset)


@dataclass
class ToolCall:
    provider: str
    endpoint: str
    model_family: str
    account: str
    region: str
    action: str
    duration_s: float | None = None
    resolution_px: int | None = None
    input_source: str | None = None


@dataclass
class ToolCallVerdict:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


def check_tool_call(call: ToolCall, manifest: ToolAuthorizationManifest) -> ToolCallVerdict:
    """Denies a call the moment it drifts from the exact authorized operation.

    Catches: provider hopping, undocumented model substitution, region
    exfiltration of a private asset, and out-of-manifest actions (A8).
    """
    reasons: list[str] = []
    if call.provider != manifest.provider:
        reasons.append(f"provider mismatch: {call.provider} != {manifest.provider}")
    if call.endpoint != manifest.endpoint:
        reasons.append(f"endpoint mismatch: {call.endpoint} != {manifest.endpoint}")
    if call.model_family != manifest.model_family:
        reasons.append(f"model_family mismatch: {call.model_family} != {manifest.model_family}")
    if call.account != manifest.account:
        reasons.append(f"account mismatch: {call.account} != {manifest.account}")
    if call.region != manifest.region:
        reasons.append(f"region mismatch: {call.region} != {manifest.region}")
    if call.action not in manifest.allowed_actions:
        reasons.append(f"action not authorized: {call.action} not in {sorted(manifest.allowed_actions)}")
    if manifest.max_duration_s is not None and (call.duration_s or 0) > manifest.max_duration_s:
        reasons.append(f"duration {call.duration_s}s exceeds ceiling {manifest.max_duration_s}s")
    if manifest.max_resolution_px is not None and (call.resolution_px or 0) > manifest.max_resolution_px:
        reasons.append(f"resolution {call.resolution_px}px exceeds ceiling {manifest.max_resolution_px}px")
    if manifest.input_source_allowlist and call.input_source not in manifest.input_source_allowlist:
        reasons.append(f"input source not allowlisted: {call.input_source}")
    return ToolCallVerdict(allowed=not reasons, reasons=reasons)
