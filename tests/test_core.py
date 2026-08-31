from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lattice_mg.baselines import ALL_PROFILES, LATTICE_MG, PROMPT_ONLY
from lattice_mg.cmsc import build_cmsc
from lattice_mg.corpus import ATTACK_FAMILIES, full_corpus, generate_adversarial_cases, generate_benign_cases
from lattice_mg.decision import Decision, DecisionEngine
from lattice_mg.intent_graph import IntentGraph, composition_score
from lattice_mg.request import MediaRequest
from lattice_mg.risk import GateInvariants, RiskVector, allow_gate, r_pre
from lattice_mg.tam import ToolAuthorizationManifest, ToolCall, check_tool_call
from lattice_mg.temporal import TemporalRiskLattice, Transition, Window, adaptive_windows, r_video


def test_corpus_sizes_match_paper():
    adv = generate_adversarial_cases()
    ben = generate_benign_cases()
    assert len(adv) == 12 * 8 * 10 == 960
    assert len(ben) == 480
    assert len(full_corpus()) == 1440
    assert set(c.attack_family for c in adv) == set(ATTACK_FAMILIES)


def test_composition_score_zero_without_flag():
    req = MediaRequest(request_id="r1", text="a landscape", signals={"cross_modal": 0.9})
    graph = IntentGraph()  # composition_flag defaults False
    assert composition_score(graph, req) == 0.0


def test_composition_score_reflects_signal_when_flagged():
    req = MediaRequest(request_id="r1", text="x", images=["y"], signals={"cross_modal": 0.7})
    graph = IntentGraph.from_request(req)
    assert graph.composition_flag is True
    assert composition_score(graph, req) == 0.7


def test_r_pre_monotonic_in_gamma():
    low = r_pre(0.1, 0.1, 0.0, 0.0, 0.1, 0.0, phi=0.0, gamma=0.0)
    high = r_pre(0.1, 0.1, 0.0, 0.0, 0.1, 0.0, phi=0.9, gamma=1.2)
    assert 0.0 <= low <= 1.0
    assert high > low  # G3: unimodal-only (gamma=0) underestimates cross-modal risk


def test_allow_gate_requires_all_invariants():
    risk = RiskVector(categories={"violence": 0.1})
    thresholds = {"violence": 0.5}
    ok = GateInvariants(identity=True, tool=True, lineage=True, inspection=True)
    bad = GateInvariants(identity=False, tool=True, lineage=True, inspection=True)
    assert allow_gate(risk, thresholds, ok) is True
    assert allow_gate(risk, thresholds, bad) is False


def test_decision_engine_four_way():
    engine = DecisionEngine(thresholds={"violence": 0.5}, refuse_margin=0.25)
    ok_inv = GateInvariants()
    assert engine.decide(RiskVector({"violence": 0.1}), ok_inv) == Decision.ALLOW
    assert engine.decide(RiskVector({"violence": 0.6}), ok_inv) == Decision.REVIEW
    assert engine.decide(RiskVector({"violence": 0.9}), ok_inv) == Decision.REFUSE
    no_consent = GateInvariants(identity=False)
    assert engine.decide(RiskVector({"violence": 0.1}), no_consent) == Decision.REFUSE


def test_cmsc_signature_detects_tamper():
    req = MediaRequest(request_id="r1", text="a synthetic portrait")
    risk = RiskVector({"violence": 0.05})
    key = b"test-key"
    contract = build_cmsc(req, intent_graph_digest="abc", risk=risk, surface_id="chatgpt-images",
                           decision="allow", key=key)
    assert contract.verify(key) is True
    contract.operation_limits["duration_s"] = 999  # simulate a downstream tool tampering
    assert contract.verify(key) is False


def test_tam_denies_provider_hop():
    manifest = ToolAuthorizationManifest(
        provider="grok", endpoint="images.generate", model_family="grok-imagine",
        account="acct-1", region="us", allowed_actions=frozenset({"generate"}),
    )
    legit = ToolCall(provider="grok", endpoint="images.generate", model_family="grok-imagine",
                      account="acct-1", region="us", action="generate")
    hopped = ToolCall(provider="another-provider", endpoint="images.generate", model_family="grok-imagine",
                       account="acct-1", region="us", action="generate")
    assert check_tool_call(legit, manifest).allowed is True
    verdict = check_tool_call(hopped, manifest)
    assert verdict.allowed is False
    assert any("provider mismatch" in r for r in verdict.reasons)


def test_temporal_lattice_boundary_pair_dominates():
    lattice = TemporalRiskLattice(
        windows=[Window(0, 1, 0.1), Window(1, 2, 0.1)],
        transitions=[Transition(0, 1, 0.2)],
        boundary_pair_risk=0.9,
    )
    assert r_video(lattice) == 0.9


def test_adaptive_windows_denser_near_events():
    spans = adaptive_windows(duration_s=10.0, base_window_s=2.0, motion_events_s=[5.0])
    near_event = [s for s in spans if abs(s[0] - 5.0) <= 2.0]
    assert any((e - s) < 2.0 for s, e in near_event)


def test_lattice_mg_dominates_baselines_on_every_channel():
    for profile in ALL_PROFILES:
        if profile is LATTICE_MG:
            continue
        for channel in profile.channel_scale:
            assert LATTICE_MG.detect_probability(channel) >= profile.detect_probability(channel)


def test_prompt_only_has_no_cross_modal_access():
    assert PROMPT_ONLY.channel_scale.get("cross_modal", 0.0) == 0.0
