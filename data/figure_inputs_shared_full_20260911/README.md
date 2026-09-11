# Composite source-only figure inputs: shared full-source GeoPRR

This directory supplies the source-only tables and the four source/zero-shot comparison figures from the two published result archives.

## Provenance and model identities

- `method=geoprr, family=main` is a compatibility alias for `shared_full` in `../geoprr_shared_full_20260911`.
- The other six methods (Raw ResNet-18, Raw EfficientNet-B0, Raw MobileNetV3-Large, YOLO, VDN and DeepLab) are the unchanged `family=main` source-only observations from `../official_syncg_fulltrain_20260908`.
- VDN and DeepLab retain automatic reference geometry. Annotation-assisted observations are not included.
- Every baseline prediction field is identical to its original archive. Source archives are unchanged.

## Included tables

`per_seed_metrics.csv` contains all 567 main method/seed/dataset/scope rows; `seed_mean_sample_sd.csv` contains the corresponding 189 means and sample SDs. All nine existing condition scopes are retained.

`details/per_sample/{syncg,rf100,industrial}_main.csv.gz` keeps the original schema and row order. Only GeoPRR normalized prediction, normalized error and status fields are replaced. Targets, sample IDs, group aliases, method and seed pairing remain identical.

`details/group_comparisons.csv.gz` contains 4,698 target-domain group rows for six GeoPRR comparisons, two target datasets and nine scopes. Errors are first averaged across seeds for each original sample-condition row, then averaged within each group. Weight groups by `rows_per_seed` to recover the overall image-weighted effect. Negative candidate-minus-reference values favor shared_full GeoPRR.

`paired_comparisons.csv` covers the currently used all-condition and clean scopes: 36 comparisons across three datasets and six baselines. The six Raw EfficientNet-B0 absolute 95% intervals are copied from the new release's official paired table. That table does not publish a resampling RNG seed or relative-reduction interval; those compatibility fields are blank, not zero. Every other absolute and relative interval reuses `figures/derive_condition_summaries.py::paired_group_bootstrap_fast`, with 20,000 source-group resamples and dataset seeds SyncG=20260907, RF100=20261007, Industrial=20261107. All calls use per-row errors averaged across source seeds before resampling. These intervals describe source-group uncertainty conditional on the three fitted seeds; seed SD is reported separately. `paired_comparisons_provenance.csv` identifies each interval source.

`main_table_comparisons.csv` provides descriptive NMAE differences, relative reductions and accuracy gains for all nine scopes. `paired_group_consistency.csv` records descriptive better/tied/worse group counts. `paired_acc5_outcomes.csv` records the 18 same-seed rescue/regression rate means, sample SDs and net Acc@5 gains. `source_text_values.json` provides the updated GeoPRR all-condition/clean summaries and paired Acc@5 rates used in the source/zero-shot prose. `validation.json` records the completed direct checks.

## Scope boundaries

The shared_full package changes GeoPRR source training: it reuses same-seed RawEff foundations trained on 16,000 images and fits downstream modules and the final router on all 16,000 source images (96,000 final-router image-condition rows). It reuses one saved warm initializer previously fitted on A=12,818 images. This differs from the original A/B-separated GeoPRR protocol. The fixed source-test image roster is unchanged and is not scene-disjoint.

Target-adapted models, ablation variants, alpha scans and efficiency measurements belong to the original GeoPRR configuration and are outside this source-only view. Tables/Figures 6 and 7 use the separately documented cross-configuration view.
