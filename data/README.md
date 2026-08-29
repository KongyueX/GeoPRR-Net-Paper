# Public result data

This directory contains the public, machine-readable result tables underlying
the current GeoPRR-Net manuscript. Values are normalized to full scale in
`[0, 1]`; multiply errors by 100 to obtain `%FS`.

The release contains predictions and training/evaluation metrics only. It does
not redistribute source images, model checkpoints, third-party weights, local
paths, runtime logs, or restricted Industrial-1395 per-sample records.

## Inventory

| File | Rows | Contents |
|---|---:|---|
| `syncg/geoprr_predictions.csv.gz` | 168,264 | Three-seed predictions for the five reported EMA variants plus the three full-model terminal-router stability runs; each run has 1,558 images × 6 conditions = 9,348 rows. |
| `syncg/external_cnn_predictions.csv.gz` | 168,264 | Matched Raw and SARN-v2 SyncG predictions from ResNet-18, EfficientNet-B0, and MobileNetV3-Large, each with three seeds. The `preprocessing` field distinguishes the two arms. |
| `syncg/external_cnn_audit.json` | — | Independent 18-ledger validation and aggregate metrics for the corrected CNN release. |
| `syncg/routing_diagnostics_seed_20262020.csv.gz` | 9,348 | Prespecified-seed candidate predictions, adaptive weights, predicted gains, and polar diagnostics. |
| `syncg/vdn_matched_predictions.csv.gz` | 28,044 | Three independently trained terminal VDN direction checkpoints on the same full SyncG roster. The progress conversion is annotation-assisted and is not a deployable end-to-end VDN result. |
| `rf100/predictions.csv.gz` | 13,590 | Public RF100-VL transfer predictions for GeoPRR-Net, its raw/normalized endpoints, and Raw/SARN-v2 EfficientNet-B0 controls. |
| `industrial1395/group_metrics.csv.gz` | 6,240 | Group-level metrics for 52 anonymized groups, five GeoPRR/control outputs, three seeds, and eight condition scopes. |
| `industrial1395/dataset_metrics.csv` | 360 | Full-denominator and group-macro metrics for the three Industrial-1395 subsets. |
| `industrial1395/group_metrics_audit.json` | — | Denominator, group-macro, anonymization, and test-only evaluation checks. |
| `training/geoprr_training_history.csv.gz` | 651 | Shared polar and variant-specific router optimization histories for the three GeoPRR-Net seeds. |
| `training/vdn_training_history.csv.gz` | 600 | The complete 200-epoch history for each of the three matched VDN checkpoints. |
| `public_results_summary.json` | — | Current SyncG, RF100-VL, VDN, efficiency, and Industrial-1395 aggregate statistics. Industrial data are aggregates only. |
| `inventory.json` | — | Row counts, file sizes, cohort dimensions, and explicit exclusions for this release. |

## Core schemas

The main GeoPRR-Net SyncG table uses one row per
`(seed, variant, image_id, condition)` and includes the normalized target,
prediction, absolute error, endpoint predictions, relation availability, and
explicit `geometry_on` / `adaptive_routing_on` indicators. The terminal-router
stability rows are distinguished by `weight_variant`.

The external CNN table uses explicit `model`, `source_model_name`,
`preprocessing`, `source_method`, and `source_protocol` fields. The initial
84,132-row release contained valid SARN-v2 predictions but described them as
Raw; the corrected table preserves those rows and adds the 84,132 authoritative
Raw rows. The external CNN and VDN tables use the same sample-condition roster.
VDN failures, if any, remain in the denominator with an absolute error of
`1.0`; the current released ledgers are otherwise preserved without high-error
sample filtering.

RF100-VL targets are annotation-derived normalized progress values. The release
is an external transfer evaluation, not an official scalar-reading leaderboard.

Industrial-1395 contains 1,395 restricted images in three subsets and 52
source/capture-session groups. Raw images, original group names, and per-sample
records are not redistributed. Stable `group_001 ... group_N` aliases preserve
the group-level analysis without exposing the source identifiers.

## Reading compressed tables

Python's standard library, pandas, R, and common archive tools read these files
directly. For example:

```python
import pandas as pd

syncg = pd.read_csv("data/syncg/geoprr_predictions.csv.gz")
print(syncg.groupby(["variant", "seed"])["absolute_error"].mean())
```

The compact CSV files in `../figures/` remain the exact plotting inputs used by
the manuscript figures and tables.
