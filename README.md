# GeoPRR-Net Paper

Standalone manuscript repository for **GeoPRR-Net: A Geometry-Aware Mixture of
Heterogeneous Experts for Robust Analog Gauge Reading**.

The implementation and reproducibility scripts are maintained in the companion
[GeoPRR-Net code repository](https://github.com/KongyueX/GeoPRR-Net).

The current experiment uses the official 16,000-image SyncG training pool and
4,000-image test split. Results first compare all seven readers on SyncG and
then evaluate zero-shot transfer on RF100-VL and Industrial-1395. Main comparisons
use automatic ROI-to-reading paths and report NMAE, Acc@5%, and coverage.
The [full-source result package](data/geoprr_shared_full_20260911/README.md)
provides the current GeoPRR predictions. The [original experiment package](data/official_syncg_fulltrain_20260908/README.md)
provides the six baselines, retained adapted models and variants, routing-scale
sweep, and recorded execution costs. Both packages include aggregate and
per-sample/source-group data.
Each of Sections 5.1 and 5.2 pairs a direct NMAE/Acc@5% overview with
a separate matched-outcome analysis figure.

## Contents

- `manuscript.tex`: MDPI *Electronics* manuscript source.
- [GeoPRR-Net_中文审阅版V5.9.docx](GeoPRR-Net_中文审阅版V5.9.docx): latest Chinese
  author-review source, synchronized with the English manuscript, tables, figures
  and model-focused limitations. The LaTeX file is the submission source.
- `references.bib`: bibliography database.
- `Definitions/`: bundled MDPI class, styles, bibliography styles, and assets.
- `figures/`: manuscript figures, figure-building scripts, and compact aggregate
  CSV files supporting the reported tables and figures.
- `data/`: compressed public per-sample prediction tables, the
  geometry-by-routing and perspective/fallback ledgers, training histories,
  detailed aggregate statistics, and a machine-readable inventory.
- `README_CN.md`: Chinese author notes and submission checklist.

## Build

Upload the repository contents to Overleaf and select `manuscript.tex` as the
main document, or compile it with a compatible local TeX distribution.

Rebuild the current quantitative figures from the released results in the
dedicated plotting environment with:

```bash
python3 -m venv .venv-figures
.venv-figures/bin/python -m pip install -r figures/requirements.txt
.venv-figures/bin/python figures/build_restructured_results.py
```

Public datasets are referenced from the manuscript. Public result tables are
documented in the [full-source package](data/geoprr_shared_full_20260911/README.md)
and the [original experiment package](data/official_syncg_fulltrain_20260908/README.md).
The [source-only comparison view](data/figure_inputs_shared_full_20260911/README.md)
supplies Figures 2–5. The [cross-configuration view](data/figure_inputs_cross_version_shared_full_20260911/README.md)
supplies Tables/Figures 6 and 7, combining the updated frozen/full reference with
retained adapted and variant results as identified in the captions.
Restricted field images and
non-anonymized Industrial-1395 source records, model checkpoints, and
third-party weights are not redistributed here.
