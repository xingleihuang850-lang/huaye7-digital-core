# Mirrored remote B2-min evidence — 2026-07-06

This directory mirrors the small B2-min JSON/MD/hash evidence from the remote ordered view so local audits do not require SSH for every check.

Source ordered view:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/00_ORDERED_VIEW/05_b2_min_calibrated
```

Mirrored files:

```text
baseline_package_ep015/b2_min_manifest.json
baseline_package_ep015/b2_min_readme.md
baseline_package_ep015/hashes.txt
constrained_selection_smoke_ep015/selection_summary.json
constrained_selection_smoke_ep015/selection_summary.md
constrained_selection_smoke_ep015/qmatch_manifest.json
```

SHA256 after mirroring:

```text
27c2cf40476f78e69480ba364011bb86a394a01d99750c8cc3037ec4d04439df  baseline_package_ep015/b2_min_manifest.json
6458295a689dbcfc193a3f1774d690ccc6aba0840bee3a232527beb785bff7ae  baseline_package_ep015/b2_min_readme.md
658f3ff9f392c609b04b88f53479524a31709d79d14c5591961f624b9921634c  baseline_package_ep015/hashes.txt
dc6303f99902e9717f086718397afc4d96e3e495ac8f7f549dabfa617fb071e7  constrained_selection_smoke_ep015/qmatch_manifest.json
40f51bdc04da5c5a373a948f5a874cdda134447f88a257392b0ac8bc96eebae4  constrained_selection_smoke_ep015/selection_summary.json
839851afbc29f2dab8b523f784b89aad9e7e753ad9b054ff9c3e52825d0e764f  constrained_selection_smoke_ep015/selection_summary.md
```

These are lightweight evidence records only. Large arrays, samples, and checkpoints remain remote / ignored and must be referenced by path + hash/manifest, not committed here.
