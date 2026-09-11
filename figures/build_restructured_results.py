"""Build source-only, matched-adaptation and mechanism figures from released results."""
from pathlib import Path
import csv
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/official_syncg_fulltrain_20260908"
OUTPUT = ROOT / "figures"
METHODS = ["resnet18", "efficientnet_b0", "mobilenet_v3_large", "yolo", "vdn", "deeplab", "geoprr"]
CNN_METHODS = METHODS[:3]
ADAPTED_METHODS = CNN_METHODS + ["geoprr"]
NAMES = {
    "resnet18": "ResNet-18", "efficientnet_b0": "EfficientNet-B0",
    "mobilenet_v3_large": "MobileNetV3-L", "vdn": "VDN",
    "deeplab": "DeepLab", "yolo": "YOLO", "geoprr": "GeoPRR-Net",
}
COLORS = {
    "resnet18": "#778492", "efficientnet_b0": "#9BA6B0", "mobilenet_v3_large": "#BBC2C8",
    "vdn": "#168A82", "deeplab": "#B17645", "yolo": "#7563A8", "geoprr": "#0F4D92",
}
INK, GRID = "#1D2A36", "#D9E1E7"
CONDITIONS = ["clean", "blur_moderate", "blur_severe", "perspective_moderate", "perspective_severe", "combined_severe"]
CONDITION_NAMES = ["Clean", "Blur M", "Blur S", "Persp. M", "Persp. S", "Persp. + blur"]
CORE = ["no_geometry_fusion", "fixed_routing", "no_relational_transport"]
CORE_NAMES = ["No geometry fusion", "Fixed routing", "No relational transport"]
CORE_COLORS = ["#B94B45", "#7563A8", "#168A82"]

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 8, "axes.labelsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": .75, "axes.edgecolor": INK, "text.color": INK,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "legend.frameon": False, "pdf.fonttype": 42, "svg.fonttype": "none",
    "figure.facecolor": "white", "savefig.facecolor": "white",
})


def read_csv(name):
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


SUMMARY = {(r["family"], r["method"], r["dataset"], r["scope"]): r for r in read_csv("seed_mean_sample_sd.csv")}
PAIRED = {(r["comparison"], r["dataset"], r["scope"]): r for r in read_csv("paired_comparisons.csv")}


