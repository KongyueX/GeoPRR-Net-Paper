# GeoPRR-Net Paper

Standalone manuscript repository for **GeoPRR-Net: Geometry-Aware
Polar-Relational Routing for Robust Analog Gauge Reading**.

The implementation and reproducibility scripts are maintained in the companion
[GeoPRR-Net code repository](https://github.com/KongyueX/GeoPRR-Net).

## Contents

- `manuscript.tex`: MDPI *Electronics* manuscript source.
- `references.bib`: bibliography database.
- `Definitions/`: bundled MDPI class, styles, bibliography styles, and assets.
- `figures/`: manuscript figures, figure-building scripts, and compact aggregate
  CSV files supporting the reported tables and figures.
- `README_CN.md`: Chinese author notes and submission checklist.

## Build

Upload the repository contents to Overleaf and select `manuscript.tex` as the
main document, or compile it with a compatible local TeX distribution.

Rebuild the quantitative figures from the included aggregate data with:

```bash
python figures/build_geoprr_figures.py
```

Public datasets are referenced from the manuscript. Restricted field images,
model checkpoints, and third-party weights are not redistributed here.
