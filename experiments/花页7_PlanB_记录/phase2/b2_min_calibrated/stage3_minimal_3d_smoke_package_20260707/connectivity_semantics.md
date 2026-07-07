# Connectivity semantics

- pore-phase connectivity: 6-neighborhood (face-connected voxels only).
- complementary solid/background connectivity: 26-neighborhood is declared to avoid dual-connectivity ambiguity; this launcher does not claim Euler/Minkowski validation.
- percolation definition: one pore-phase connected component touches both opposing faces along axis k.
- axis mapping: x/y/z -> ndarray axes 0/1/2.
- 2D x/y penetration must not be interpreted as 3D permeability or 3D connectivity.
