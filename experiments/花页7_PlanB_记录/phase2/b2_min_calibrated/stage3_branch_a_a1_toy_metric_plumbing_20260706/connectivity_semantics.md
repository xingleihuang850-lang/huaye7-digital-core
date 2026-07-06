# HY7 Stage 3 Branch A A1 connectivity semantics

Status: synthetic toy metric-plumbing only; not HY7 scientific evidence.

- pore-phase connectivity: 6-neighborhood (face-connected voxels only).
- complementary solid connectivity: 26-neighborhood is declared for future Euler/Minkowski work to avoid dual-connectivity ambiguity, but solid components are not used by this A1 implementation.
- percolation definition: a single pore-phase connected component touches both opposing faces along axis k.
- x/y/z axes map to ndarray axes 0/1/2 in the synthetic toy volume.
- 2D x/y penetrate inherited from Stage 2 remains 2D tile-level only and must not be interpreted as 3D permeability or 3D connectivity.
- Euler/Minkowski status: NOT_IMPLEMENTED_FAIL_CLOSED in A1.
