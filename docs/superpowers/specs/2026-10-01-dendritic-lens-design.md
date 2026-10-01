# The dendritic lens

## Intent

Antti's question is whether dendrites can do something operationally like Varjoluotain: transform restricted observations into a readable fingerprint of their hidden causes. V1 supplies the research framing. V2 must contain runnable experiments, measured results, an interactive local demo, and explicit blind spots. The user already authorized the continuation and implementation decisions; execution is inline.

## Scope and alternatives

A hand-designed filter bank would establish temporal reconstruction quickly. A passive cable tree additionally makes the physical forward operator explicit. Extracellular transmission is a later experiment. This deliverable chooses the cable tree and measures two uses of that same instrument: recovery of simultaneous branch inputs from a soma trace, and recovery of hidden dynamical coordinates from current branch voltages.

These are new experiments. The unverified numbers from the lost September 30 session are not targets, evidence, or results for this version. There is no ephaptic, spike-waveform, consciousness, learned morphology, or biological-validation claim.

## Passive cable

Use six branches with three compartments each plus one soma: 19 real voltage states. Capacitance is in nF, conductance in microSiemens, current in nA, voltage relative to rest in mV, and time in ms. The illustrative circuit has soma capacitance 0.05, soma leak 0.005, and branch compartment capacitance 0.01. Diverse branch membrane time constants are [3, 6, 12, 24, 48, 96] ms and axial conductances are [0.012, 0.009, 0.006, 0.004, 0.0025, 0.0015]. The symmetric control uses 24 ms and 0.004 on every branch. All values are illustrative, not fitted to biological cells.

The conductance matrix is leak plus the graph Laplacian. C dv/dt = -G v + B i, advanced by exact matrix exponential under a constant current during each sample. Soma index is zero. Each distal branch is an independent input port. Test current conservation of axial terms, passivity, a one-compartment analytic solution, causality, and symmetric ambiguity.

## Experiment 1: temporal tomography

Inject simultaneous 1 ms pulses of 0.01 nA times six unknown amplitudes in [0,1]. Observe soma every 0.5 ms for 200 ms. The six unit responses form K; voltage = K amplitudes + noise. The inverse is truncated SVD, retaining singular values greater than max(3 sigma, s_max * 1e-10), where sigma is independent Gaussian voltage noise per sample. Report the minimum-norm estimate without positivity clipping, which would add a prior.

Use symmetric and diverse cables, plus a soma snapshot at a fixed 20 ms. Noise fractions are [0, 0.0001, 0.001, 0.01, 0.05] of a fixed reference waveform RMS: the diverse cable driven by amplitudes all 0.5. Both architectures get the same absolute noise. Report an additional fixed 0.01 mV noise case. Test 64 random scenes for each seed [0,1,2,3,4], with matched scenes/noise across architectures. Metrics: amplitude RMSE, normalized measurement residual, singular values, retained modes at the declared contrast scale, and a symmetric twin pair. No inference of arbitrary waveforms: the pulse timing and shape are known.

Model mismatch uses data from a diverse cable with all branch time constants multiplied by 1.2, inverted with the nominal cable. Preserve the result even if waveform fit looks good while the inputs are wrong.

## Experiment 2: hidden dynamical state

Generate Lorenz (10,28,8/3) with RK4 at 0.01 dimensionless time. After a 1000-step world burn-in, observe 4000 steps. One observed step corresponds to 1 ms of cable time; this declared rescaling is illustrative. Only noisy x enters the observer, normalized by training x mean/std, as equal 0.01 nA-scaled currents at the six distal ports. Discard the first 500 observed steps and fit on every fourth sample.

Train trajectory seeds [10,11,12,13,14,15]; evaluate seeds [100,101,102,103]. Initial coordinates come from independent uniform draws in [-15,15], [-15,15], [5,35]. Fit normalization and decoder only on training trajectories. Evaluate 0 and 0.02 input noise, measured relative to training x standard deviation.

Compare full 19-compartment diverse cable state, symmetric cable state, 19 raw delays at two-sample spacing, a 19-state bank of independent exponential filters with geometrically spaced 3..96 ms constants, soma alone, and current observation alone. Pad the scalar baselines to 19 so all use the same 210-coefficient quadratic feature family per target. Every arm gets its own training-only normalizer and ridge decoder, with fixed regularization 0.001 times sample count; targets are y and z normalized by their training scale.

Report mean and per-trajectory normalized RMSE and R2; show truth and decoded y/z for one held-out trajectory. A same-present example must have current x within 0.02 training std and hidden-state separation greater than one training std. Include reset-at-readout features and an independent hidden variable that never affects x. An evaluation decoder using hidden labels measures information content; it is not a self-taught world model. No future input enters the observer.

## Demo and delivery

A static site uses bundled calibration responses and singular factors from the Python experiment. Six amplitude sliders, symmetry/diversity, trace/snapshot, and noise controls recompute the forward signal and truncated inverse locally. Show the hidden inputs, accessible soma trace, recovered inputs, singular spectrum, retained modes, and both reconstruction and measurement error. Include a held-out dynamical reconstruction panel driven by saved results. Browser computation must agree with Python on a fixed fixture and handle rank deficiency, zero noise, narrow screens, and repeated control changes.

Dependencies: Python >=3.10, NumPy >=1.24, SciPy >=1.10; standard-library unittest. Browser: plain HTML/CSS/JavaScript, no network dependencies. The demo opens from site/index.html directly; hosting is optional and is not configured by this task.

Save the frozen settings, dependency versions, actual results, provenance, and the command to reproduce them. Publish verified files to BrainAsInverseModelerV2 using GitHub's connector. Read the remote files and commit back before claiming delivery.