def save(fig, stem):
    fig.savefig(OUTPUT / f"{stem}.png", dpi=600)
    fig.savefig(OUTPUT / f"{stem}.pdf")
    fig.savefig(OUTPUT / f"{stem}.svg")
    fig.savefig(OUTPUT / f"{stem}.tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


def panel(ax, letter, title, *, grid="x"):
    ax.set_title(f"({letter}) {title}", loc="left", fontweight="bold", pad=8)
    if grid:
        ax.set_axisbelow(True)
        ax.grid(axis=grid, color=GRID, linewidth=.6)
    ax.tick_params(length=3)


def metric_bars(ax, methods, rows, metric, *, ensemble=False):
    key = metric if ensemble else metric + "_mean"
    values = np.array([float(r[key]) for r in rows])
    errors = np.zeros(len(rows)) if ensemble else np.array([float(r[metric + "_sample_sd"]) for r in rows])
    assert np.isfinite(values).all() and np.isfinite(errors).all()
    y = np.arange(len(methods))
    ax.barh(y, values, xerr=None if ensemble else errors, color=[COLORS[m] for m in methods],
            height=.62, capsize=2, error_kw={"ecolor": INK, "elinewidth": .8})
    ax.set_yticks(y, [NAMES[m] for m in methods])
    ax.invert_yaxis()
    upper = 109 if metric == "acc_at_5_pct" else float(np.max(values + errors)) * 1.25
    ax.set_xlim(0, upper)
    ax.set_xlabel("Acc@5%" if metric == "acc_at_5_pct" else "NMAE (%FS)")
    for i, (value, error) in enumerate(zip(values, errors)):
        ax.text(value + error + upper * .025, i, f"{value:.1f}" if metric == "acc_at_5_pct" else f"{value:.2f}",
                va="center", fontsize=6.5, fontweight="bold" if methods[i] == "geoprr" else "normal")


def paired_values(rows):
    values = np.array([float(r["candidate_minus_reference_pct_fs"]) for r in rows])
    low = np.array([float(r["ci95_low_pct_fs"]) for r in rows])
    high = np.array([float(r["ci95_high_pct_fs"]) for r in rows])
    assert np.isfinite([values, low, high]).all()
    assert np.all(low <= values) and np.all(values <= high)
    return values, low, high


def syncg():
    rows = [SUMMARY["main", m, "syncg", "all_conditions"] for m in METHODS]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.5), layout="constrained")
    metric_bars(axes[0, 0], METHODS, rows, "nmae_pct_fs")
    panel(axes[0, 0], "a", "SyncG error")
    metric_bars(axes[0, 1], METHODS, rows, "acc_at_5_pct")
    panel(axes[0, 1], "b", "SyncG reading accuracy")

    heat = np.array([[float(SUMMARY["main", m, "syncg", c]["nmae_pct_fs_mean"]) for c in CONDITIONS] for m in METHODS])
    ax = axes[1, 0]
    im = ax.imshow(heat, cmap="Blues", vmin=0, vmax=float(heat.max()), aspect="auto")
    ax.set_yticks(np.arange(7), [NAMES[m] for m in METHODS])
    ax.set_xticks(np.arange(6), CONDITION_NAMES, rotation=30, ha="right", rotation_mode="anchor")
    ax.tick_params(length=0)
    for i in range(7):
        for j in range(6):
            ax.text(j, i, f"{heat[i,j]:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if heat[i,j] > heat.max() * .58 else INK)
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=.065, pad=.04, aspect=28)
    cb.set_label("NMAE (%FS)")
    panel(ax, "c", "Condition-wise error", grid=None)

    comparisons = [PAIRED["geoprr_minus_" + m, "syncg", "all_conditions"] for m in METHODS[:-1]]
    values, low, high = paired_values(comparisons)
    ax = axes[1, 1]
    for i, method in enumerate(METHODS[:-1]):
        ax.errorbar(values[i], i, xerr=[[values[i]-low[i]], [high[i]-values[i]]],
                    fmt="o", color=COLORS[method], capsize=2.5, markersize=4.5, elinewidth=1)
    ax.axvline(0, color=INK, linewidth=.75, linestyle="--")
    ax.set_yticks(np.arange(6), [NAMES[m] for m in METHODS[:-1]])
    ax.invert_yaxis()
    ax.set_xlim(float(low.min()) * 1.1, .25)
    ax.set_xlabel("GeoPRR − comparator NMAE (%FS)")
    panel(ax, "d", "Paired differences")
    save(fig, "fig2_syncg_performance")


def zero_shot():
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0), layout="constrained")
    for i, (dataset, title) in enumerate([("rf100", "RF100-VL"), ("industrial", "Industrial-1395")]):
        rows = [SUMMARY["main", m, dataset, "all_conditions"] for m in METHODS]
        metric_bars(axes[i, 0], METHODS, rows, "nmae_pct_fs")
        panel(axes[i, 0], chr(97 + 2*i), f"{title} error")
        metric_bars(axes[i, 1], METHODS, rows, "acc_at_5_pct")
        panel(axes[i, 1], chr(98 + 2*i), f"{title} reading accuracy")
    save(fig, "fig_zero_shot_transfer")


