# HY7 Stage 3 Branch A minimal 3D smoke package

Gate verdict: `ALLOW_MINIMAL_3D_SMOKE_ONLY`
Package status: `DIAGNOSTIC_SMOKE_METADATA_ONLY`
Scientific status: `diagnostic_smoke_not_evidence`

This package is a diagnostic smoke contract only. It is not A2 execution, not a
scientific acceptance result, and not a generative digital-well claim. The frozen
route is `nnUNet ep015_qmatch` with calibration `hy7-gray-calibration-qmatch-v1`; formal
`ep015_all` remains `planning_anchor_only`.

If prerequisite evidence or candidate source is absent, the package deliberately
fails closed while still writing the required 12 metadata files. Negative evidence
is retained as useful output rather than hidden.

No voxel arrays, weights, checkpoints, `.npy`, `.npz`, or `.pt` files are written
by this launcher.
