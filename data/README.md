# Public result data

This directory contains the public, machine-readable result tables underlying
the current GeoPRR-Net manuscript. Values are normalized to full scale in
`[0, 1]`; multiply errors by 100 to obtain `%FS`. The new
`roi_comparison_zero_shot*` files and the `*_pct` / `*_pct_fs` fields in
`official_syncg_fulltrain_20260908/` and `geoprr_shared_full_20260911/` explicitly use percentage units; do not
multiply those values by 100 again.

The release contains predictions and training/evaluation metrics only,
including an anonymized Industrial-1395 adapted-OOF prediction ledger. It does
not redistribute source images, model checkpoints, third-party weights, local
paths, runtime logs, or non-public Industrial-1395 source records.

## Shared full-source GeoPRR: 2026-09-11

[geoprr_shared_full_20260911](geoprr_shared_full_20260911/README.md) contains
three completed seeds (20262020, 20262021, 20262022) with a same-seed full-16k
RawEff foundation and full-16k downstream training. Its 16 files include
99,828 per-sample predictions, 8,352 group-metric rows, 4,176 group differences,
1,005 training-epoch rows, mean/sample-SD tables and paired group intervals.

The shared reader's six-condition NMAE is 0.741 ± 0.022%FS on SyncG,
3.205 ± 0.254%FS on RF100-VL and 11.624 ± 1.603%FS on Industrial-1395.
Original GeoPRR and RawEff references come from the official full-training
package below. Sample/group aliases were verified to match that package.

The files match the [code-repository release](https://github.com/KongyueX/GeoPRR-Net/tree/3fa8c7deae182f491d97e7a64389db45d240159e/docs/data/geoprr_shared_full_20260911).
This is a separate training protocol; the manuscript and existing figure
builders have not been switched to this dataset package.

## Official full-training results

[official_syncg_fulltrain_20260908](official_syncg_fulltrain_20260908/README.md)
contains the complete official 16,000-image source-training / 4,000-image
source-test results. The package records 21 source model-seed combinations
and 65 optimization stages. Its 44 files cover main comparisons, SARN and
annotation diagnostics, ablations, sensitivity, angle scans, OOF adaptation,
ensembles, training costs and full-path efficiency.

The [detailed tables](official_syncg_fulltrain_20260908/details/README.md)
include 2,762,352 per-sample prediction rows, 215,424 group-metric rows and
39,558 group-comparison rows. The manifest identifies repeated fold-alignment
and default-sensitivity outputs. Industrial sample identities and all group
identities use consistent aliases within this release.

The files match the [code-repository publication](https://github.com/KongyueX/GeoPRR-Net/tree/c8d249ba78aeb8f7c3f07dca32e3a5a90207687d/docs/data/official_syncg_fulltrain_20260908).
See `protocol.json` for dataset roles and metric units and `manifest.json`
for the included tables. Earlier files listed below belong to older experiment
versions; the existing manuscript and figure builders have not been switched
to this full-training package.

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
| `industrial1395/supervised_feature_head_ensemble_per_sample.json` | 8,370 | Per-row predictions and aggregate metrics for supervised five-fold target-domain OOF GeoPRR-Net feature-head adaptation and equal-weight three-encoder aggregation. |
| `training/geoprr_training_history.csv.gz` | 651 | Shared polar and variant-specific router optimization histories for the three GeoPRR-Net seeds. |
| `training/vdn_training_history.csv.gz` | 600 | The complete 200-epoch history for each of the three matched VDN checkpoints. |
| `roi_geometry_comparison_three_seed.csv` | 12 | Complete three-domain by four-method ROI-level comparison for GeoPRR-Net, VDN, DeepLabV3+-ROI, and YOLO11s-Pose-4KP, including clean/pooled NMAE, Acc@5%, coverage, and paired cluster-bootstrap intervals where released. The Industrial-1395 GeoPRR-Net row uses the five-fold OOF aggregate. |
| `public_results_summary.json` | — | Current SyncG, RF100-VL, VDN, efficiency, and Industrial-1395 aggregate statistics. Industrial data are aggregates only. |
| `inventory.json` | — | Row counts, file sizes, cohort dimensions, and explicit exclusions for this release. |

## Source-reference update: 2026-09-07

| File | Rows | Contents |
|---|---:|---|
| `roi_comparison_zero_shot.csv` | 12 | Three readers on Industrial-1395 and RF100-VL, clean and six-condition scopes; per-seed NMAE, Acc@2, Acc@5, coverage, and mean/sample SD in percentage units. |
| `roi_comparison_zero_shot_public.json` | — | Aggregate source-only transfer results, reference-model provenance, cohort sizes, and per-seed statistics. |
| `roi_comparison_efficiency.csv` | 5 | Matched FP32 batch-1 native-component and complete ROI-reader parameter, operation, latency, throughput, and memory measurements. |
| `roi_comparison_efficiency_public.json` | — | Hardware, input/measurement scope, observed FP32 precision, and aggregate timing/failure evidence for all five arms. |

Industrial DeepLab and VDN now use same-seed YOLO11s-Pose-4KP models trained
on SyncG to provide pivot/start/end. The predicted pointer tip is excluded
from reference selection, confidence checks, and decoding. The previous
detector's training roster could not be established; its predictions have
been replaced by a fresh three-seed evaluation. Six-condition NMAE is now
32.9356 ± 4.0842%FS for DeepLab and 25.3840 ± 6.7070%FS for VDN. YOLO remains
31.0045 ± 7.6146%FS. RF100 DeepLab/VDN remain annotation-assisted components.

The existing Industrial GeoPRR entry uses supervised target-domain OOF
adaptation, whereas these comparators are source-only readers within supplied
ROIs. `evaluation_setting` makes this distinction explicit in the 12-row
comparison table. Its Industrial delta column is a descriptive point
difference against that OOF aggregate; confidence intervals remain unreported.
The frozen source-only GeoPRR result of 12.3664%FS is a different setting.

For the Industrial GeoPRR OOF row, `seeds` identifies the three source encoders,
not three independently evaluated ensembles. Seed SD is not applicable to this
single ensemble and is empty in the comparison CSV and `null` in the summary
JSON. Its single-value `per_seed` lists retain the ensemble result for compatibility;
they do not represent an estimate of variation across seeds. Plotting uses zero
only to omit its error bar.

Efficiency uses RTX 4060 / PyTorch 2.11 / CUDA 12.8, FP32, batch 1, seed
20262020, 20 warmups and 100 timed clean ROIs. Complete reader arms include
reference detection, preprocessing, transfers, decoding and synchronization.
DeepLab probability-map and VDN direction-only arms are explicitly identified
as native components. FPS is inverse mean latency; failures remain timed.
Supported neural GFLOPs omit preprocessing, NMS, CPU geometry and unsupported
operators. Accuracy evaluation uses the existing CUDA autocast configuration.

The new public JSON/CSV files contain cohort/seed aggregates, without source
images, weights, local absolute paths, or per-image Industrial readings.
Reproduction code and the full explanation are in the
[code repository report](https://github.com/KongyueX/GeoPRR-Net/blob/main/docs/ROI_GEOMETRY_COMPARISON_CN.md).

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
and subset-specific results are not reported. Raw images and unredacted source
records are not redistributed. The public OOF ledger contains pseudonymous
sample identifiers, while the group summary uses one global
`group_001 ... group_052` alias roster for cluster analysis.

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
