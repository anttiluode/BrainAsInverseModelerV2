# V2 implementation record

2026-10-01: Inspected V1 and Varjoluotain through GitHub. V2 main contained only LICENSE at 6b90cef34b6144ff4d5cffa4a8951ee002180618. Local isolation is feature/dendritic-lens in a separate worktree. Existing user authorization covers the continuation and implementation choices.

The new design directly tests dendritic temporal fingerprints, followed by hidden-state reconstruction. It does not recreate or validate the lost cable-and-field build. All numerical settings are frozen in the design before collecting results.

Pre-flight: Task 1's Cable.encode and SVD interfaces feed Task 3; Task 2's feature/readout interfaces feed Task 3; Task 3's exported data feed Task 4. Interfaces agree.

Task 1: complete. Twelve physical/inverse tests pass with python -m unittest discover -s tests -v. RED: missing cable/inverse APIs; GREEN: analytic RC response, passivity, conservation, causal history, symmetric ambiguity, and SVD truncation.

Task 2: complete. RED: world/readout modules absent. GREEN: 20/20 full-suite tests pass, including fixed Lorenz RK4, causal delay/filter histories, exact quadratic recovery, constant-feature stability, and frozen training normalization under extreme held-out values.
