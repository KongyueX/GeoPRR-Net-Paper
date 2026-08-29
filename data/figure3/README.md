# GeoPRR-Net Figure 3 experiment data

This directory contains the complete sample-level ledgers and derived statistics for the Geometry x Routing factorial (Figure 3a) and perspective/fallback scan (Figure 3d).

- `geometry_routing_per_sample.csv.gz`: four cells x three seeds x 9,348 rows (1,558 images x six conditions).
- `geometry_routing_seed_metrics.csv`: NMAE and Acc@2% for every cell and seed.
- `geometry_routing_summary.csv`: pooled metrics and seed mean +/- sample SD.
- `geometry_routing_conditions.csv`: six-condition NMAE and Acc@2% summaries.
- `geometry_routing_interaction.json`: prespecified difference-in-differences interaction and the 20,000-resample, 14-scene cluster-bootstrap 95% CI.
- `perspective_scan_per_sample.csv.gz`: three models x three seeds x 1,558 images x six angles; no high-angle row is filtered.
- `perspective_scan_seed_metrics.csv`: per-angle, per-model, per-seed metrics.
- `perspective_scan_summary.csv`: NMAE, Acc@2%, P95 error, support-normalization availability, identity fallback, and support fraction.
- `perspective_full_vs_raw.csv`: paired Full GeoPRR minus Raw EfficientNet-B0 error differences with scene-bootstrap 95% CIs.
- `figure3_experiment_summary.json`: machine-readable consolidated results and intervention audit.

NMAE is mean absolute error on the normalized full-scale target. Acc@2% counts absolute error <= 0.02. SD is the sample SD over seeds. Bootstrap resampling treats each of the 14 scenes as a cluster and retains the complete image/condition denominator. The 25- and 45-degree pixels use the same deterministic axis/sign assignment and exact projective transform as the existing formal SyncG conditions.

`valid_support_fraction` is the geometric fraction of the projectively warped source plane remaining inside the canvas. It is reported independently of the all-ones effective model mask used when identity fallback is active.
