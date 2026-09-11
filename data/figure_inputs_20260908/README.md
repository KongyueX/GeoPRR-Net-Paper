# Original-release figure-format inputs

These tables expose the `official_syncg_fulltrain_20260908` results in the formats used by the plotting functions.

The current complete-reader efficiency function reads:

- `frozen_industrial.csv`: original three-seed frozen-reader metrics. Error, accuracy and coverage fields are stored on the normalized/fraction scale and converted to percentages by the reader.
- `efficiency_raw.csv`: parameter counts, P50/P95 latency in milliseconds and peak allocated memory in MiB for GeoPRR and the raw CNNs.
- `efficiency_structured.csv`: complete structured-reader parameter counts in millions, P50/P95 latency and peak allocated memory.
- `structured_industrial.csv`: original automatic-reference structured-reader NMAE means and sample SDs in %FS.

Figure 9 replaces only the GeoPRR NMAE and seed SD with the current full-source values from `../figure_inputs_shared_full_20260911`; recorded runtime and memory values remain from the original experiment.

The remaining files preserve other plotting formats for the original release. Current source-only comparison figures use `../figure_inputs_shared_full_20260911`, and Tables/Figures 6 and 7 use `../figure_inputs_cross_version_shared_full_20260911`. The routing-scale figure reads its original sensitivity and diagnostic records directly from `../official_syncg_fulltrain_20260908`.

The current quantitative figure entry point is `figures/build_restructured_results.py`, run from the paper repository with the packages listed in `figures/requirements.txt`.
