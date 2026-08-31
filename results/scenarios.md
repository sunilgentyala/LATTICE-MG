# Coverage simulation: what this is and isn't

`experiments/run_evaluation.py` runs five **decision-engine capability
profiles** against a synthetic, schema-level corpus of 960 adversarial
cases (12 policy categories x 8 attack families x 10 variants) and 480
benign hard negatives, as specified in Section VII.B of the paper. It
reproduces, as runnable code, the qualitative claims in the paper's
Table VI ("architectural control-path coverage, not measured attack
success rate").

**This is not a test against any live text-to-image or text-to-video
platform.** No provider is called. No operational bypass prompt exists
anywhere in this repository. Each corpus case only records *which
detection channel* (text, cross-modal composition, history, edit
lineage, temporal transition, dense sampling, or tool-operation binding)
carries the discriminating evidence for that case; each capability
profile only records *which channels a given defense design can observe,
and at what strength* (`lattice_mg/baselines.py`). The detection and
false-positive probabilities attached to each channel are illustrative
defaults chosen to be directionally consistent with the qualitative
claims in Table VI; they are not measurements from Grok, ChatGPT, Sora,
Claude Code, or any other product. Anyone can inspect, contest, or
replace them; that is the point of shipping them as a parameter table
instead of a paragraph of prose.

## Reproducing the results

```bash
python experiments/run_evaluation.py
```

writes `results/metrics_summary.csv` and `results/coverage_by_family.csv`
(seed = 2026, 5 repetitions per case per Section VII.C's minimum-repetition
guidance, majority vote across repetitions).

## Latest run

Per-family catch rate on the 960 adversarial cases (higher = more attack
families with an observable control path):

| defense | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|---|
| prompt_only | 1.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| prompt_plus_image | 1.00 | 0.28 | 0.51 | 0.00 | 0.28 | 0.17 | 0.07 | 0.00 |
| prompt_plus_sparse_video | 1.00 | 0.28 | 0.23 | 0.00 | 0.21 | 0.33 | 0.03 | 0.00 |
| tool_allowlist_only | 0.01 | 0.01 | 0.00 | 0.01 | 0.00 | 0.01 | 0.00 | 0.27 |
| **lattice_mg** | 1.00 | 0.97 | 0.99 | 0.98 | 0.99 | 0.97 | 0.92 | 0.99 |

Attack success rate / benign preservation rate:

| defense | attack success rate | benign preservation rate |
|---|---|---|
| prompt_only | 0.87 | 0.92 |
| prompt_plus_image | 0.71 | 0.97 |
| prompt_plus_sparse_video | 0.74 | 0.98 |
| tool_allowlist_only | 0.96 | 1.00 |
| **lattice_mg** | **0.02** | **1.00** |

These numbers regenerate deterministically from the seed above; they are
real output of real code, not hand-authored. They are reported here as a
reproducibility artifact for the architecture's design claims, not as an
empirical jailbreak-resistance result for any deployed system; that
requires the authorized, preregistered multi-platform evaluation the
paper defines in Section VII.
