"""Build the seven-reader source-only overview for both target domains."""
from pathlib import Path
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
METHODS = ["resnet18", "efficientnet_b0", "mobilenet_v3_large", "yolo", "vdn", "deeplab", "geoprr"]
NAMES = ["ResNet-18", "EfficientNet-B0", "MobileNetV3-L", "YOLO", "VDN", "DeepLab", "GeoPRR-Net"]
COLORS = ["#778492", "#9BA6B0", "#BBC2C8", "#7563A8", "#168A82", "#B17645", "#0F4D92"]
INK, GRID = "#1D2A36", "#D9E1E7"


def main():
    with (ROOT / "data/figure_inputs_shared_full_20260911/seed_mean_sample_sd.csv").open(encoding="utf-8-sig") as stream:
        rows = {(row["dataset"], row["method"]): row for row in csv.DictReader(stream)
                if row["family"] == "main" and row["dataset"] in {"rf100", "industrial"} and row["scope"] == "all_conditions"}
    assert len(rows) == 14
    assert all(int(row["seeds"]) == 3 for row in rows.values())
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial"],
        "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9.5,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": .8, "axes.edgecolor": INK, "text.color": INK,
        "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "pdf.fonttype": 42, "svg.fonttype": "none", "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 7.0), layout="constrained")
    for i, (dataset, name) in enumerate([("rf100", "RF100-VL"), ("industrial", "Industrial-1395")]):
        for j, (metric, label) in enumerate([("nmae_pct_fs", "NMAE (%FS)"), ("acc_at_5_pct", "Acc@5%")]):
            axis = axes[i, j]
            values = np.array([float(rows[dataset, method][metric + "_mean"]) for method in METHODS])
            errors = np.array([float(rows[dataset, method][metric + "_sample_sd"]) for method in METHODS])
            assert np.isfinite([values, errors]).all() and np.all(errors >= 0)
            axis.barh(np.arange(7), values, xerr=errors, color=COLORS, height=.62, capsize=2.5,
                      error_kw={"ecolor": INK, "elinewidth": .8})
            axis.set_yticks(np.arange(7), NAMES)
            axis.invert_yaxis()
            upper = 114 if metric == "acc_at_5_pct" else float(np.max(values + errors)) * 1.25
            axis.set_xlim(0, upper)
            axis.set_xlabel(label)
            title = "NMAE" if j == 0 else "Acc@5%"
            axis.set_title(f"({chr(97 + 2*i + j)}) {name} {title}", loc="left", fontweight="bold", pad=8)
            axis.set_axisbelow(True)
            axis.grid(axis="x", color=GRID, linewidth=.55)
            for method_index, (value, error) in enumerate(zip(values, errors)):
                axis.text(value + error + .025 * upper, method_index,
                          f"{value:.1f}" if metric == "acc_at_5_pct" else f"{value:.2f}",
                          va="center", fontsize=8.5, fontweight="bold" if METHODS[method_index] == "geoprr" else "normal")
    stem = HERE / "fig_zero_shot_overview"
    fig.savefig(stem.with_suffix(".png"), dpi=400)
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".svg"))
    plt.close(fig)


if __name__ == "__main__":
    main()
