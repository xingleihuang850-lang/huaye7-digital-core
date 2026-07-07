# S2 boundary semantics

The diagnostic S2 proxy uses lag-1 valid adjacent voxel pairs independently on x,
y, and z. It does not use periodic wrapping, padding, or cross-boundary pairs.
The boundary label is `lag_1_valid_pairs_no_wrap_no_periodic_boundary`.