def adaptation():
    view = ROOT / "data/figure_inputs_cross_version_shared_full_20260911"
    with (view / "seed_mean_sample_sd.csv").open(encoding="utf-8-sig") as stream:
        summary = {(r["family"], r["method"], r["dataset"], r["scope"]): r for r in csv.DictReader(stream)}
    seeds = ["20262020", "20262021", "20262022"]
    with (view / "per_seed_metrics.csv").open(encoding="utf-8-sig") as stream:
        source = [r for r in csv.DictReader(stream)
                  if r["family"] in {"main", "adapted"} and r["method"] in ADAPTED_METHODS
                  and r["dataset"] == "industrial" and r["scope"] == "all_conditions"]
    rows = {(r["family"], r["method"], r["seed"]): r for r in source}
    assert len(source) == len(rows) == 24
    assert all((r["images"], r["rows"], r["groups"]) == ("1395", "8370", "52") for r in source)
    with plt.rc_context({"font.sans-serif": ["Arial"], "font.size": 8.5, "axes.labelsize": 8.5,
                         "axes.titlesize": 9.5, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                         "legend.fontsize": 8.5}):
        fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.9), layout="constrained")
        for axis, metric, label, letter in zip(axes, ["nmae_pct_fs", "acc_at_5_pct"],
                                              ["NMAE (%FS)", "Acc@5%"], ["a", "b"]):
            values = np.array([[[float(rows[family, method, seed][metric]) for seed in seeds]
                                for family in ["main", "adapted"]] for method in ADAPTED_METHODS])
            means, errors = values.mean(axis=2), values.std(axis=2, ddof=1)
            for i, method in enumerate(ADAPTED_METHODS):
                hero = method == "geoprr"
                color = COLORS[method]
                axis.plot(means[i], [i, i], color=color, linewidth=2.1 if hero else 1.1,
                          alpha=1 if hero else .65, zorder=2)
                for state, family in enumerate(["main", "adapted"]):
                    recorded = summary[family, method, "industrial", "all_conditions"]
                    assert abs(means[i, state] - float(recorded[metric + "_mean"])) < 1e-10
                    assert abs(errors[i, state] - float(recorded[metric + "_sample_sd"])) < 1e-10
                    axis.errorbar(means[i, state], i, xerr=errors[i, state], fmt="o", color=color,
                                  markerfacecolor="white" if state == 0 else color, markeredgewidth=1.2,
                                  markersize=6.5 if hero else 5.5, capsize=3, elinewidth=1.2 if hero else .8,
                                  alpha=1 if hero else .7, zorder=4 if hero else 3)
                    axis.annotate(f"{means[i, state]:.2f}", (means[i, state], i), xytext=(0, 9),
                                  textcoords="offset points", ha="center", va="bottom", fontsize=8.5,
                                  color=color if hero else INK, fontweight="bold" if hero else "normal")
            axis.set_yticks(np.arange(4), [NAMES[m] for m in ADAPTED_METHODS])
            axis.get_yticklabels()[-1].set_color(COLORS["geoprr"])
            axis.get_yticklabels()[-1].set_fontweight("bold")
            axis.set_ylim(3.5, -.7)
            axis.set_xlim(0, 102 if metric == "acc_at_5_pct" else float(np.max(means + errors)) * 1.12)
            axis.set_xlabel(label)
            panel(axis, letter, label)
        handles = [Line2D([0], [0], marker="o", markerfacecolor="white", markeredgecolor=INK,
                          color=INK, linestyle="", label="Frozen", markersize=6),
                   Line2D([0], [0], marker="o", markerfacecolor=INK, markeredgecolor=INK,
                          color=INK, linestyle="", label="Head-adapted", markersize=6)]
        fig.legend(handles=handles, loc="outside lower center", ncol=2)
        save(fig, "fig4_industrial_1395")


