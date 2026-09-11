# Cross-version figure and table inputs

This directory supplies cross-training-configuration comparisons for Table/Figure 6 (updated Industrial baseline versus retained adapted outputs) and Table/Figure 7 (retained ablation variants versus the updated full reader). The compared predictions originate from the two published experiment packages described below.

## Model sources

The new `main/geoprr` observations come from `../geoprr_shared_full_20260911`, via the checked `../figure_inputs_shared_full_20260911` source-only view. Its Industrial observations also replace the compatibility alias `frozen_fold_aligned/geoprr`. All other source readers, all target-adapted outputs, all ablation variants, and all adapted ensembles remain from `../official_syncg_fulltrain_20260908`.

The updated three-member frozen GeoPRR ensemble is reconstructed from the three new normalized predictions for each identical sample/condition row. Predictions are averaged first, then compared with the target. No error averaging is used for ensemble scoring. All 8,370 ensemble rows have valid members. `details/per_sample/industrial_ensemble_frozen_fold_aligned.csv.gz` contains this updated GeoPRR ensemble alongside the three unchanged CNN ensembles. `industrial_frozen_fold_aligned.csv.gz` preserves the original outer-fold labels while updating only the GeoPRR frozen predictions.

## Compatibility tables and intervals

`seed_mean_sample_sd.csv`, `per_seed_metrics.csv`, and `ensemble_metrics.csv` retain their original schemas. Only the intended frozen/full GeoPRR baseline systems are updated; adapted and ablation variant values are unchanged.

`paired_comparisons.csv` is scoped exclusively to the 25 recomputed cross-version comparisons used for Tables/Figures 6 and 7: 21 old-variant-minus-new-full SyncG ablation contrasts (three variants over all_conditions and the six individual conditions), and four old-adapted-minus-new-frozen Industrial contrasts (per-source-seed and ensemble, each for all_conditions and clean). Every candidate system is from `official_syncg_fulltrain_20260908`; every reference full/frozen system is from `geoprr_shared_full_20260911`, including the newly derived frozen ensemble. No source-only baseline comparisons, old matched adapted-CNN comparisons, or untouched historical comparison scopes are included in this paired table. The complete original paired tables remain in their source packages. This derived view is exclusively for Figures/Tables 6 and 7, not the main seven-reader comparison or the alpha-sensitivity analysis.

The `derived/` files record the 21 ablation intervals and the single four-cell contrast. They use the existing `figures/derive_condition_summaries.py::paired_group_bootstrap_fast`, 145 source groups, 20,000 resamples, and seed 20260907. Only the full-model cell is new in the factorial; the other three cells use the original training protocol. This arithmetic contrast cannot be interpreted as isolated component causality or strengthened geometry-routing synergy.

The four adaptation intervals use the same helper, 52 acquisition groups, 20,000 resamples, and seed 20261107. For the single-model aggregate, errors are averaged across source seeds within each original row before group resampling. For an ensemble, one scored ensemble prediction is used per row. Groups retain their original row counts, so overall effects are image weighted. These before/after numbers compare an old adapted system with a different new frozen source checkpoint family; they are not the measured improvement from fitting a head to the new checkpoints.

`cross_version_adaptation_comparisons.csv` retains point metrics for all nine existing scopes; confidence intervals are supplied for the all-condition and clean scopes used here. `source_text_values.json` provides those principal metrics and intervals. Relative intervals absent from the ablation derivation are left blank, not set to zero.

## Seed and scored-system metadata

`source_seed_count` is the number of source-training seeds represented by each compared system and is 3 for both ordinary seed-averaged results and three-member ensembles. `scored_prediction_sets` distinguishes three separately scored source-seed prediction vectors (value 3) from one scored ensemble prediction vector (value 1). `ensemble_members` is 3 for the ensemble rows and is blank/null for individual-seed scoring.

For an ensemble CI, the bootstrap receives one error value per original row from the already scored equal-weight three-member ensemble, retaining the source groups during resampling. It does not treat the ensemble as one training seed or replicate its rows three times. For ordinary per-source-seed comparisons, the three error vectors are averaged per original row before the same group-resampling step.

## Scope

This view supplies Tables/Figures 6 and 7. The alpha-sensitivity figure and Section 5.4.1 use the original fixed-checkpoint inputs. Source-only main comparisons use `../figure_inputs_shared_full_20260911`; efficiency measurements remain in their original result package.
