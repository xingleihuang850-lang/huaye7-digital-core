# B1 gray sus probe evidence

Read-only probe of ct28 same-grid `sus` grayscale distribution for B1 gray-medium generation design. No training was run.

Remote output directory:

```text
hy7-linux:/home/user/HXL/HY7_planb/phase2/b1_gray_sus_probe_20260703/
```

Local files:

```text
ct28_sus_gray_distribution_summary.json
ct28_sus_gray_distribution_report.md
```

sha256:

```text
4f84f6ddd965d9a51abf690a413537cfbb054db5b7f1766b13609d4df6af6173  ct28_sus_gray_distribution_summary.json
df6288da58d99af9a848921d87fee1af8320f1966159c2c3a969f1935e30a75d  ct28_sus_gray_distribution_report.md
```

Key findings:

- Valid mask rule: `(sus != 0) OR (pore == pore_val)`; pore overrides outside-air zeros.
- Decoded `pore_val=0`.
- Volume: 1500×1500×1500 uint8.
- Valid voxels: 2,615,526,000 / 3,375,000,000 = 77.497067%.
- Pore fraction of valid voxels: 7.181879%.
- Valid gray percentiles: p1=45, p50=115, p99=205; p0.5=35, p99.5=233.
- M7 tile-compatible probe (`tile=128`, `z_step=6`, `axes=z`, `min_valid=0.999`) reproduces 20,750 tiles: 16,600 train / 4,150 test.
- Recommended first normalization candidate: valid-mask percentile clip p1–p99 `[45,205]` then linear map to `[-1,1]`; p0.5–p99.5 `[35,233]` is a wider backup.
