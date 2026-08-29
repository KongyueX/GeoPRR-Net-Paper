# GeoPRR-Net Paper

Standalone manuscript repository for **GeoPRR-Net: Geometry-Aware
Polar-Relational Routing for Robust Analog Gauge Reading**.

The implementation and reproducibility scripts are maintained in the companion
[GeoPRR-Net code repository](https://github.com/KongyueX/GeoPRR-Net).

## Contents

- `manuscript.tex`: MDPI *Electronics* manuscript source.
- `GeoPRR-Net_中文翻译版V4.docx`: Chinese author-review translation synchronized
  with the manuscript figures and captions; it is not the submission source.
  Chinese review DOCX revisions use an incrementing `V<N>` filename suffix;
  the current version is V4.
- `references.bib`: bibliography database.
- `Definitions/`: bundled MDPI class, styles, bibliography styles, and assets.
- `figures/`: manuscript figures, figure-building scripts, and compact aggregate
  CSV files supporting the reported tables and figures.
- `data/`: compressed public per-sample prediction tables, the Figure 3
  Geometry × Routing and perspective/fallback ledgers, training histories,
  detailed aggregate statistics, and a machine-readable inventory.
- `README_CN.md`: Chinese author notes and submission checklist.

## Build

Upload the repository contents to Overleaf and select `manuscript.tex` as the
main document, or compile it with a compatible local TeX distribution.

Re-derive the condition summaries from the public release tables, then rebuild
the quantitative figures with:

```bash
python figures/derive_condition_summaries.py
python figures/build_geoprr_figures.py
```

Public datasets are referenced from the manuscript. Public result tables are
documented in [`data/README.md`](data/README.md). Restricted field images and
per-sample Industrial-1395 records, model checkpoints, and third-party weights
are not redistributed here.
