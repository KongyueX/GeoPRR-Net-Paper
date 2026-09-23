# Revision supplementary figure data

`figure_plot_data.csv` is a compact long-format table for the 2026-09-22
revision supplementary experiment suite. It contains the values used for
manuscript tables and plots. It does not include source images, model
checkpoints, local paths or per-sample predictions.

## Record groups

| `section` | Contents |
|---|---|
| `table_main` | Three-seed frozen-transfer metrics for the main comparison table. |
| `table_paired` | All-condition whole-group paired bootstrap estimates and pointwise intervals. |
| `figure_ablation` | SyncG component-ablation values. |
| `figure3` | Six-condition, factorial and perspective-scan values for Figure 3. |
| `figure_routing` | Candidate-weight, routing-entropy and moment-residual values. |
| `table_industrial_oof` | Five-fold Industrial-1395 target-supervised OOF aggregate metrics. |
| `table_efficiency` | Complete native-ROI batch-1 timing and executed-parameter values. |

## Columns

- `source_table` identifies the aggregate source table used to create the row.
- `cohort`, `method`, `candidate`, `reference`, `seed`, `aggregation`, `scope`,
  `condition`, and `angle_degrees` identify the experimental comparison.
- `metric`, `statistic`, and `value` hold the reported measurement.
- `sample_sd`, `ci95_low`, and `ci95_high` are present when the source table
  supplies a seed sample standard deviation or a paired bootstrap interval.
- `images`, `rows`, `groups`, `source_seeds`, and `ensemble_members` describe
  the included evaluation population.

Metric fields ending in `_pct_fs` are percentage points of full scale. Metric
fields ending in `_pct` are percentages. Bootstrap intervals are pointwise 95%
intervals conditional on fitted models and use the documented whole-group
resampling scheme. Industrial OOF records use target supervision and are stored
separately from frozen-transfer records.
