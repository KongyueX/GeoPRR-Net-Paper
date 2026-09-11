"""Plot routing-scale sensitivity and default-scale expert composition."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np


OUTPUT = Path(__file__).resolve().parent
ROOT = OUTPUT.parent
SOURCE = ROOT / "data/official_syncg_fulltrain_20260908/alpha_prior_sensitivity.csv"
DIAGNOSTICS = ROOT / "data/official_syncg_fulltrain_20260908/geoprr_diagnostics.json"
DATASETS = ("SyncG", "RF100-VL", "Industrial-1395")
SEEDS = ("20262020", "20262021", "20262022")
ALPHAS = (0, 10, 25, 50, 100, 200)
COLORS = ("#0F4D92", "#7563A8", "#168A82")
MARKERS = ("o", "s", "^")
EXPERTS = ("base", "polar_evidence", "relational_transport")
EXPERT_LABELS = ("Base", "Polar", "Relational")
EXPERT_COLORS = ("#0F4D92", "#C48832", "#168A82")
DEFAULT = "alpha_100_default_prior"
SCOPES = ("all_conditions", "projective_three")
INK, GRID = "#1D2A36", "#D9E1E7"

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.75,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))
index = {
    (r["dataset"], r["seed"], r["configuration"], r["scope"]): r
    for r in rows
}
assert len(index) == len(rows) == 567
summaries = []


def values(dataset, configuration, scope, metric):
    return np.array([
        float(index[(dataset, seed, configuration, scope)][metric])
        for seed in SEEDS
    ])


def paired_error(dataset, configuration, scope):
    return (
        values(dataset, configuration, scope, "nmae_pct_fs")
        - values(dataset, DEFAULT, scope, "nmae_pct_fs")
    )


def summary(panel, dataset, configuration, scope, metric, data):
    mean, sd = float(data.mean()), float(data.std(ddof=1))
    summaries.append({
        "panel": panel, "dataset": dataset, "configuration": configuration,
        "scope": scope, "metric": metric, "mean": mean, "sample_sd": sd,
        **{f"seed_{seed}": float(value) for seed, value in zip(SEEDS, data)},
    })
    return mean, sd


def style(ax, letter, title):
    ax.set_title(f"{letter}  {title}", loc="left", fontweight="bold", pad=11)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.55, alpha=0.8)
    ax.tick_params(axis="both", length=3, width=0.7)


fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.8))
fig.subplots_adjust(left=0.115, right=0.98, bottom=0.105, top=0.855,
                    wspace=0.38, hspace=0.60)
handles = [
    Line2D([0], [0], color=color, marker=marker, linewidth=1.6,
           markersize=5, label=name)
    for name, color, marker in zip(DATASETS, COLORS, MARKERS)
]
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.54, 0.985),
           ncol=3, handlelength=2, columnspacing=2.1)

positions = np.arange(len(ALPHAS))
for ax in axes[0]:
    ax.set_xticks(positions, [str(alpha) for alpha in ALPHAS])
    ax.set_xlim(-0.25, 5.25)
    ax.set_xlabel("Routing scale α")
    ax.axvline(4, color="#AEBBC6", linewidth=0.8, linestyle=(0, (3, 3)), zorder=0)

style(axes[0, 0], "a", "Overall error")
style(axes[0, 1], "b", "Weight concentration")
axes[0, 0].set_ylabel("ΔNMAE from α = 100 (%FS)")
axes[0, 1].set_ylabel("Rows with max(w) > 0.95 (%)")
axes[0, 0].axhline(0, color="#63717E", linewidth=0.85)
for dataset, color, marker in zip(DATASETS, COLORS, MARKERS):
    changes, concentration = [], []
    for alpha in ALPHAS:
        configuration = f"alpha_{alpha}_default_prior"
        delta = paired_error(dataset, configuration, "all_conditions")
        changes.append(summary("a", dataset, configuration, "all_conditions",
                               "paired_delta_nmae_pct_fs", delta))
        saturation = values(dataset, configuration, "all_conditions",
                            "percent_max_weight_strictly_gt_095")
        concentration.append(summary("b", dataset, configuration, "all_conditions",
                                     "percent_max_weight_strictly_gt_095", saturation))
    for ax, statistics in zip(axes[0], (changes, concentration)):
        means, sds = np.array(statistics).T
        ax.errorbar(positions, means, yerr=sds, color=color, marker=marker,
                    linewidth=1.6, markersize=4.6, capsize=2.2,
                    elinewidth=0.9, markeredgewidth=0.8, zorder=3)
axes[0, 0].set_ylim(-0.045, 0.62)
axes[0, 0].set_yticks((0, 0.2, 0.4, 0.6))
axes[0, 1].set_ylim(-0.8, 16)
axes[0, 1].set_yticks((0, 5, 10, 15))

comparisons = (
    ("c", "Scale: 200 − 100", "alpha_200_default_prior"),
)
for ax, (letter, title, configuration) in zip(axes[1], comparisons):
    style(ax, letter, title)
    ax.set_xticks((0, 1), ("All conditions", "Projective three"))
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel("Paired ΔNMAE (%FS)")
    ax.axhline(0, color="#63717E", linewidth=0.85)
    ax.set_ylim(-0.028, 0.032)
    ax.set_yticks((-0.02, -0.01, 0, 0.01, 0.02, 0.03))
    for j, (dataset, color, marker) in enumerate(zip(DATASETS, COLORS, MARKERS)):
        for k, scope in enumerate(SCOPES):
            data = paired_error(dataset, configuration, scope)
            mean, sd = summary(letter, dataset, configuration, scope,
                               "paired_delta_nmae_pct_fs", data)
            x = k + (j - 1) * 0.23
            ax.scatter(x + np.array((-0.035, 0, 0.035)), data, s=11,
                       facecolors=color, edgecolors="none", alpha=0.35, zorder=2)
            ax.errorbar(x, mean, yerr=sd, color=color, marker=marker,
                        markersize=5.2, markerfacecolor="white", markeredgewidth=1.2,
                        linewidth=1.2, capsize=3, elinewidth=1.15, zorder=4)

with DIAGNOSTICS.open(encoding="utf-8") as stream:
    diagnostics = json.load(stream)
diagnostic_index = {(row["dataset"], str(row["seed"])): row for row in diagnostics}
ax = axes[1, 1]
style(ax, "d", "Expert weights at α = 100")
ax.grid(False, axis="y")
ax.grid(axis="x", color=GRID, linewidth=0.55, alpha=0.8)
for i, dataset in enumerate(DATASETS):
    records = [diagnostic_index[(dataset, seed)] for seed in SEEDS]
    assert all(row["expert_order"] == list(EXPERTS) for row in records)
    weights = 100 * np.array([
        row["routing_mechanism"]["all_conditions"]["mean_expert_weights"]
        for row in records
    ])
    assert np.allclose(weights.sum(axis=1), 100, atol=1e-3)
    start = 0.0
    for j, (expert, color) in enumerate(zip(EXPERTS, EXPERT_COLORS)):
        mean, _sd = summary("d", dataset, DEFAULT, "all_conditions",
                            f"expert_weight_{expert}_percent", weights[:, j])
        ax.barh(i, mean, left=start, height=0.55, color=color,
                edgecolor="white", linewidth=0.65, zorder=3)
        ax.text(start + mean / 2, i, f"{mean:.1f}%", ha="center", va="center",
                fontsize=7.5, color=INK if j == 1 else "white", zorder=4)
        start += mean
ax.set_yticks(np.arange(len(DATASETS)), DATASETS, fontsize=7.5)
ax.tick_params(axis="y", length=0)
ax.set_ylim(2.65, -0.65)
ax.set_xlim(0, 100)
ax.set_xticks((0, 25, 50, 75, 100))
ax.set_xlabel("Mean expert weight (%)")
fig.legend(handles=[Patch(facecolor=color, label=label)
                    for color, label in zip(EXPERT_COLORS, EXPERT_LABELS)],
           loc="lower center", bbox_to_anchor=(0.798, 0.002), ncol=3,
           fontsize=7.5, handlelength=1.05, handletextpad=0.45, columnspacing=0.9)

stem = OUTPUT / "fig_alpha_prior_sensitivity"
fig.savefig(stem.with_suffix(".png"), dpi=450)
fig.savefig(stem.with_suffix(".pdf"))
fig.savefig(stem.with_suffix(".svg"))
plt.close(fig)

with (OUTPUT / "alpha_prior_sensitivity_plot_data.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
    writer.writeheader()
    writer.writerows(summaries)

caption = """# Routing-scale sensitivity and default expert composition