def ablation():
    view = ROOT / "data/figure_inputs_cross_version_shared_full_20260911"
    with (view / "seed_mean_sample_sd.csv").open(encoding="utf-8-sig") as stream:
        summary = {(r["family"], r["method"], r["dataset"], r["scope"]): r for r in csv.DictReader(stream)}
    with (view / "paired_comparisons.csv").open(encoding="utf-8-sig") as stream:
        pairs = {(r["comparison"], r["dataset"], r["scope"]): r for r in csv.DictReader(stream)}
    with plt.rc_context({"font.sans-serif": ["Arial"], "font.size": 8.5, "axes.labelsize": 8.5,
                         "axes.titlesize": 9.5, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                         "legend.fontsize": 8.5, "axes.linewidth": .8}):
        fig = plt.figure(figsize=(8.2, 5.4), layout="constrained")
        grid = fig.add_gridspec(2, 2, height_ratios=[1, .86])
        ax = fig.add_subplot(grid[0, 0])
        effects_ax = fig.add_subplot(grid[0, 1])
        heat_ax = fig.add_subplot(grid[1, :])
        for names, label, color, marker in [(["fixed_routing", "geoprr"], "Geometry on", COLORS["geoprr"], "o"),
                                            (["no_geometry_fixed_routing", "no_geometry_fusion"], "Geometry off", "#B94B45", "s")]:
            rows = [summary["main" if m == "geoprr" else "ablation", m, "syncg", "all_conditions"] for m in names]
            values = [float(r["nmae_pct_fs_mean"]) for r in rows]
            errors = [float(r["nmae_pct_fs_sample_sd"]) for r in rows]
            ax.errorbar([0, 1], values, yerr=errors, marker=marker, color=color, linewidth=1.5,
                        capsize=2.5, markersize=5.5, label=label)
        ax.set_xticks([0, 1], ["Fixed routing", "Adaptive routing"])
        ax.set_xlim(-.15, 1.15)
        ax.set_ylim(.68, 1.65)
        ax.set_ylabel("NMAE (%FS)")
        ax.legend(loc="upper right")
        ax.set_title("(a) Geometry × routing", loc="left", fontweight="bold", pad=8)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=GRID, linewidth=.55)

        rows = [pairs["geoprr_" + v + "_minus_full", "syncg", "all_conditions"] for v in CORE]
        values, low, high = paired_values(rows)
        for i, color in enumerate(CORE_COLORS):
            effects_ax.errorbar(values[i], i, xerr=[[values[i]-low[i]], [high[i]-values[i]]], fmt="o", color=color,
                                capsize=2.5, markersize=5.5, elinewidth=1)
        effects_ax.axvline(0, color=INK, linewidth=.75, linestyle="--")
        effects_ax.set_yticks(np.arange(3), CORE_NAMES)
        effects_ax.set_ylim(2.5, -.5)
        effects_ax.set_xlim(-.015, float(high.max()) * 1.15)
        effects_ax.set_xlabel("Variant − full NMAE (%FS)")
        effects_ax.set_title("(b) Core ablation effects", loc="left", fontweight="bold", pad=8)
        effects_ax.set_axisbelow(True)
        effects_ax.grid(axis="x", color=GRID, linewidth=.55)

        heat = np.array([[float(pairs["geoprr_"+v+"_minus_full", "syncg", c]["candidate_minus_reference_pct_fs"])
                          for c in CONDITIONS] for v in CORE])
        cmap = LinearSegmentedColormap.from_list("core_effect", ["#DCEAF7", "white", "#B94B45"])
        norm = TwoSlopeNorm(vmin=-.05, vcenter=0, vmax=1.5)
        im = heat_ax.imshow(heat, cmap=cmap, norm=norm, aspect="auto")
        heat_ax.set_xticks(np.arange(6), CONDITION_NAMES)
        heat_ax.set_yticks(np.arange(3), CORE_NAMES)
        heat_ax.tick_params(length=0)
        for i in range(3):
            for j in range(6):
                heat_ax.text(j, i, f"{heat[i,j]:+.4f}", ha="center", va="center", fontsize=8.5,
                             color="white" if heat[i,j] > .7 else INK)
        cb = fig.colorbar(im, ax=heat_ax, orientation="horizontal", fraction=.075, pad=.05, aspect=45)
        cb.set_ticks([-.05, 0, .5, 1.0, 1.5])
        cb.set_label("Variant − full NMAE (%FS)")
        heat_ax.set_title("(c) Condition-wise core ablation effects", loc="left", fontweight="bold", pad=8)
        stem = OUTPUT / "fig3_ablation_routing"
        fig.savefig(stem.with_suffix(".png"), dpi=400)
        fig.savefig(stem.with_suffix(".pdf"))
        fig.savefig(stem.with_suffix(".svg"))
        fig.savefig(stem.with_suffix(".tiff"), dpi=400, pil_kwargs={"compression": "tiff_lzw"})
        plt.close(fig)


def polar():
    scopes = CONDITIONS + ["all_conditions"]
    rows = [PAIRED["geoprr_no_polar_evidence_minus_full", "syncg", c] for c in scopes]
    values, low, high = paired_values(rows)
    fig, ax = plt.subplots(figsize=(7.2, 3.25), layout="constrained")
    for i in range(7):
        color = COLORS["geoprr"] if i == 6 else "#D38B2C"
        ax.errorbar(values[i], i, xerr=[[values[i]-low[i]], [high[i]-values[i]]], fmt="D" if i == 6 else "o",
                    color=color, capsize=3, markersize=5, elinewidth=1)
    ax.axvline(0, color=INK, linewidth=.75, linestyle="--")
    ax.axhline(5.5, color=GRID, linewidth=.6)
    ax.set_yticks(np.arange(7), CONDITION_NAMES + ["All six"])
    ax.set_ylim(6.5, -.5)
    extent = max(abs(float(low.min())), abs(float(high.max()))) * 1.12
    ax.set_xlim(-extent, extent)
    ax.set_xlabel("No polar evidence − full NMAE (%FS)")
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=GRID, linewidth=.6)
    save(fig, "fig_polar_diagnostic")


if __name__ == "__main__":
    subprocess.run([sys.executable, str(OUTPUT / "build_syncg_overview.py")], check=True)
    subprocess.run([sys.executable, str(OUTPUT / "build_syncg_evidence.py")], check=True)
    subprocess.run([sys.executable, str(OUTPUT / "build_zero_shot_overview.py")], check=True)
    subprocess.run([sys.executable, str(OUTPUT / "build_zero_shot_evidence.py")], check=True)
    adaptation()
    ablation()
    subprocess.run([sys.executable, str(OUTPUT / "build_alpha_prior_sensitivity.py")], check=True)
    from build_comparison_visuals import efficiency
    efficiency()
