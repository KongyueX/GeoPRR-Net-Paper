"""Build paired corruption, reading-transition and tolerance evidence on SyncG."""
from pathlib import Path
import csv
import gzip
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "data/figure_inputs_shared_full_20260911"
METHODS = ["resnet18", "efficientnet_b0", "mobilenet_v3_large", "yolo", "vdn", "deeplab", "geoprr"]
NAMES = ["ResNet-18", "EfficientNet-B0", "MobileNetV3-L", "YOLO", "VDN", "DeepLab", "GeoPRR-Net"]
COLORS = ["#778492", "#9BA6B0", "#BBC2C8", "#7563A8", "#168A82", "#B17645", "#0F4D92"]
SEEDS = [20262020, 20262021, 20262022]
CONDITIONS = ["clean", "blur_moderate", "blur_severe", "perspective_moderate", "perspective_severe", "combined_severe"]
CONDITION_NAMES = ["Blur M", "Blur S", "Perspective M", "Perspective S", "Perspective + blur"]
INK, GRID = "#1D2A36", "#D9E1E7"


def load_data():
    errors = np.full((3, 7, 24000), np.nan)
    successful = np.zeros((3, 7, 24000), dtype=bool)
    index = {}
    metadata = []
    method_index = {method: i for i, method in enumerate(METHODS)}
    seed_index = {seed: i for i, seed in enumerate(SEEDS)}
    with gzip.open(SOURCE / "details/per_sample/syncg_main.csv.gz", "rt", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            assert row["family"] == "main" and row["dataset"] == "syncg"
            key = (row["sample_id"], row["condition"])
            target = float(row["normalized_target"])
            if key not in index:
                index[key] = len(index)
                metadata.append((row["group_id"], target))
            position = index[key]
            assert position < 24000 and metadata[position] == (row["group_id"], target)
            seed, method = seed_index[int(row["seed"])], method_index[row["method"]]
            assert np.isnan(errors[seed, method, position])
            error = float(row["normalized_absolute_error"])
            success = row["status"] == "success"
            if success:
                assert abs(abs(float(row["normalized_prediction"]) - target) - error) < 1e-12
            else:
                assert row["status"] == "failure" and row["normalized_prediction"] == "" and error == 1.0
            errors[seed, method, position] = error
            successful[seed, method, position] = success
    assert len(index) == 24000 and np.isfinite(errors).all()
    assert len({sample for sample, _ in index}) == 4000
    assert len({group for group, _ in metadata}) == 145
    assert {condition for _, condition in index} == set(CONDITIONS)
    with (SOURCE / "seed_mean_sample_sd.csv").open(encoding="utf-8-sig") as stream:
        summary = {(row["method"], row["scope"]): row for row in csv.DictReader(stream)
                   if row["family"] == "main" and row["dataset"] == "syncg"}
    return errors, successful, index, summary


def main():
    errors, successful, index, summary = load_data()
    increments = np.zeros((7, 5))
    for column, condition in enumerate(CONDITIONS[1:]):
        samples = sorted(sample for sample, current in index if current == condition)
        assert len(samples) == 4000
        perturbed = [index[sample, condition] for sample in samples]
        clean = [index[sample, "clean"] for sample in samples]
        increments[:, column] = (errors[:, :, perturbed] - errors[:, :, clean]).mean(axis=(0, 2)) * 100
        for method_index, method in enumerate(METHODS):
            expected = float(summary[method, condition]["nmae_pct_fs_mean"]) - float(summary[method, "clean"]["nmae_pct_fs_mean"])
            assert abs(increments[method_index, column] - expected) < 1e-10

    correct_at_5 = successful & (errors <= .05)
    regression = np.array([(correct_at_5[:, i] & ~correct_at_5[:, -1]).mean(axis=1).mean() * 100 for i in range(6)])
    rescue = np.array([(~correct_at_5[:, i] & correct_at_5[:, -1]).mean(axis=1).mean() * 100 for i in range(6)])
    tolerances = np.linspace(0, 10, 1001)
    curves = np.zeros((7, len(tolerances)))
    for i, method in enumerate(METHODS):
        for seed in range(3):
            valid_errors = np.sort(errors[seed, i, successful[seed, i]])
            curves[i] += np.searchsorted(valid_errors, tolerances / 100, side="right") / 24000 / 3
        expected = float(summary[method, "all_conditions"]["acc_at_5_pct_mean"])
        assert abs(curves[i, 500] * 100 - expected) < 1e-10
        if i < 6:
            geo = float(summary["geoprr", "all_conditions"]["acc_at_5_pct_mean"])
            assert abs(rescue[i] - regression[i] - (geo - expected)) < 1e-10

    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial"],
        "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9.5,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8.5,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "axes.edgecolor": INK, "axes.linewidth": .8,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "pdf.fonttype": 42, "svg.fonttype": "none",
        "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=(8.2, 7.0), layout="constrained")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.05, 1])
    heat_ax = fig.add_subplot(grid[0, :])
    pair_ax = fig.add_subplot(grid[1, 0])
    curve_ax = fig.add_subplot(grid[1, 1])

    extent = 5 * np.ceil(np.abs(increments).max() / 5)
    cmap = LinearSegmentedColormap.from_list("clean_change", ["#0F4D92", "white", "#B94B45"])
    image = heat_ax.imshow(increments, cmap=cmap, norm=TwoSlopeNorm(vmin=-extent, vcenter=0, vmax=extent), aspect="auto")
    heat_ax.set_yticks(range(7), NAMES)
    heat_ax.set_xticks(range(5), CONDITION_NAMES)
    heat_ax.tick_params(length=0)
    heat_ax.set_title("(a) Change from matched clean images", loc="left", fontweight="bold", pad=8)
    for row in range(7):
        for column in range(5):
            value = increments[row, column]
            heat_ax.text(column, row, f"{value:+.4f}", ha="center", va="center", fontsize=8.5,
                         color="white" if abs(value) > .6 * extent else INK)
    colorbar = fig.colorbar(image, ax=heat_ax, location="right", fraction=.028, pad=.025)
    colorbar.set_ticks([-30, -15, 0, 15, 30])
    colorbar.set_label("ΔNMAE from clean (%FS)")

    limit = np.ceil(max(rescue.max(), regression.max()) / 2) * 2 + 2
    pair_ax.plot([0, limit], [0, limit], color="#657482", linestyle="--", linewidth=.8, label="y = x")
    for i in range(6):
        pair_ax.scatter(regression[i], rescue[i], s=28, color=COLORS[i], zorder=3)
        offset = (68, 0) if i == 1 else (5, 0)
        leader = {"arrowstyle": "-", "color": COLORS[i], "linewidth": .6} if i == 1 else None
        pair_ax.annotate(NAMES[i], (regression[i], rescue[i]), xytext=offset, textcoords="offset points",
                         ha="left", va="center", color=INK, fontsize=8.5, arrowprops=leader)
    pair_ax.set_xlim(-.5, limit)
    pair_ax.set_ylim(0, limit)
    pair_ax.set_aspect("equal", adjustable="box")
    pair_ax.set_xlabel("Regression (% of all rows)")
    pair_ax.set_ylabel("Rescue (% of all rows)")
    pair_ax.set_title("(b) Paired correct readings at 5%FS", loc="left", fontweight="bold", pad=8)
    pair_ax.grid(color=GRID, linewidth=.55)
    pair_ax.set_axisbelow(True)
    pair_ax.legend(loc="lower right")

    styles = ["--", ":", "-.", "-", "-", "-", "-"]
    for i in range(7):
        curve_ax.plot(tolerances, curves[i], color=COLORS[i], linestyle=styles[i],
                      linewidth=2.1 if i == 6 else 1.4, label=NAMES[i], zorder=5 if i == 6 else 2)
    curve_ax.axvline(5, color="#657482", linestyle="--", linewidth=.8, zorder=1)
    curve_ax.set_xlim(0, 10)
    curve_ax.set_ylim(0, 1.02)
    curve_ax.set_xticks([0, 2, 4, 5, 6, 8, 10])
    curve_ax.set_yticks([0, .25, .5, .75, 1])
    curve_ax.set_xlabel("Error tolerance (%FS)")
    curve_ax.set_ylabel("Correct-reading fraction")
    curve_ax.set_title("(c) Reading accuracy across tolerances", loc="left", fontweight="bold", pad=8)
    curve_ax.grid(color=GRID, linewidth=.55)
    curve_ax.set_axisbelow(True)
    fig.legend(*curve_ax.get_legend_handles_labels(), loc="outside lower center", ncol=4)

    stem = HERE / "fig_syncg_evidence"
    fig.savefig(stem.with_suffix(".png"), dpi=400)
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".svg"))
    plt.close(fig)
    with (HERE / "syncg_rescue_regression.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["method", "regression_pct_all_rows", "rescue_pct_all_rows", "net_acc5_gain_pp"])
        for i in range(6):
            writer.writerow([METHODS[i], regression[i], rescue[i], rescue[i] - regression[i]])
    (HERE / "syncg_evidence_values.json").write_text(json.dumps({
        "methods": METHODS, "conditions": CONDITIONS[1:], "seeds": SEEDS,
        "images_per_condition": 4000, "rows_per_seed": 24000, "scene_groups": 145,
        "clean_increment_nmae_pct_fs": increments.tolist(),
        "regression_pct_all_rows": regression.tolist(), "rescue_pct_all_rows": rescue.tolist(),
        "correct_fraction_at_5": curves[:, 500].tolist(),
        "failed_prediction_counts_per_seed_method": (~successful).sum(axis=2).tolist(),
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"regression": dict(zip(METHODS[:-1], regression.tolist())),
                      "rescue": dict(zip(METHODS[:-1], rescue.tolist()))}, indent=2))


if __name__ == "__main__":
    main()