**Figure caption.** Frozen-model sensitivity of GeoPRR-Net to routing scale and
expert-weight composition at the default scale. **a**, Change in six-condition NMAE relative to α=100 with the default
prior (0.50, 0.25, 0.25), calculated within each matched model seed before
aggregation. **b**, Fraction of evaluated image–condition rows whose largest
expert weight exceeds 0.95. The dashed vertical lines mark α=100; the six tested
α values are displayed at equally spaced positions, with connecting lines used
only as visual guides. **c**, Paired NMAE changes from α=100 to α=200, shown
separately for all six conditions and the three projective conditions. **d**,
Mean weights of the base, polar-evidence, and relational-transport experts at
α=100, pooled over all six conditions within each seed and then averaged across
the same three seeds. Each bar sums to 100%; labels show percentages rounded
to one decimal place. The colors in a–c identify datasets; the local legend
below d identifies experts. Panel d displays composition means only;
individual seed weights and their sample SD are included in alpha_prior_sensitivity_plot_data.csv.
Independent component SD bars are not placed on cumulative stack boundaries.
Negative NMAE changes in a and c indicate lower error. Points and error bars in a–c show
the mean and sample standard deviation across the three model seeds
(20262020, 20262021, 20262022); the small points in c show individual paired
seed differences. These are descriptive seed standard deviations, not confidence
intervals. The reference difference at α=100 in a is zero by construction.
SyncG uses 4,000 images, RF100-VL 151 images, and Industrial-1395 1,395 images.
The corresponding six-condition denominators per seed are 24,000, 906, and
8,370 rows; projective-three denominators are 12,000, 453, and 4,185.

