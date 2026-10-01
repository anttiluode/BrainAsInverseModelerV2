# Dendritic Lens Implementation Plan

> For agentic workers: use superpowers:executing-plans to implement this plan task-by-task. Execution is inline under the user's existing authorization.

**Goal:** Deliver a cable-based inverse instrument, its blind spots, and a working interactive demo.

**Architecture:** A passive cable generates temporal fingerprints and current history coordinates. A small SVD inverse and training-only quadratic readout evaluate two uses of the same circuit. A static demo consumes exported experiment data.

**Tech Stack:** Python, NumPy, SciPy, unittest, plain browser JavaScript.

**Spec:** docs/superpowers/specs/2026-10-01-dendritic-lens-design.md

## Global Constraints

- Python >=3.10, NumPy >=1.24, SciPy >=1.10; no browser network dependencies.
- 19 voltage states, six three-compartment branches; physical constants and experiment schedules exactly as frozen in the spec.
- Training and held-out trajectories are disjoint; normalization and decoder use training data only.
- No future input, privileged hidden labels in the observer, or reuse of yesterday's unverified numbers.
- Publish code, results, and demo together; verify the remote commit and files.

## Review Focus

- Rank-deficient symmetric responses must produce ambiguity without NaNs.
- Zero or large noise must never divide by zero or claim invented resolution.
- Decoder normalization must stay frozen when test values are extreme.
- Observer outputs before an input perturbation must stay unchanged.
- Demo controls must stay responsive and usable on narrow screens.

## Task 1: physical cable and temporal inverse

**Files:** dendritic_lens/cable.py, dendritic_lens/inverse.py, tests/test_cable.py, tests/test_inverse.py, requirements.txt.

**Interfaces:** Cable(capacitance, conductance, ports); make_cable(diverse=True, tau_scale=1.0); Cable.transition(dt_ms) -> (F,H); Cable.encode(currents, dt_ms) -> voltage history; impulse_operator(cable, dt_ms=0.5, steps=400, pulse_ms=1.0, current_na=0.01) -> K; svd_inverse(K, sigma) -> inverse, singular values, retained mask.

- [ ] Write tests for the analytic single-compartment response, passive energy decay, axial conservation, causality, symmetric twins, full-rank noiseless inverse, noise truncation, and invalid dt/noise.
- [ ] Run python -m unittest discover -s tests -v; observe missing APIs fail.
- [ ] Implement exact ZOH discretization and SVD truncation.
- [ ] Run the suite; expected all task tests pass.
- [ ] Commit and save a verified remote feature-branch checkpoint.

## Task 2: causal world-state evaluation

**Files:** dendritic_lens/world.py, dendritic_lens/readout.py, tests/test_world.py, tests/test_readout.py.

**Interfaces:** lorenz(initial, steps, dt=0.01) -> states; delay_features(signal, size=19, stride=2) -> features; exponential_features(signal, dt_ms=1.0, size=19) -> features; QuadraticReadout.fit(features, targets), predict(features); normalized_rmse(truth, prediction, scale) -> float.

- [ ] Write tests for causal delay/filter histories, fixed Lorenz derivative/short integration, quadratic held-out prediction, frozen normalization, and constant features.
- [ ] Run the focused tests; observe missing APIs fail.
- [ ] Implement the world and training-only standardized quadratic ridge readout.
- [ ] Run the full suite; expected all tests pass.
- [ ] Commit.

## Task 3: frozen experiment and receipt

**Files:** dendritic_lens/experiment.py, tests/test_experiment.py, results/receipt.json, site/data.js, scripts/run_experiment.py.

**Interfaces:** run_experiment(output_dir, site_dir) -> receipt; exported data includes cable K/U/S/Vt and held-out trajectories.

- [ ] Write a small integration test for seeded output, equal absolute noise, hidden labels excluded from observer inputs, and a held-out fixture with an independent unrecoverable variable.
- [ ] Run it; observe the missing runner fail.
- [ ] Implement the exact frozen schedule, all comparisons, mismatch and fixed-noise checks, and artifact export.
- [ ] Run the integration test, then OPENBLAS_NUM_THREADS=1 python scripts/run_experiment.py; expected finite receipt with declared seeds and measurements, regardless of scientific outcome.
- [ ] Inspect every comparison, document limitations, and commit the receipt.

## Task 4: visible demo and publication

**Files:** site/index.html, site/core.js, site/app.js, site/style.css, tests/core.test.cjs, README.md, docs/findings.md, .github/workflows/checks.yml.

**Interfaces:** JS reconstruct(operator, observation, sigma) mirrors Python's declared SVD inverse; app consumes site/data.js.

- [ ] Write JS tests against a hand-derived diagonal operator and the exported Python fixture; run node --test tests/core.test.cjs and observe missing code fail.
- [ ] Implement the static interactive demo and explanatory copy.
- [ ] Run Python and JS suites; expected no failures.
- [ ] Inspect desktop/mobile browser renders and exercise architecture, snapshot, noise, and slider changes.
- [ ] Request one fresh whole-branch review, fix material findings, publish all verified files, and read remote main/README/results/demo back.
