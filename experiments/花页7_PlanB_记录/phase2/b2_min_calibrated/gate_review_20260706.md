# HY7 B2-min gate review — 2026-07-06

## Workflow node

- Node: `HY7-B2-min-gate-review`
- Trigger: continue from remote `00_ORDERED_VIEW` and B2-min gate review.
- Local git HEAD checked: `dd6cae0 docs: document workspace cleanup and remote ordered view`.
- Scope: read-only review of remote ordered view, B2-min baseline package, constrained selection smoke, and local lightweight tests.
- No new training launched.

## Remote ordered view check

Remote root:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/00_ORDERED_VIEW
```

Checks run by SSH from local Hermes session:

```text
ORDERED_VIEW_DIR_OK
README_OK
ORDERED_LINKS_OK
LINK_COUNT 42
BROKEN_COUNT 0
```

Current ordered B2-min links:

```text
00_ORDERED_VIEW/05_b2_min_calibrated/00_baseline_package_ep015 -> ../../b2_min_calibrated_baseline_ep015_20260706
00_ORDERED_VIEW/05_b2_min_calibrated/01_constrained_selection_smoke_ep015 -> ../../b2_min_constrained_selection_smoke_ep015_20260706
00_ORDERED_VIEW/90_code_and_run_scripts/hy7_b2_min_package.py -> ../../hy7_b2_min_package.py
00_ORDERED_VIEW/90_code_and_run_scripts/hy7_b2_min_select.py -> ../../hy7_b2_min_select.py
```

Interpretation: remote ordered view is valid and can be used as the phase-2 reading/index layer. The B2-min evidence is reachable via the ordered links, not by the raw directory names under `05_b2_min_calibrated/`.

## Baseline package review

Ordered path:

```text
00_ORDERED_VIEW/05_b2_min_calibrated/00_baseline_package_ep015
```

Required files present:

```text
b2_min_manifest.json
b2_min_readme.md
hashes.txt
```

Actual hashes from remote ordered path:

```text
27c2cf40476f78e69480ba364011bb86a394a01d99750c8cc3037ec4d04439df  b2_min_manifest.json
6458295a689dbcfc193a3f1774d690ccc6aba0840bee3a232527beb785bff7ae  b2_min_readme.md
658f3ff9f392c609b04b88f53479524a31709d79d14c5591961f624b9921634c  hashes.txt
```

Manifest gate fields:

```text
status=calibrated_b2_min_candidate
main_checkpoint=ep015
calibration_version=hy7-gray-calibration-qmatch-v1
orig_raw_status=known_fail
allowed_next_step=calibrated_b2_min_baseline_or_constrained_selection
```

Forbidden constraints preserved:

```text
unconditional_b1_1_pass_claim
orig_raw_pass_claim
second_b1_1_topology_rescue
gate_relaxation
implicit_qmatch
```

Evidence summary:

```text
formal512 ep015@phi6.4:
  S2 rmse=0.00034034164909631633
  Euler=120.810546875
  maxCC=0.06408827658203413
  passed_gate=True

nnUNet ep015_qmatch:
  phi=5.794930458068848
  S2 rmse=0.0017214588891168259
  Euler=116.154296875
  maxCC=0.06510709034871634
  reverse_fail=False

qmatch split generalization:
  even_pass=True, even_euler=116.13671875
  odd_pass=True, odd_euler=116.16796875
```

Interpretation: baseline package passes the reproducibility/entry gate for calibrated B2-min. It does not authorize ORIG raw pass claims or uncalibrated downstream use.

## Constrained selection smoke review

Ordered path:

```text
00_ORDERED_VIEW/05_b2_min_calibrated/01_constrained_selection_smoke_ep015
```

Required files present:

```text
selection_summary.json
selection_summary.md
qmatch_manifest.json
```

Actual hashes from remote ordered path:

```text
40f51bdc04da5c5a373a948f5a874cdda134447f88a257392b0ac8bc96eebae4  selection_summary.json
839851afbc29f2dab8b523f784b89aad9e7e753ad9b054ff9c3e52825d0e764f  selection_summary.md
dc6303f99902e9717f086718397afc4d96e3e495ac8f7f549dabfa617fb071e7  qmatch_manifest.json
```

Selection status:

```text
status=calibrated_constrained_selection_smoke
calibration_version=hy7-gray-calibration-qmatch-v1
selection_method=pass_gate_then_min_s2_then_abs_euler_minus_120_then_maxcc_then_abs_phi_minus_6p4
rows=9
pass_rows=8
```

Selected row:

```text
variant=ep015_chunk384_447
n=64
phi=6.462860107421875
S2 rmse=0.0002106706336130071
Euler=121.171875
maxCC=0.06431804952279352
pass_gate=True
selection_reason=passed_gate_min_score
```

Full-batch control row:

```text
variant=ep015_all
n=512
phi=6.442654132843018
S2 rmse=0.0002854642510439182
Euler=121.26953125
maxCC=0.06397858477862998
pass_gate=True
```

Forbidden constraints preserved:

```text
no_retraining
no_second_b1_1_topology_rescue
no_gate_relaxation
orig_raw_pass_claim
explicit_qmatch_required
```

Interpretation: constrained selection smoke is internally consistent and does not break the full-batch evidence. The selected chunk may be used for B2-min candidate triage only; the full-batch row remains the stronger gate evidence for stage decisions.

## Local code/test check

Local command:

```bash
cd '/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude' && python3 -m pytest tests -q
```

Result:

```text
31 passed in 0.12s
```

Local git working tree after review:

```text
## main
```

## Gate conclusion

B2-min gate review result: `PASS_WITH_CONSTRAINTS`.

Allowed next step:

- Proceed to a formal B2-min design review / rock gate using the baseline package plus constrained selection smoke as evidence.
- If approved, design the next B2 component around the calibrated/qmatch pipeline and keep it no-retraining unless a new gate explicitly authorizes training.

Still forbidden:

- Do not claim B1.1 unconditional full pass.
- Do not claim ORIG raw nnUNet passed.
- Do not hide qmatch as an implicit step.
- Do not run a second B1.1 topology rescue.
- Do not relax gates after seeing B2-min outputs.
- Do not treat the 64-slice selected chunk as a substitute for full-batch formal/nnUNet review.
