# LATTICE-MG

[![CI](https://github.com/sunilgentyala/LATTICE-MG/actions/workflows/ci.yml/badge.svg)](https://github.com/sunilgentyala/LATTICE-MG/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Site](https://img.shields.io/badge/site-live-0b5fff.svg)](https://sunilgentyala.github.io/LATTICE-MG/)
[![Status](https://img.shields.io/badge/paper-in%20preparation-lightgrey.svg)](#defensive-research-boundary)

**Cross-Modal, Temporal, and Agent-Delegation Defenses Against Jailbreaks in Text-to-Image and Text-to-Video Generation.**

Companion research prototype (paper in preparation, not yet submitted). Site: https://sunilgentyala.github.io/LATTICE-MG/

---

## The problem

Text-to-image and text-to-video jailbreak research and defenses are usually evaluated one modality, one frame, and one prompt filter at a time. That misses three real failure modes: (1) text and an image, or a benign image and a benign edit, can be safe *alone* but unsafe *together*; (2) a video can look safe at every sampled frame yet be unsafe in the *transition* between two benign boundary states; and (3) an agent (a coding assistant, an MCP-connected tool) can route a request to a weaker provider or a broader operation than the one a human approved. No single classifier (a prompt filter, an output image classifier, or a tool allowlist) has a control path for all of that at once.

## What LATTICE-MG does

LATTICE-MG binds one signed policy contract, the **Cross-Modal Safety Contract (CMSC)**, across the whole execution path of a generation request: normalized intent, cross-modal composition score, identity/consent state, and the exact operation being authorized. Agent-mediated generation is additionally constrained by a **Tool Authorization Manifest (TAM)** that authorizes an exact provider/endpoint/model/account/region/action, not just an allowlisted server, closing the "confused deputy" gap where a broad server-level allowlist unintentionally covers editing or video-extension endpoints it was never meant to. Video is evaluated with a **Temporal Risk Lattice**: overlapping windows at adaptive density plus a transition score between boundary states, so a violation that only exists in the infill between two sampled frames isn't hidden by sparse sampling.

This repository is a **reference implementation and research simulator**, not a production integration: it implements the CMSC, TAM, the pre-generation risk score and four-way decision rule (Eq. 1-2), and the Temporal Risk Lattice (Eq. 3) from the paper as real, tested code, plus a schema-level coverage-simulation harness that reproduces the paper's Table VI claims as runnable numbers instead of prose. It does not call any live generation platform and contains no jailbreak payloads, bypass strings, or circumvention automation for any named provider; see "Defensive research boundary" below.

## Repository layout

```
lattice_mg/          core package: request/intent-graph, CMSC, TAM, risk score + decision engine,
                     temporal risk lattice, evidence receipt, corpus generator, baseline profiles
experiments/         schema-level coverage-simulation harness (run_evaluation.py)
tests/               correctness tests for every formal claim in the design (Eq. 1-3, CMSC
                     tamper-evidence, TAM denial, decision-engine four-way logic, temporal lattice)
results/             CSV/markdown output from experiments/ (regenerable, not fabricated)
docs/                GitHub Pages site source
```

## Quickstart

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
python experiments/run_evaluation.py   # writes results/metrics_summary.csv, results/coverage_by_family.csv
```

## Headline result

Schema-level coverage simulation (960 adversarial cases across 8 attack families A1-A8, 480 benign hard negatives; see `results/scenarios.md` for exactly what is and isn't being measured):

| defense | attack success rate | benign preservation rate |
|---|---|---|
| prompt filter only | 0.87 | 0.92 |
| prompt + image output classifier | 0.71 | 0.97 |
| prompt + sparse video sampling | 0.74 | 0.98 |
| tool allowlist only | 0.96 | 1.00 |
| **LATTICE-MG** | **0.02** | **1.00** |

These are real numbers from real, deterministic code (`experiments/run_evaluation.py`, seed 2026), **not** measurements against Grok, ChatGPT, Sora, Claude Code, or any other live platform. They demonstrate that the architecture, as specified, has an observable control path for attack families that channel-limited baselines structurally cannot see (cross-modal composition, multi-turn context, edit lineage, temporal transitions, and agent tool-hopping). Read `results/scenarios.md` before citing any number from this repo.

## Defensive research boundary

No weaponized prompts, transformation templates, or prohibited media are generated, stored, or disclosed anywhere in this repository. The evaluation corpus (`lattice_mg/corpus.py`) is schema-level: every case records which detection *channel* carries the discriminating evidence, never an operational prompt. This matches the paper's own defensive research boundary (Section II.B).

## Honest limitations

- Detection and false-positive probabilities in `lattice_mg/baselines.py` are illustrative defaults chosen to be directionally consistent with the paper's qualitative Table VI, not measurements from any real system.
- The CMSC signature uses HMAC-SHA256 for tamper-evidence in this reference implementation; a production deployment would use an asymmetric signature tied to the enforcement service's key material.
- The intent graph and temporal lattice here operate on declared schema features, not real vision/ASR/OCR models; wiring in real multimodal detectors is future work.
- This does not replace the authorized, preregistered, multi-platform empirical evaluation the paper defines in Section VII; it is a reproducibility artifact for the architecture's design claims.

---

## How to Cite

If you use LATTICE-MG in your research, please cite the software:

```bibtex
@software{gentyala2026latticemg,
  author    = {Gentyala, Sunil},
  title     = {LATTICE-MG},
  year      = {2026},
  url       = {https://github.com/sunilgentyala/LATTICE-MG}
}
```

Machine-readable metadata is in [`CITATION.cff`](CITATION.cff); GitHub shows it under "Cite this repository".

---

## License

MIT, see `LICENSE`.
