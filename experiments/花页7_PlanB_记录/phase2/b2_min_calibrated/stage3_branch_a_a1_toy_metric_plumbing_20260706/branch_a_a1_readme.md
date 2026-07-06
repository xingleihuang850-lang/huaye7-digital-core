# HY7 Stage 3 Branch A A1 toy metric-plumbing dry-run

This package is not HY7 scientific evidence. It only verifies 3D metric code paths and artifact package shape using known-answer synthetic phantoms.

## Gate verdict

`ALLOW_A1_WITH_CONSTRAINTS`

## Boundary

- no training
- no new sampling from any model
- no checkpoint
- no actual 2D→3D reconstruction
- no voxel export as scientific output
- no B2-min final pass claim

## Known-answer phantom suite

The package validates all-solid, all-pore, single x-axis through-channel, and isolated-voxel phantoms. A run that only avoids crashing is not enough; expected porosity/percolation/connectivity values must match known answers.

## Toy volume policy

No toy volume is committed. This package contains metrics and provenance only. If future toy arrays are materialized, they must remain untracked or outside git and be recorded only by path/hash/size.

## Euler status

3D Euler/Minkowski is explicitly `NOT_IMPLEMENTED_FAIL_CLOSED`; it is not omitted or silently treated as passing.
