# Revision supplementary figure data

`supplementary_experiment_results.csv` is a compact wide-format table for the
2026-09-22 revision supplementary experiment suite. Each row represents one
experiment setting, cohort, seed, aggregation, condition or paired comparison.
It does not include source images, model checkpoints, local paths or
per-sample predictions.

## Record groups

| `section` | Contents |
|---|---|
| `E14_E20_E27_C4` | Independent-warm, gate, dual-view, matched Raw B0, main metrics and paired bootstrap results. |
| `C13_refresh` | Five-fold Industrial-1395 target-supervised OOF results. |
| `A_expert_A_moment` | Routing diagnostics and moment-consistency values. |
| `A_moment` | Complete native-ROI timing and executed-parameter values. |
| `A_Fig3` | Six-condition, factorial and perspective-scan results for Figure 3. |

## Columns

- `source_table` identifies the aggregate source table used to create the row.
- `experiment_id`, `result_type`, `cohort`, `method`, `candidate`, `reference`,
  `seed`, `aggregation`, `scope`, `condition`, and `angle_degrees` identify the
  experimental comparison.
- NMAE, RMSE, accuracy, coverage, routing, efficiency and paired-comparison
  values are stored in their corresponding named columns.
- `images`, `rows`, `groups`, `source_seeds`, and `ensemble_members` describe
  the included evaluation population.

Metric fields ending in `_pct_fs` are percentage points of full scale. Metric
fields ending in `_pct` are percentages. Bootstrap intervals are pointwise 95%
intervals conditional on fitted models and use the documented whole-group
resampling scheme. Industrial OOF records use target supervision and are stored
separately from frozen-transfer records.
