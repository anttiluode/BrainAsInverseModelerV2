# V2 implementation record

2026-10-01: Inspected V1 and Varjoluotain through GitHub. V2 main contained only LICENSE at 6b90cef34b6144ff4d5cffa4a8951ee002180618. Local isolation is feature/dendritic-lens in a separate worktree. Existing user authorization covers the continuation and implementation choices.

The new design directly tests dendritic temporal fingerprints, followed by hidden-state reconstruction. It does not recreate or validate the lost cable-and-field build. All numerical settings are frozen in the design before collecting results.

Pre-flight: Task 1's Cable.encode and SVD interfaces feed Task 3; Task 2's feature/readout interfaces feed Task 3; Task 3's exported data feed Task 4. Interfaces agree.

Task 1: complete. Twelve physical/inverse tests pass with python -m unittest discover -s tests -v. RED: missing cable/inverse APIs; GREEN: analytic RC response, passivity, conservation, causal history, symmetric ambiguity, and SVD truncation.

Task 2: complete. RED: world/readout modules absent. GREEN: 20/20 full-suite tests pass, including fixed Lorenz RK4, causal delay/filter histories, exact quadratic recovery, constant-feature stability, and frozen training normalization under extreme held-out values.

Task 3: complete. The frozen experiment records the declared tomography seeds [0,1,2,3,4], dynamics training seeds [10,11,12,13,14,15], and held-out seeds [100,101,102,103]. The full run reproduces diverse six-source inversion at numerical precision in zero noise, exact rank collapse for symmetric branches, model-mismatch failure despite a small waveform residual, and hidden-state recovery from cable history that is useful but weaker than raw delay coordinates. The independent hidden-variable control remains unrecoverable. The CLI regression was changed to write only to temporary directories after it was found overwriting the full publication receipt during tests.

Task 4: complete. Browser reconstruction is covered by six Node tests, including rank-one symmetry and the one-soma-snapshot regression. Playwright/Chromium checks exercised readable, symmetric, noisy, wrong-calibration, and 20 ms snapshot states at desktop and mobile widths with no console/page errors or horizontal overflow. The browser snapshot bug was traced to numerical rank inflation in the fallback factorization and fixed by preserving the thin observable rank. Generated browser arrays are Float32 and checked against Python to a declared 2e-6 amplitude tolerance.

Publication review: self-review (no separate subagent tool available). The review checked the frozen focus items: rank-deficient symmetry, zero/large noise, training-only normalization, causality before perturbations, and narrow-screen behavior. A stale pre-compaction diverse-data shard was detected by Git blob comparison during remote publication and replaced with the verified compact shard.

Final verification before integration: local suite 23/23 Python tests and 6/6 Node tests green; a fresh full experiment reproduced diverse tomography RMSE 2.87381322503957e-15, symmetric tomography RMSE 0.2648868189619672, diverse-cable hidden-state NRMSE 0.17737440173586524, and delay-coordinate NRMSE 0.07771547488744764. GitHub Actions run 36811514976 completed successfully on the published feature branch, including Python tests, Node tests, and an independent frozen experiment rerun.
