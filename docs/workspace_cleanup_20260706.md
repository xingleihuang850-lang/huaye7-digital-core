# Workspace cleanup and remote ordered view — 2026-07-06

## Local cleanup

Workspace root:

`/Users/hxl/Documents/Hermes工作区/01_Claude接管剩余工作/claude`

Actions performed:

1. Moved root-level GJ5-15 external symlinks out of the active HY7 root:
   - `GJ5-15data` -> `archive_external_links/GJ5-15/GJ5-15data`
   - `nnunet_pipeline` -> `archive_external_links/GJ5-15/nnunet_pipeline`
2. Moved the empty root-level vectorstore directory:
   - `vectorstore/` -> `_archive/local_cleanup_20260706/vectorstore/`
3. Added local README files explaining both moves.
4. Added `.gitignore` rules so absolute external-data symlinks under `archive_external_links/GJ5-15/` are not committed.

Safety checks:

- The moved GJ5-15 entries are symlinks only.
- Their targets remain under `/Volumes/Untitled/GJ5-15data`.
- No real external GJ5-15 data was deleted or modified.
- `vectorstore/` was empty at move time.

## Remote ordered view

Remote phase2 root:

`/home/user/HXL/HY7_planb/phase2`

Created:

`/home/user/HXL/HY7_planb/phase2/00_ORDERED_VIEW`

This is a symlink-only ordered index. Original remote experiment folders/files were not moved or deleted, so existing scripts, notes, and paths continue to work.

Ordered reading groups:

1. `00_inputs/` — CT28/HY7 slice inputs.
2. `01_m7_baseline/` — earlier M7/phase2 baseline and 200ep evidence.
3. `02_b1_gray_sus_inputs_controls/` — B1 gray/sus probes, controls, diagnostics.
4. `03_b11_failed_or_superseded/` — periodic/soft-pore/output-calibration branches that are closed or superseded.
5. `04_b11_rescue20_conditional_pass/` — current B1.1 conditional-pass evidence.
6. `05_b2_min_calibrated/` — calibrated B2-min package and constrained selection smoke.
7. `90_code_and_run_scripts/` — active code and run scripts.
8. `99_root_cache_and_legacy/` — cache/smoke leftovers kept visible but not mainline.

Remote verification:

```text
00_ORDERED_VIEW/README.md: OK
00_ORDERED_VIEW/ORDERED_LINKS.txt: OK
link count: 42
```

Current mainline remains:

- B1.1 = conditional pass, not unconditional full pass.
- Main candidate = ep015.
- Required preprocessing = `hy7-gray-calibration-qmatch-v1`.
- ORIG raw nnUNet remains known fail.
- No second B1.1 topology rescue; no gate relaxation.
