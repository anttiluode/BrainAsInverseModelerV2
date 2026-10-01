# BrainAsInverseModelerV2 — The Dendritic Lens

Can a dendritic cable turn a restricted observation into a readable fingerprint of hidden causes?

This repository makes that question runnable. It uses an **illustrative 19-compartment passive cable** (six three-compartment branches plus a soma) in two experiments:

1. **Temporal tomography:** six hidden branch amplitudes generate one soma voltage trace. A truncated-SVD inverse asks which source directions survive.
2. **Hidden-state reconstruction:** only the `x` coordinate of a Lorenz system drives the cable. A training-only evaluation decoder asks how much withheld `y,z` information remains in the cable's ongoing state.

The result is useful but bounded: **history inside the cable contains hidden-state information, but ordinary delay coordinates do better on this benchmark.** Symmetry destroys source identity, a one-sample soma snapshot destroys most source dimensions, and a slightly wrong cable model can fit the waveform while recovering the wrong causes.

## Measured result

Frozen full run (`OPENBLAS_NUM_THREADS=1 python scripts/run_experiment.py`):

| Test | Result |
|---|---:|
| Diverse cable, six pulse amplitudes, zero noise | RMSE **2.87×10⁻¹⁵**, 6/6 modes |
| Symmetric cable, same task, zero noise | RMSE **0.2649**, 1/6 modes |
| Diverse cable at 5% reference-RMS voltage noise | RMSE **0.1577**, 5/6 modes |
| Diverse cable at fixed 0.01 mV noise | RMSE **0.2530**, 3/6 modes |
| One soma sample at 20 ms, diverse cable | RMSE **0.3271**, 1 mode |
| 20% time-constant mismatch | input RMSE **0.2168** while waveform residual is **0.000752** reference RMS |

Hidden Lorenz `y,z` recovery from only observed `x`:

| Observer coordinates | Held-out mean NRMSE | Mean R² |
|---|---:|---:|
| 19 raw delays | **0.0777** | 0.9938 |
| diverse cable state | **0.1774** | 0.9665 |
| 19 exponential traces | **0.2043** | 0.9479 |
| symmetric cable state | **0.2792** | 0.9112 |
| current `x` only | **0.6216** | 0.5904 |
| diverse cable reset every sample | **0.6216** | 0.5904 |
| soma alone | **0.6777** | 0.4938 |

With 2% input noise, the diverse cable changes only slightly (0.1790 NRMSE), while raw delays degrade to 0.0984. An independent hidden variable that never affects `x` remains unrecoverable (NRMSE 0.9945, R² −0.0052).

A held-out same-present example is also found: two moments differ in current `x` by only **0.0149 training standard deviations**, while their hidden `y,z` states are **3.96 standard deviations apart**.

## Interactive demo

[Open site!](https://anttiluode.github.io/BrainAsInverseModelerV2/site/index.html) directly in a browser. It has no network dependencies.

The demo recomputes the forward soma signal and inverse locally. To keep the self-contained browser payload small, generated calibration/trajectory arrays are stored as Float32; the authoritative full-precision metrics remain in `results/receipt.json`, and the browser fixture is checked to 2e-6 amplitude precision. Try the presets:

- **Readable mix:** diverse branch dynamics, full trace, no noise.
- **Indistinguishable twins:** identical branches. The trace determines only their sum; the minimum-norm inverse spreads the estimate across indistinguishable sources.
- **Noise:** weak singular directions disappear as the declared three-sigma cutoff rises.
- **Wrong calibration:** the true cable is 20% slower while the inverse remains nominal, showing that a small waveform residual need not imply correct hidden causes.

Switch the readout to a **single 20 ms soma sample** to see the observable rank collapse to one.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
node --test tests/core.test.cjs
OPENBLAS_NUM_THREADS=1 python scripts/run_experiment.py
```

`results/receipt.json` records the exact seeds, dependency versions, settings, source SHA-256 hashes, and measured comparisons. `site/data.js` is generated from the same run.

## Claim boundary

This is a mechanism demonstration, not a fitted biological neuron and not evidence that dendrites literally implement Takens delay coordinates. Cable dynamics provide one physical way to create history-dependent coordinates; the experiment asks what information those coordinates preserve. The hidden-state labels train an **evaluation decoder** and never enter the observer. The result does not establish an autonomously learned world model, ephaptic communication, spike-waveform coding, consciousness, or biological optimality.

See [`docs/findings.md`](docs/findings.md) for the experiment logic and failure modes, and the frozen design in [`docs/superpowers/specs/2026-10-01-dendritic-lens-design.md`](docs/superpowers/specs/2026-10-01-dendritic-lens-design.md).
