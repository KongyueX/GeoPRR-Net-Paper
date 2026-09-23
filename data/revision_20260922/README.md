# Revision supplementary figure data

`supplementary_experiment_figure_data.csv` is a compact long-format table for
the 2026-09-22 revision supplementary experiment suite. It contains aggregate
records only; it does not include source images, model checkpoints, local paths
or per-sample predictions.

## Record groups

| `section` | Contents |
|---|---|
| `main_results` | Three-seed per-cohort metrics and seed-mean/sample-SD summaries. |
| `paired_effect` | Whole-group paired bootstrap estimates and pointwise 95% intervals. |
| `routing_diagnostic` | Candidate-weight, routing-entropy and moment-residual summaries. |
| `industrial_target_supervised_oof` | Five-fold Industrial-1395 target-supervised OOF aggregate metrics. |
| `efficiency` | Complete native-ROI batch-1 timing and executed-parameter summaries. |
| `figure3_condition_curve` | Six-condition Geometry × Routing summaries. |
| `figure3_factorial_interaction` | Difference-in-differences statistics for the four Geometry × Routing cells. |
| `figure3_perspective_curve` | Metrics for 0°, 15°, 25°, 35°, 45° and 60° perspective scans. |
| `figure3_perspective_paired` | Paired perspective-scan comparison statistics. |

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
