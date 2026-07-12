# HuaYe7 Digital Core / 花页7数字岩心研究仓库

This repository records the HuaYe7 (HY7, 花页7) multi-scale digital-rock workflow: data inventory, segmentation, 2D gray/sus generative modeling, topology-aware validation, and calibrated handoff toward digital-well / B2-min experiments.

本仓库用于留存 HY7 花页7数字岩心主线的代码、实验记录、阶段性证据和可复现实验入口。仓库只管理代码、轻量指标、图表和审计记录；大型原始体素、模型权重、`.npy/.pt/.nii.gz` 等重资产不直接入库，按 `.gitignore` 规则只在 manifest / sha256 / notes 中记录路径与证据。

## Current status

As of the latest committed state, the main research status is:

- HY7 is the primary mainline closure target.
- Phase 2 B1.1 has reached **conditional pass / 有条件阶段性闭合** after rock multi-model review.
- The frozen main candidate is `ep015` from the explicit Euler/maxCC rescue run.
- The B1.1 topology side is frozen: no second topology rescue, no gate relaxation, no 100/200ep scaling from the failed soft-pore branch.
- `ORIG raw` nnUNet remains a known failure mode; downstream use must explicitly apply gray calibration.
- The required calibrated inference preprocessing is `hy7-gray-calibration-qmatch-v1`.
- A calibrated B2-min baseline reproducibility package has been generated and recorded.

Key B1.1 closure evidence:

- `formal512 ep015@φ6.4`: S₂≈0.00034, Euler≈120.81, maxCC≈0.0641, gate pass.
- `nnUNet ep015_qmatch`: S₂≈0.00172, Euler≈116.15, maxCC≈0.0651, reverse_fail=False.
- held-out qmatch split generalization: ep015 even/odd split both pass.
- rock multi-expert review: B1.1 = conditional pass, not unconditional full pass.

## Repository layout

```text
.
├── src/                         # Python scripts and reusable utilities
├── tests/                       # Lightweight pytest tests
├── notes/                       # Research notes and decision records
├── experiments/                 # Lightweight experiment evidence and indexes
├── deliverables/                # Report/deck output area; large artifacts may be ignored
├── scripts/                     # Sync and utility scripts
└── .hermes/plans/               # Implementation plans generated during the workflow
```

Important files:

- `notes/30_阶段二_B11输出校准与checkpoint选择.md`  
  Main B1.1 decision record: checkpoint selection, formal gates, soft-pore closure, Euler/maxCC rescue, qmatch calibration, rock review, and B2-min entry notes.

- `src/hy7_phase2_ddpm.py`  
  Phase-2 DDPM training/sampling/evaluation script. Includes periodic validation, formal proxy selection, and explicit Euler/maxCC rescue controls.

- `src/hy7_gray_calibration.py`  
  Versioned qmatch / gray calibration preprocessing module. Current version: `hy7-gray-calibration-qmatch-v1`.

- `src/hy7_b2_min_package.py`  
  Packages the calibrated B2-min baseline evidence into manifest/readme/hash records.

- `src/hy7_remote_sync_audit.py`
  Read-only local/remote SHA audit. It maps Phase-1 PlanB to remote `src/`, Phase-2 runtime to remote `phase2/`, and blocks undeclared/local-only deployment.

- `.hermes/plans/2026-07-06_141348-calibrated-b2-min.md`  
  Calibrated B2-min implementation plan.

- `docs/workspace_cleanup_20260706.md`  
  Local symlink/empty-directory cleanup record and remote `00_ORDERED_VIEW` index description.

## Scientific gates and wording rules

Use these wording rules when citing repository results:

- Correct: “B1.1 conditional pass / 有条件阶段性闭合.”
- Correct: “Main candidate is ep015 with mandatory qmatch / gray calibration.”
- Incorrect: “B1.1 unconditionally passed.”
- Incorrect: “ORIG raw nnUNet passed.”
- Incorrect: “B2 can ignore calibration.”

Frozen B1.1 constraints:

1. Do not run a second B1.1 topology rescue.
2. Do not continue tuning soft S₂/φ or topology proxy weights for B1.1.
3. Do not relax S₂/Euler/maxCC gates after seeing results.
4. Do not treat qmatch as an implicit hidden step; it must be documented and versioned.
5. Do not start substantive B2 training without the calibrated/qmatch pipeline.

## Data and artifact policy

The repository intentionally avoids committing large or sensitive scientific artifacts:

- ignored: model weights (`*.pt`, `*.pth`, `*.ckpt`)
- ignored: dense arrays (`*.npy`, `*.npz`)
- ignored: medical/volume formats (`*.nii`, `*.nii.gz`, large TIFFs)
- tracked: lightweight JSON/MD/CSV summaries, hashes, selected plots, logs, and decision notes

Remote/Linux paths in notes are provenance references, not guaranteed portable data locations. Reproduction requires access to the HY7 local/remote data workspace described in the notes.

## Quick verification

The current lightweight test suite can be run with:

```bash
python3 -m pytest tests -q
```

At the latest local verification (2026-07-12) this returned:

```text
84 passed in 1.46s
```

For guard-triggered changes, additional focused ad-hoc verification scripts were created under the macOS temp directory with the `hermes-verify-` prefix and then cleaned up. Those ad-hoc checks should not be described as canonical suite green.

## Core workflow summary

1. Build/inspect HY7 phase-2 gray/sus slices.
2. Train/evaluate B1 gray/sus DDPM candidates.
3. Use formal proxy gates: S₂, Euler, maxCC, and φ.
4. Close failed branches explicitly, e.g. soft-pore line failed and was frozen.
5. Run one registered Euler/maxCC rescue when topology is the bottleneck.
6. Validate at n=512 and run nnUNet / disagreement review.
7. Use rock multi-expert review for major gates.
8. Freeze B1.1 conditionally and move only to calibrated B2-min.

## GitHub sync note

This GitHub repository is a research-code and evidence-log mirror. It is not a complete standalone data release. Large upstream data, model weights, and generated arrays are intentionally excluded; use the notes and hashes to locate or reproduce them in the HY7 working environment.
