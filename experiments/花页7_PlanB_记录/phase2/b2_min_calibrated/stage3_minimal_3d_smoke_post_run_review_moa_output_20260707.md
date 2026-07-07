Verdict: REDESIGN_BEFORE_ANY_A2_SMALL_GATE

Rationale:
1. Zero percolation on all three axes + near-zero connected porosity (0.53% pore basis / 0.031% total, LCC == connected fraction so one tiny component dominates) + identically-zero flow proxy = no positive connectivity signal to gate any scaling on.
2. Key technical tell: S2 lag-1 anisotropy — x=0.0034 vs y=0.0358 / z=0.0372, ~10× decorrelation along the slice-stacking axis. This is the classic signature of per-slice 2D nnUNet inference producing inter-slice inconsistency, which mechanically destroys 3D connectivity. Non-percolation may be a 2D→3D assembly artifact, not proven rock/route failure — a design problem, not a scaling-constraint problem.
3. Euler/Minkowski explicitly de-scoped fail-closed → topology cannot corroborate anything; the evidence base is incomplete by construction. Absence is not positive evidence.
4. This is a single 64×128×128 sub-REV subvolume labeled scientific_status=diagnostic_smoke_not_evidence; qmatch is planning_anchor_only, not the formal acceptance route. So neither "scientific success" nor terminal "route is dead" can be claimed from it — which is exactly why STOP over-reads it and A2-small under-respects the negative evidence.

Still-forbidden (unchanged): A2-small/medium execution; full 2D→3D campaign; any training/fine-tuning; checkpoint operations; HY7 scientific acceptance; B2-min final pass; qmatch formal acceptance; any validated-permeability claim; any generative digital-well claim. Additionally forbidden: interpreting the flow proxy as permeability or positive flow; re-running the smoke on cherry-picked slices to "find" percolation; silently remediating or dropping the failed chunk ep015_chunk000_063 (it stays visible).

Next allowed artifact/action (the only one): a metadata-only root-cause / redesign package — same hygiene as the current 12-file package (no .npy/.npz/.pt, no volumes, no weights), e.g. stage3_smoke_rca_redesign_plan_<date>_run01, containing:
- Root-cause analysis of the S2 x-axis decorrelation and non-percolation, with ranked, discriminating hypotheses: (a) inter-slice 2D-inference inconsistency, (b) sub-REV subvolume, (c) calibration threshold in hy7-gray-calibration-qmatch-v1, (d) genuinely tight rock.
- Paper-only redesign proposal: inter-slice consistency check protocol, alternative subvolume-selection criteria, minimum-REV estimation plan, and the explicit criteria a future second smoke must hit before an A2-small gate is even discussable.
- Preserved provenance: source path + sha256 24655b…b7b2, slice 384:448, shape 64×128×128, frozen route identifiers (nnUNet ep015_qmatch, hy7-gray-calibration-qmatch-v1, formal ep015_all planning_anchor_only), failed chunk ep015_chunk000_063 kept visible, scientific_status=diagnostic_smoke_not_evidence carried forward.

This is a clean negative diagnostic, not a success. No execution, model runs, or volume generation is permitted; any future reconsideration requires a new gate and a different candidate subvolume or route.
