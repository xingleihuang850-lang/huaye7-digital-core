# External GJ5-15 links

This folder stores moved symlinks that point to the external GJ5-15 disk data. They are kept here for provenance only and are not part of the HY7 mainline workspace.

Moved on: 2026-07-06

Links:

- `GJ5-15data` -> `/Volumes/Untitled/GJ5-15data`
- `nnunet_pipeline` -> `/Volumes/Untitled/GJ5-15data/nnunet_pipeline`

Safety note:

Moving these entries only moved the symlink files inside this repository. It did not delete or modify the real external data under `/Volumes/Untitled/`.

Current HY7 mainline work should use HY7 paths under `data/`, `experiments/花页7_PlanB_记录/`, and the remote `/home/user/HXL/HY7_planb/phase2` workspace unless a note explicitly says GJ5-15 is needed as external transfer validation.
