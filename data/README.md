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
| `figure3/geometry_routing_per_sample.csv.gz` | 112,176 | Complete four-cell Geometry × Routing factorial: four cells × three seeds × 1,558 images × six conditions. |
| `figure3/geometry_routing_seed_metrics.csv` | 12 | Per-cell, per-seed pooled NMAE and Acc@2%. |
| `figure3/geometry_routing_summary.csv` | 4 | Four-cell pooled metrics and seed mean ± sample SD. |
| `figure3/geometry_routing_conditions.csv` | 24 | Six-condition NMAE and Acc@2% summaries for all four factorial cells. |
| `figure3/geometry_routing_interaction.json` | — | Difference-in-differences interaction with a 20,000-resample, 14-scene cluster-bootstrap 95% CI. |
| `figure3/perspective_scan_per_sample.csv.gz` | 84,132 | Three models × three seeds × six angles × 1,558 images, with availability, fallback, and valid-support fields; no high-angle row is filtered. |
| `figure3/perspective_scan_seed_metrics.csv` | 54 | Per-model, per-angle, per-seed NMAE, Acc@2%, and P95 absolute error. |
| `figure3/perspective_scan_summary.csv` | 18 | Angle-wise seed summaries plus support-normalization availability and identity-fallback rates. |
| `figure3/perspective_full_vs_raw.csv` | 6 | Paired Full GeoPRR minus Raw EfficientNet-B0 differences with 20,000-resample scene-bootstrap intervals. |
| `figure3/perspective_scan_audit.json` | — | Standalone Raw EfficientNet-B0 checkpoint provenance, FP32 external-ledger cross-check, Cartesian-roster checks, fallback counts, hashes, and deterministic summary reproduction. |
| `figure3/figure3_experiment_summary.json` | — | Consolidated machine-readable statistics and the checkpoint/intervention audit. |
| `rf100/predictions.csv.gz` | 24,462 | Public RF100-VL transfer predictions for GeoPRR-Net, its raw/normalized endpoints, and Raw/SARN-v2 ResNet-18, EfficientNet-B0, and MobileNetV3-Large controls. |
| `rf100/predictions_audit.json` | — | Cartesian-roster, prior-EfficientNet reproduction, and aggregate-metric checks for all nine released RF100-VL method arms. |
| `industrial1395/group_metrics.csv.gz` | 11,232 | Group-level metrics for 52 globally anonymized acquisition clusters within one unified Industrial-1395 cohort, nine GeoPRR/CNN outputs, three seeds, and eight condition scopes. |
| `industrial1395/cohort_metrics.csv` | 216 | Full-denominator and group-macro metrics for the complete 1,395-image cohort; Raw and SARN-v2 ResNet-18, EfficientNet-B0, and MobileNetV3-Large are included, and no source-partition rows are reported. |
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

The Figure 3 factorial table uses one row per
`(seed, variant, image_id, condition)` and explicitly records `geometry_on` and
`adaptive_routing_on`. The missing geometry-off/fixed-routing cell is an
inference-only intervention on the existing fixed-routing checkpoints; the
machine-readable audit confirms that no joint-specific trained parameters or
router execution are involved. The perspective table uses one row per
`(model, seed, image_id, angle)`. All methods and seeds receive identical
deterministic pixels, including exact reproduction of the formal 25° and 45°
transforms. All three models use FP32 inference. Raw EfficientNet-B0 is loaded
standalone from the three scene-disjoint baseline checkpoints rather than read
from a GeoPRR output; the accompanying audit verifies its 0° predictions
against the separately released Raw EfficientNet-B0 clean ledger. The 60°
identity-fallback rows remain in the denominator.
`valid_support_fraction` records the geometric fraction of the warped source
plane remaining inside the canvas, not the all-ones effective mask supplied to
the model after identity fallback.

RF100-VL targets are annotation-derived normalized progress values. Its CNN
rows use the same explicit Raw/SARN-v2 distinction as the SyncG release. The
release is an external transfer evaluation, not an official scalar-reading
leaderboard.

Industrial-1395 contains 1,395 restricted images and 52 acquisition clusters.
Every published statistic pools the complete cohort; source-partition labels
and subset-specific results are not released. Raw images, original group names,
and per-sample records are not redistributed. One global
`group_001 ... group_052` alias roster preserves the cluster analysis without
exposing source identifiers.

## Reading compressed tables

Python's standard library, pandas, R, and common archive tools read these files
directly. For example:

```python
import pandas as pd

syncg = pd.read_csv("data/syncg/geoprr_predictions.csv.gz")
print(syncg.groupby(["variant", "seed"])["absolute_error"].mean())
```

The compact CSV files in `../figures/` and `figure3/` are the exact plotting
inputs used by the repository figures and tables.