**中文阅读说明。** a：相对默认 α=100 的误差变化，纵轴越低越好；b：单个专家
权重大于0.95的评估行比例；c：把α从100增至200后，总体与透视三条件的误差
变化；d：固定α=100时，三个数据域的三专家平均权重组成，每根柱总计100%。
a–c的误差棒都是三个种子的样本标准差，c中的淡色小点是各个种子的配对差值。
d仅显示平均组成，各种子的权重和样本标准差保留在数据表中。扫描固定模型参数，仅调整推理
门控设置。图中的原始点估计不构成统计等效或硬路由优劣的结论。

**Sources.** `data/official_syncg_fulltrain_20260908/alpha_prior_sensitivity.csv`
for a–c; `data/official_syncg_fulltrain_20260908/geoprr_diagnostics.json`,
using `routing_mechanism.all_conditions.mean_expert_weights`, for d.
The sensitivity source contains 567 aggregate rows. The figure uses the all-conditions
and projective-three scopes without excluding images or seeds; the remaining
scopes are overlapping condition breakdowns retained in the original source.
`alpha_prior_sensitivity_plot_data.csv` records every displayed mean, sample SD, and contributing seed
value. Absolute NMAE values remain in the unmodified source table.
The uniform-prior comparison remains in the source table and is not displayed
in this figure. All nine dataset/seed diagnostic records are used for d.
"""
(OUTPUT / "alpha_prior_sensitivity_caption.md").write_text(caption, encoding="utf-8")
print(f"Exported {stem.name}.png/.pdf/.svg and {len(summaries)} plotted summaries.")
