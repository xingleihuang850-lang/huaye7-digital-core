# HY7 Report Provenance Contract

Status: `DRAFT_NOT_ACTIVE`. This contract does not authorize report generation or change existing report wording.

## Required Input Manifest

Every Word, PPT, or Excel run must declare a JSON manifest before rendering:

- generator script path and committed SHA;
- `experiments/hy7_stats.json` path and SHA256;
- every evidence/figure path, SHA256, and evidence grade (`XLSX_DIRECT`, `XLSX_RECOMPUTED`, `REPORT_DIRECT`, `INTERPRETIVE`, or `diagnostic`);
- report `as_of` date and execution timestamp;
- output paths and overwrite policy; and
- allowed conclusion identifiers for the report edition.

## Wording Rules

- `INTERPRETIVE`, diagnostic, smoke, toy, conditional pass, same-volume internal validation, and same-image unbuffered holdout must remain explicitly labelled.
- A generator may not turn a missing evidence grade into a pass claim, independent validation, external generalization, permeability, or digital-well conclusion.
- E0-E3 must be worded as same-volume internal validation; S3 must be worded as same-image unbuffered holdout unless future spatial reruns provide a completed manifest.
- B1.1 must retain `conditional pass`, mandatory qmatch, and ORIG raw `known_fail`.

## Required Output Manifest

After rendering, write a lightweight manifest beside the output with input-manifest SHA, output SHA256, command, environment, timestamp, generator SHA, warnings, and the exact conclusion identifiers rendered. Never infer an output manifest from file names or static dates.

## Activation Gate

This draft becomes active only after the research lead approves the conclusion vocabulary and each generator is changed to consume the manifest. Until then, do not bulk-update dates or regenerate historical Office/PPT deliverables.
