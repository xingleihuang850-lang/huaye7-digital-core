VERDICT: A1_COMPLETE_WITH_CONSTRAINTS_ALLOW_A2_DESIGN_ONLY

Carried-forward binding constraint: 3D Euler/Minkowski remain NOT_IMPLEMENTED_FAIL_CLOSED; must be implemented and phantom-validated before any A2 execution. WITH_CONSTRAINTS (not plain COMPLETE) because topology plumbing is only partially exercised and the toy volume is not committed (reproducibility rests on seed+source hash alone).

1. Verdict: A1_COMPLETE_WITH_CONSTRAINTS_ALLOW_A2_DESIGN_ONLY.

2. Toy metric-plumbing only? Yes. 8³ synthetic volume, voxel_spacing=synthetic_no_physical_spacing, route_label=synthetic_toy_plumbing, purpose limited to verifying 3D metric code paths + artifact package shape. All four known-answer phantoms are mathematically correct: all_solid (φ=0), all_pore (φ=1), x_channel (φ=1/64, S₂ lag1 x=1/64, percolation true/false/false), isolated_voxel (φ=1/512, LCC=1, no percolation). 3/3 branch + 42/42 suite pass; 5/5 hashes OK.

3. HY7 scientific evidence? No — and correctly so. Manifest declares scientific_status=not_evidence, no_hy7_scientific_claim=true, forbidden_claims.txt present. These are plumbing checks on synthetic phantoms; they carry zero physical meaning for HY7.

4. Prior binding conditions (ALLOW_A1_WITH_CONSTRAINTS) satisfied? Yes, as evidenced by manifest flags: volume_committed_to_git=false (no .npy/path file), no_training, no_new_sampling_from_model, no_checkpoint, no_actual_2d_to_3d_reconstruction all true; Euler/Minkowski honored fail-closed on all phantoms; connectivity semantics declared (6-conn pore / 26-conn solid, face-touching percolation, ndarray axis mapping). Compliance assessed against manifest flags mapping to prior constraints.

5. May enter A2? Yes — A2 DESIGN ONLY. A2 execution is NOT authorized by this gate.

6. A2 design may include (documents/specs only, no runs producing artifacts): design docs + interface/schema specs; 3D Euler/Minkowski algorithm design (connectivity handling, complementary 6/26); phantom-suite extension with analytically known answers — including phantoms with known Euler characteristic (sphere, torus, hollow cube) AND an asymmetric phantom to disambiguate periodic vs non-periodic S₂ (x_channel does not discriminate this); metric acceptance criteria; real 2D→3D reconstruction pipeline architecture (design only); provenance/hash/manifest conventions; test plan; risk register; A2 execution gate criteria.

7. Still forbidden (unchanged, verbatim): A2 execution of any kind; real 2D→3D reconstruction; model training/fine-tuning; new sampling from any model; checkpoint creation/loading; voxel volume export or git commit; any HY7 scientific claim from A1 or A2 design outputs.

8. Required before A2 EXECUTION:
   (a) 3D Euler/Minkowski — may REMAIN fail-closed during A2 design, but MUST be implemented and phantom-validated before A2 execution if any A2 metric/acceptance-criterion/claim depends on topology; otherwise explicitly de-scoped in the A2 design doc with justification and fail-closed status persisted in manifests. No silent fail-closed at execution time.
   (b) Toy-volume commit OR deterministic-regeneration proof (seed+source-hash round-trip test) so reproducibility does not rest on seed alone.
   (c) Pin the S₂ boundary-condition convention (periodic vs non-periodic) and test with a discriminating asymmetric phantom.
   (d) Scale-up validation beyond 8³.
   (e) A fresh strict gate review before any A2 execution.

This gate authorizes design documents only. A separate strict gate is required to authorize A2 execution.
