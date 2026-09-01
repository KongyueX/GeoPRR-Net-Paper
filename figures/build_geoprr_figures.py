"""Build submission-grade figures for the GeoPRR-Net manuscript.

All quantitative panels are rendered from the released machine-readable data.
Primary Industrial-1395 transfer panels retain the complete prespecified
1,395-image cohort; the structured-reader comparison uses the released
five-fold OOF GeoPRR-Net aggregate for that domain.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle, Wedge
from matplotlib.ticker import FuncFormatter


HERE = Path(__file__).resolve().parent
FONT_BODY = 7.0
FONT_HEAD = 8.0

COLORS = {
    "ink": "#1D2A36",
    "muted": "#657482",
    "grid": "#D9E1E7",
    "paper": "#FFFFFF",
    "hero": "#0F4D92",
    "hero_soft": "#DCEAF7",
    "base": "#0F4D92",
    "base_soft": "#DCEAF7",
    "polar": "#D38B2C",
    "polar_soft": "#F8E8D1",
    "rel": "#168A82",
    "rel_soft": "#D9F0ED",
    "resnet": "#778492",
    "efficient": "#7563A8",
    "mobile": "#B17645",
    "warn": "#B94B45",
    "warn_soft": "#F6DFDC",
    "neutral_soft": "#EEF2F5",
    "baseline_dark": "#778492",
    "baseline_mid": "#9BA6B0",
    "baseline_light": "#BBC2C8",
}

METHOD_COLORS = {
    "GeoPRR-Net": COLORS["hero"],
    "Raw ResNet-18": COLORS["baseline_dark"],
    "Raw EfficientNet-B0": COLORS["baseline_mid"],
    "Raw MobileNetV3-Large": COLORS["baseline_light"],
}

SHORT_METHOD = {
    "GeoPRR-Net": "GeoPRR-Net",
    "Raw ResNet-18": "Raw ResNet-18",
    "Raw EfficientNet-B0": "Raw EfficientNet-B0",
    "Raw MobileNetV3-Large": "Raw MobileNetV3-L",
}

CANDIDATE_COLORS = [COLORS["base"], COLORS["polar"], COLORS["rel"]]
CANDIDATE_LABELS = ["Geometry/base", "Polar", "Relational"]

CONDITION_ORDER = [
    "clean",
    "blur_moderate",
    "blur_severe",
    "perspective_moderate",
    "perspective_severe",
    "combined_severe",
]

CONDITION_SHORT = {
    "Clean": "Clean",
    "Blur moderate": "Blur moderate",
    "Blur severe": "Blur severe",
    "Perspective moderate": "Perspective moderate",
    "Perspective severe": "Perspective severe",
    "Perspective severe + blur": "Perspective + blur",
    "Combined severe": "Perspective + blur",
}


def condition_color(label: str) -> str:
    """Use one visual vocabulary for clean, blur, and projective conditions."""
    if label.startswith("Blur"):
        return COLORS["polar"]
    if label.startswith("Perspective") or label.startswith("Combined"):
        return COLORS["rel"]
    return COLORS["ink"]


def style_condition_ticks(ax: plt.Axes, labels: list[str]) -> None:
    for tick, label in zip(ax.get_yticklabels(), labels):
        tick.set_color(condition_color(label))
        tick.set_fontweight("bold" if condition_color(label) != COLORS["ink"] else "normal")


def configure_style() -> None:
    """Set typography before any figure is instantiated."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
            "font.size": FONT_BODY,
            "axes.titlesize": FONT_HEAD,
            "axes.labelsize": FONT_BODY,
            "xtick.labelsize": FONT_BODY,
            "ytick.labelsize": FONT_BODY,
            "legend.fontsize": FONT_BODY,
            "axes.linewidth": 0.75,
            "axes.edgecolor": COLORS["ink"],
            "axes.labelcolor": COLORS["ink"],
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "text.color": COLORS["ink"],
            "grid.color": COLORS["grid"],
            "grid.linewidth": 0.6,
            "grid.alpha": 0.85,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
        }
    )


def read_csv(name: str) -> list[dict[str, str]]:
    with (HERE / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_data_csv(name: str) -> list[dict[str, str]]:
    with (HERE.parent / "data" / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_gzip_csv(relative_path: str) -> list[dict[str, str]]:
    """Read a released prediction ledger without creating an expanded copy."""
    path = HERE.parent / relative_path
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def seed_averaged_syncg_errors() -> list[tuple[str, str, str, float, float]]:
    """Return matched three-seed SyncG errors using the raw EfficientNet-B0 only."""
    expected_seeds = {"20262020", "20262021", "20262022"}
    geo: dict[tuple[str, str, str, str], float] = {}
    for row in read_gzip_csv("data/syncg/geoprr_predictions.csv.gz"):
        if row["variant"] != "full" or row["weight_variant"] != "ema":
            continue
        key = (row["seed"], row["scene_id"], row["image_id"], row["condition"])
        require(key not in geo, f"Duplicate GeoPRR-Net SyncG key: {key}")
        geo[key] = number(row, "absolute_error")

    raw: dict[tuple[str, str, str, str], float] = {}
    for row in read_gzip_csv("data/syncg/external_cnn_predictions.csv.gz"):
        if row["model"] != "EfficientNet-B0" or row["preprocessing"] != "raw":
            continue
        key = (row["seed"], row["scene_id"], row["image_id"], row["condition"])
        require(key not in raw, f"Duplicate Raw EfficientNet-B0 SyncG key: {key}")
        raw[key] = number(row, "absolute_error")

    require(len(geo) == len(raw) == 3 * 1558 * 6, "Unexpected SyncG matched-ledger row count")
    require(set(key[0] for key in geo) == expected_seeds, "Unexpected GeoPRR-Net SyncG seed roster")
    require(set(key[0] for key in raw) == expected_seeds, "Unexpected Raw EfficientNet-B0 SyncG seed roster")
    require(geo.keys() == raw.keys(), "SyncG ledgers are not exactly matched")

    units: dict[tuple[str, str, str], list[tuple[str, float, float]]] = defaultdict(list)
    for key in geo:
        seed, scene_id, image_id, condition = key
        units[(scene_id, image_id, condition)].append((seed, geo[key], raw[key]))

    averaged: list[tuple[str, str, str, float, float]] = []
    for (scene_id, image_id, condition), values in sorted(units.items()):
        require({value[0] for value in values} == expected_seeds, "A SyncG unit is missing a prescribed seed")
        averaged.append(
            (
                scene_id,
                image_id,
                condition,
                float(np.mean([value[1] for value in values])),
                float(np.mean([value[2] for value in values])),
            )
        )
    require(len(averaged) == 1558 * 6, "Unexpected seed-averaged SyncG unit count")
    errors = np.array([[row[3], row[4]] for row in averaged])
    require(bool(np.isfinite(errors).all()), "SyncG errors must be finite")
    require(bool((errors > 0).all()), "Log-scale SyncG errors must be strictly positive")
    return averaged


def seed_averaged_rf100_group_effects() -> list[tuple[str, float]]:
    """Return RF100 source-group effects against the raw EfficientNet-B0 only."""
    expected_seeds = {"20262020", "20262021", "20262022"}
    geo: dict[tuple[str, str, str, str], float] = {}
    raw: dict[tuple[str, str, str, str], float] = {}
    for row in read_gzip_csv("data/rf100/predictions.csv.gz"):
        if row["model"] not in {"GeoPRR-Net", "Raw EfficientNet-B0"}:
            continue
        key = (row["seed"], row["group_id"], row["image_id"], row["condition"])
        target = geo if row["model"] == "GeoPRR-Net" else raw
        require(key not in target, f"Duplicate RF100 key: {key}")
        target[key] = number(row, "absolute_error")
    require(len(geo) == len(raw) == 3 * 151 * 6, "Unexpected RF100 matched-ledger row count")
    require(geo.keys() == raw.keys(), "RF100 ledgers are not exactly matched")
    require(set(key[0] for key in geo) == expected_seeds, "Unexpected RF100 seed roster")

    units: dict[tuple[str, str, str], list[tuple[str, float]]] = defaultdict(list)
    for key in geo:
        seed, group_id, image_id, condition = key
        units[(group_id, image_id, condition)].append((seed, 100.0 * (geo[key] - raw[key])))
    group_values: dict[str, list[float]] = defaultdict(list)
    for (group_id, _, _), values in units.items():
        require({value[0] for value in values} == expected_seeds, "An RF100 unit is missing a prescribed seed")
        group_values[group_id].append(float(np.mean([value[1] for value in values])))
    effects = [(group_id, float(np.mean(values))) for group_id, values in sorted(group_values.items())]
    require(len(effects) == 35, "Expected 35 RF100 source groups")
    return effects


def seed_averaged_industrial_group_effects() -> list[tuple[str, float]]:
    """Return one unified Industrial-1395 cohort, grouped by acquisition cluster."""
    expected_seeds = {"20262020", "20262021", "20262022"}
    geo: dict[tuple[str, str], tuple[float, int]] = {}
    raw: dict[tuple[str, str], tuple[float, int]] = {}
    for row in read_gzip_csv("data/industrial1395/group_metrics.csv.gz"):
        if row["scope"] != "all_conditions" or row["method"] not in {"GeoPRR-Net", "Raw EfficientNet-B0"}:
            continue
        require(row["cohort"] == "industrial_1395", "Unexpected Industrial cohort label")
        require(row["cohort_name"] == "Industrial-1395", "Unexpected Industrial display label")
        require(row["cohort_images"] == "1395", "Unexpected Industrial image count")
        require(row["group_unit"] == "acquisition cluster", "Unexpected Industrial grouping unit")
        key = (row["seed"], row["group_id"])
        target = geo if row["method"] == "GeoPRR-Net" else raw
        require(key not in target, f"Duplicate Industrial group key: {key}")
        target[key] = (number(row, "nmae"), int(number(row, "rows")))
    require(geo.keys() == raw.keys(), "Industrial group ledgers are not exactly matched")
    require(set(key[0] for key in geo) == expected_seeds, "Unexpected Industrial seed roster")
    require(len(geo) == 3 * 52, "Expected 52 Industrial groups for each seed")

    per_seed_rows: dict[str, int] = defaultdict(int)
    group_values: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for key in geo:
        seed, group_id = key
        geo_nmae, geo_rows = geo[key]
        raw_nmae, raw_rows = raw[key]
        require(geo_rows == raw_rows, "Industrial group denominators differ")
        per_seed_rows[seed] += geo_rows
        group_values[group_id].append((seed, 100.0 * (geo_nmae - raw_nmae)))
    require(all(rows == 1395 * 6 for rows in per_seed_rows.values()), "Industrial seed denominator differs")

    effects: list[tuple[str, float]] = []
    for group_id, values in sorted(group_values.items()):
        require({value[0] for value in values} == expected_seeds, "An Industrial group is missing a prescribed seed")
        effects.append((group_id, float(np.mean([value[1] for value in values]))))
    require(len(effects) == 52, "Expected one unified 52-group Industrial cohort")
    return effects


def deterministic_jitter(ids: list[str], width: float = 0.18) -> np.ndarray:
    order = sorted(range(len(ids)), key=lambda index: hashlib.sha256(ids[index].encode("utf-8")).digest())
    slots = np.linspace(-width, width, len(ids), dtype=float)
    jitter = np.empty(len(ids), dtype=float)
    for slot, index in zip(slots, order):
        jitter[index] = slot
    return jitter


def read_json(name: str) -> dict[str, object]:
    with (HERE / name).open("r", encoding="utf-8-sig") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {name}")
    return value


def number(row: dict[str, str], key: str) -> float:
    return float(row[key])


def save_all(fig: plt.Figure, stem: str) -> None:
    """Export editable and submission-ready variants from one source figure."""
    fig.savefig(HERE / f"{stem}.svg", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(
        HERE / f"{stem}.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.03,
    )
    fig.savefig(
        HERE / f"{stem}.tiff",
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.03,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def save_png(fig: plt.Figure, stem: str) -> None:
    """Export only the PNG review asset without creating a PDF."""
    fig.savefig(
        HERE / f"{stem}.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)


def save_pdf_png(fig: plt.Figure, stem: str) -> None:
    """Export the two manuscript assets tracked by this repository."""
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(
        HERE / f"{stem}.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)


def panel_label(ax: plt.Axes, label: str, x: float = -0.08, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=FONT_HEAD,
        fontweight="bold",
        clip_on=False,
    )


def title_left(ax: plt.Axes, title: str) -> None:
    ax.set_title(title, loc="left", fontweight="bold", pad=5)


def takeaway(ax: plt.Axes, text: str, *, x: float = 0.98, y: float = 0.96, ha: str = "right") -> None:
    """Place one prominent, data-derived conclusion inside a panel."""
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha=ha,
        va="top",
        fontsize=FONT_HEAD,
        fontweight="bold",
        color=COLORS["hero"],
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": COLORS["hero_soft"],
            "edgecolor": COLORS["hero"],
            "linewidth": 0.7,
        },
        zorder=6,
    )


def quantitative_axis(ax: plt.Axes, *, grid_axis: str = "x") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, zorder=0)
    ax.set_axisbelow(True)


def add_value_labels(
    ax: plt.Axes,
    values: Iterable[float],
    positions: Iterable[float],
    *,
    fmt: str,
    offset: float,
    color: str = COLORS["ink"],
    x_values: Iterable[float] | None = None,
) -> None:
    values = list(values)
    positions = list(positions)
    anchors = values if x_values is None else list(x_values)
    for value, position, anchor in zip(values, positions, anchors):
        ax.text(
            anchor + offset,
            position,
            fmt.format(value),
            va="center",
            ha="left",
            fontsize=FONT_BODY,
            color=color,
        )


def rounded_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    *,
    face: str = "white",
    edge: str = COLORS["muted"],
    fontsize: float = FONT_BODY,
    weight: str = "normal",
    linewidth: float = 1.0,
    radius: float = 0.018,
) -> None:
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=weight,
        linespacing=1.08,
    )


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = COLORS["muted"],
    width: float = 1.0,
    style: str = "-|>",
    connection: str = "arc3,rad=0",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=8.5,
            linewidth=width,
            color=color,
            connectionstyle=connection,
            shrinkA=1.5,
            shrinkB=1.5,
        )
    )


def architecture_example_images() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return one public RF100-VL ROI and three explanatory view variants."""
    import cv2

    source = HERE / "assets" / "rf100_test_000000.png"
    image_bgr = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise FileNotFoundError(f"Architecture example is missing: {source}")
    clean = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    clean = cv2.resize(clean, (320, 320), interpolation=cv2.INTER_AREA)

    blurred = cv2.GaussianBlur(clean, (0, 0), sigmaX=5.2, sigmaY=5.2)
    height, width = clean.shape[:2]
    src = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    dst = np.float32(
        [
            [0.18 * width, 0.04 * height],
            [0.91 * width, 0.17 * height],
            [0.98 * width, 0.88 * height],
            [0.04 * width, 0.97 * height],
        ]
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    oblique = cv2.warpPerspective(
        clean,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(239, 243, 246),
    )

    support = np.any(oblique < 232, axis=2)
    ys, xs = np.where(support)
    if len(xs):
        margin = 7
        x0, x1 = max(int(xs.min()) - margin, 0), min(int(xs.max()) + margin + 1, width)
        y0, y1 = max(int(ys.min()) - margin, 0), min(int(ys.max()) + margin + 1, height)
        normalized = cv2.resize(oblique[y0:y1, x0:x1], (320, 320), interpolation=cv2.INTER_LINEAR)
    else:
        normalized = oblique.copy()
    return clean, blurred, oblique, normalized


def image_card(
    ax: plt.Axes,
    image: np.ndarray,
    x: float,
    title: str,
    cue: str,
    color: str,
) -> None:
    inset = ax.inset_axes([x, 0.20, 0.245, 0.58])
    inset.imshow(image)
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_color(color)
        spine.set_linewidth(1.4)
    ax.text(x + 0.1225, 0.84, title, ha="center", va="center", fontsize=FONT_HEAD, fontweight="bold", color=color)
    ax.text(x + 0.1225, 0.105, cue, ha="center", va="center", fontsize=FONT_BODY, color=COLORS["ink"], fontweight="bold")


def build_architecture(*, png_only: bool = False) -> None:
    clean, blurred, oblique, normalized = architecture_example_images()
    fig = plt.figure(figsize=(7.20, 4.70), layout="constrained")
    grid = fig.add_gridspec(2, 1, height_ratios=[1.55, 2.70], hspace=0.05)

    # Panel a: the application problem, expressed with minimal labels.
    ax = fig.add_subplot(grid[0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panel_label(ax, "a", 0.0, 1.005)
    ax.text(0.035, 1.005, "Capture conditions change which visual evidence remains trustworthy", ha="left", va="bottom", fontsize=FONT_HEAD, fontweight="bold")
    image_card(ax, clean, 0.055, "Frontal view", "geometry + pointer edges", COLORS["base"])
    image_card(ax, blurred, 0.378, "Motion blur", "global layout > local edges", COLORS["polar"])
    image_card(ax, oblique, 0.701, "Oblique view", "cross-view relations > raw coordinates", COLORS["rel"])

    # Panel b: a clean left-to-right evidence-routing architecture.
    ax2 = fig.add_subplot(grid[1])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    panel_label(ax2, "b", 0.0, 1.005)
    ax2.text(0.035, 1.005, "GeoPRR-Net routes complementary evidence instead of committing to one representation", ha="left", va="bottom", fontsize=FONT_HEAD, fontweight="bold")

    rounded_box(ax2, (0.015, 0.19), 0.13, 0.63, "", face="#F7F9FB", edge=COLORS["grid"], linewidth=1.0)
    ax2.text(0.080, 0.775, "DUAL VIEWS", ha="center", fontsize=FONT_HEAD, fontweight="bold", color=COLORS["hero"])
    raw_ax = ax2.inset_axes([0.034, 0.545, 0.092, 0.18])
    raw_ax.imshow(oblique)
    raw_ax.set_xticks([])
    raw_ax.set_yticks([])
    for spine in raw_ax.spines.values():
        spine.set_color(COLORS["base"])
        spine.set_linewidth(1.1)
    ax2.text(0.080, 0.510, "raw ROI", ha="center", fontsize=FONT_BODY, fontweight="bold")

    norm_ax = ax2.inset_axes([0.034, 0.275, 0.092, 0.18])
    norm_ax.imshow(normalized)
    norm_ax.set_xticks([])
    norm_ax.set_yticks([])
    for spine in norm_ax.spines.values():
        spine.set_color(COLORS["rel"])
        spine.set_linewidth(1.1)
    ax2.text(0.080, 0.240, "normalized ROI", ha="center", fontsize=FONT_BODY, fontweight="bold")

    rounded_box(ax2, (0.18, 0.31), 0.13, 0.42, "", face="#EDF3FA", edge=COLORS["hero"], linewidth=1.25)
    ax2.text(0.245, 0.675, "SHARED\nENCODER", ha="center", va="top", fontsize=FONT_HEAD, fontweight="bold", color=COLORS["hero"], linespacing=0.95)
    ax2.text(0.245, 0.565, "EfficientNet-B0", ha="center", fontsize=FONT_BODY, fontweight="bold")
    for offset, alpha in ((0.0, 0.95), (0.012, 0.65), (0.024, 0.38)):
        ax2.add_patch(Rectangle((0.205 + offset, 0.455 + offset), 0.072, 0.070, facecolor=COLORS["hero_soft"], edgecolor=COLORS["hero"], linewidth=0.7, alpha=alpha))
    arrow(ax2, (0.145, 0.635), (0.18, 0.595), color=COLORS["base"])
    arrow(ax2, (0.145, 0.365), (0.18, 0.435), color=COLORS["rel"])

    branch_x, branch_w = 0.365, 0.245
    branches = [
        (0.65, "GEOMETRY / BASE", "p⁰  →  μG", COLORS["base_soft"], COLORS["base"]),
        (0.42, "POLAR", "q(θ)  →  μP", COLORS["polar_soft"], COLORS["polar"]),
        (0.19, "RELATIONAL", "Δz, H, M  →  μR", COLORS["rel_soft"], COLORS["rel"]),
    ]
    for y, head, outcome, face, edge in branches:
        rounded_box(ax2, (branch_x, y), branch_w, 0.15, "", face=face, edge=edge, linewidth=1.05)
        ax2.text(branch_x + 0.014, y + 0.103, head, ha="left", va="center", fontsize=FONT_HEAD, fontweight="bold", color=edge)
        ax2.text(branch_x + 0.014, y + 0.045, outcome, ha="left", va="center", fontsize=FONT_BODY, fontweight="bold", color=edge)

    for gx in (0.532, 0.546, 0.560):
        ax2.plot([gx, gx], [0.714, 0.770], color=COLORS["base"], linewidth=0.55, alpha=0.75)
    for gy in (0.723, 0.741, 0.759):
        ax2.plot([0.520, 0.574], [gy, gy], color=COLORS["base"], linewidth=0.55, alpha=0.75)
    ax2.add_patch(Wedge((0.550, 0.492), 0.030, 20, 330, width=0.009, facecolor=COLORS["polar"], edgecolor="none", alpha=0.9))
    ax2.plot([0.550, 0.573], [0.492, 0.515], color=COLORS["polar"], linewidth=1.1)
    heat = np.array([[0.1, 0.5, 0.2, 0.8], [0.7, 0.2, 0.9, 0.3], [0.3, 0.8, 0.4, 0.6]])
    heat_ax = ax2.inset_axes([0.532, 0.240, 0.038, 0.055])
    heat_ax.imshow(heat, cmap="GnBu", vmin=0, vmax=1, aspect="auto")
    heat_ax.axis("off")
    for y, color in ((0.725, COLORS["base"]), (0.495, COLORS["polar"]), (0.265, COLORS["rel"])):
        arrow(ax2, (0.31, 0.52), (branch_x, y), color=color)

    rounded_box(ax2, (0.665, 0.30), 0.13, 0.44, "", face="#F3F0FA", edge=COLORS["efficient"], linewidth=1.2)
    ax2.text(0.730, 0.690, "CONDITIONAL\nROUTER", ha="center", va="top", fontsize=FONT_HEAD, fontweight="bold", color=COLORS["efficient"], linespacing=0.95)
    triangle = Polygon([[0.688, 0.420], [0.772, 0.420], [0.730, 0.580]], closed=True, facecolor="white", edgecolor=COLORS["efficient"], linewidth=1.0)
    ax2.add_patch(triangle)
    ax2.add_patch(Circle((0.730, 0.495), 0.013, facecolor=COLORS["efficient"], edgecolor="white", linewidth=0.5))
    ax2.text(0.730, 0.355, "μ* = Σⱼ wⱼμⱼ", ha="center", fontsize=FONT_BODY, fontweight="bold")
    for y, color in ((0.725, COLORS["base"]), (0.495, COLORS["polar"]), (0.265, COLORS["rel"])):
        arrow(ax2, (branch_x + branch_w, y), (0.665, 0.52), color=color)

    rounded_box(ax2, (0.835, 0.33), 0.15, 0.41, "", face="#EAF4F8", edge=COLORS["hero"], linewidth=1.2)
    ax2.text(0.910, 0.690, "MOMENT\nPROJECTION", ha="center", va="top", fontsize=FONT_HEAD, fontweight="bold", color=COLORS["hero"], linespacing=0.95)
    curve_ax = ax2.inset_axes([0.855, 0.460, 0.111, 0.145])
    bins = np.linspace(0, 1, 128)
    base_curve = np.exp(-0.5 * ((bins - 0.43) / 0.12) ** 2)
    final_curve = np.exp(-0.5 * ((bins - 0.57) / 0.105) ** 2)
    curve_ax.plot(bins, base_curve / base_curve.max(), color=COLORS["muted"], linewidth=0.9, linestyle="--")
    curve_ax.plot(bins, final_curve / final_curve.max(), color=COLORS["hero"], linewidth=1.3)
    curve_ax.axvline(0.57, color=COLORS["warn"], linewidth=0.8)
    curve_ax.set_xlim(0, 1)
    curve_ax.set_ylim(0, 1.08)
    curve_ax.axis("off")
    ax2.text(0.910, 0.395, "E[p*] = μ*", ha="center", fontsize=FONT_BODY, fontweight="bold", color=COLORS["hero"])
    arrow(ax2, (0.795, 0.52), (0.835, 0.52), color=COLORS["hero"], width=1.2)

    rounded_box(
        ax2,
        (0.850, 0.16),
        0.12,
        0.10,
        "NORMALIZED\nPROGRESS",
        face=COLORS["hero"],
        edge=COLORS["hero"],
        fontsize=FONT_HEAD,
        weight="bold",
    )
    ax2.texts[-1].set_color("white")
    arrow(ax2, (0.910, 0.33), (0.910, 0.26), color=COLORS["hero"])

    if png_only:
        save_png(fig, "fig1_geoprr_architecture")
    else:
        save_all(fig, "fig1_geoprr_architecture")


def build_syncg(*, png_only: bool = False) -> None:
    rows = read_csv("syncg_all_models_conditions.csv")
    pooled_rows = read_csv("syncg_external.csv")
    methods = ["GeoPRR-Net", "Raw ResNet-18", "Raw EfficientNet-B0", "Raw MobileNetV3-Large"]
    lookup = {(row["method"], row["condition"]): row for row in rows}
    pooled_lookup = {row["method"]: row for row in pooled_rows}
    condition_labels = ["Clean", "Blur-M", "Blur-S", "Persp.-M", "Persp.-S", "Persp. + blur"]
    nmae = np.array(
        [[100 * number(lookup[(method, condition)], "nmae_mean") for condition in CONDITION_ORDER] for method in methods]
    )
    nmae_sd = np.array(
        [[100 * number(lookup[(method, condition)], "nmae_sd") for condition in CONDITION_ORDER] for method in methods]
    )

    x = np.arange(len(CONDITION_ORDER), dtype=float)
    syncg_colors = {
        "GeoPRR-Net": "#0B5EA8",
        "Raw ResNet-18": "#7E8B96",
        "Raw EfficientNet-B0": "#C8892B",
        "Raw MobileNetV3-Large": "#947DB4",
    }
    syncg_markers = {"GeoPRR-Net": "D", "Raw ResNet-18": "o", "Raw EfficientNet-B0": "o", "Raw MobileNetV3-Large": "o"}
    display_names = {
        "GeoPRR-Net": "GeoPRR-Net",
        "Raw ResNet-18": "Raw ResNet-18",
        "Raw EfficientNet-B0": "Raw EfficientNet-B0",
        "Raw MobileNetV3-Large": "Raw MobileNetV3-L",
    }

    distribution_rows = seed_averaged_syncg_errors()

    fig = plt.figure(figsize=(7.20, 7.25), layout="constrained")
    grid = fig.add_gridspec(3, 2, width_ratios=[1.64, 1.0], height_ratios=[1.32, 1.0, 0.92])
    ax = fig.add_subplot(grid[0, :])
    ax2 = fig.add_subplot(grid[1, 0])
    ax3 = fig.add_subplot(grid[1, 1])
    ax4 = fig.add_subplot(grid[2, :])

    # Panel a: one dominant six-condition trajectory establishes the separation.
    best_raw_nmae = nmae[1:].min(axis=0)
    ax.fill_between(
        x[3:],
        nmae[0, 3:],
        best_raw_nmae[3:],
        color=COLORS["hero_soft"],
        alpha=0.78,
        zorder=1,
    )
    for row_index, method in enumerate(methods[1:] + methods[:1]):
        source_index = methods.index(method)
        is_geo = method == "GeoPRR-Net"
        ax.errorbar(
            x,
            nmae[source_index],
            yerr=nmae_sd[source_index],
            color=syncg_colors[method],
            linestyle="-",
            linewidth=2.35 if is_geo else 1.35,
            marker=syncg_markers[method],
            markersize=5.8 if is_geo else 4.2,
            markerfacecolor=syncg_colors[method],
            markeredgecolor=COLORS["paper"] if is_geo else syncg_colors[method],
            markeredgewidth=0.85 if is_geo else 0.6,
            capsize=2.1,
            elinewidth=1.0 if is_geo else 0.8,
            label=display_names[method],
            zorder=6 if is_geo else 3 + row_index,
        )
    ax.set_xticks(x, condition_labels)
    ax.set_xlim(-0.25, 5.25)
    nmae_upper = float(np.max(nmae + nmae_sd))
    axis_upper = max(3.05, 0.5 * np.ceil(2.0 * (nmae_upper + 0.15)))
    ax.set_ylim(0.65, axis_upper)
    ax.set_ylabel("NMAE (%FS)")
    title_left(ax, "GeoPRR-Net separates from raw CNNs as projective severity increases")
    panel_label(ax, "a", -0.055, 1.03)
    quantitative_axis(ax, grid_axis="y")
    ax.legend(
        loc="upper left",
        ncol=4,
        columnspacing=1.0,
        handlelength=1.7,
        borderaxespad=0.35,
    )

    # Panel b: all comparator-by-condition reductions plus a pooled six-condition column.
    baselines = methods[1:]
    pooled_geo = number(pooled_lookup["GeoPRR-Net"], "nmae_mean")
    reduction_matrix = np.array(
        [
            [number(lookup[(method, condition)], "geo_reduction_percent") for condition in CONDITION_ORDER]
            + [100.0 * (number(pooled_lookup[method], "nmae_mean") - pooled_geo) / number(pooled_lookup[method], "nmae_mean")]
            for method in baselines
        ]
    )
    reduction_cmap = LinearSegmentedColormap.from_list(
        "geoprr_reduction",
        ["#F2F6F9", "#C9DEEC", "#7EAFD3", "#2E75B6", "#0B5EA8"],
    )
    reduction_upper = max(65.0, 10.0 * np.ceil(float(np.max(reduction_matrix)) / 10.0))
    image = ax2.imshow(
        reduction_matrix,
        cmap=reduction_cmap,
        vmin=0,
        vmax=reduction_upper,
        aspect="auto",
        interpolation="nearest",
    )
    heatmap_labels = condition_labels + ["All six"]
    ax2.set_xticks(np.arange(len(heatmap_labels)), heatmap_labels)
    ax2.set_yticks(np.arange(len(baselines)), [display_names[method] for method in baselines])
    for tick, label in zip(ax2.get_xticklabels(), heatmap_labels):
        if label == "All six":
            color = COLORS["hero"]
        elif label.startswith("Blur"):
            color = COLORS["polar"]
        elif label.startswith("Persp"):
            color = COLORS["rel"]
        else:
            color = COLORS["ink"]
        tick.set_color(color)
        tick.set_fontweight("bold" if color != COLORS["ink"] else "normal")
        tick.set_rotation(28)
        tick.set_rotation_mode("anchor")
        tick.set_ha("right")
    ax2.set_xticks(np.arange(-0.5, len(heatmap_labels), 1), minor=True)
    ax2.set_yticks(np.arange(-0.5, len(baselines), 1), minor=True)
    ax2.grid(which="minor", color=COLORS["paper"], linewidth=0.9)
    ax2.tick_params(which="both", length=0)
    ax2.axvline(2.5, color=COLORS["rel"], linewidth=1.0)
    ax2.add_patch(Rectangle((5.5, -0.5), 1.0, len(baselines), fill=False, edgecolor=COLORS["hero"], linewidth=1.35))
    for row_index in range(reduction_matrix.shape[0]):
        for column_index in range(reduction_matrix.shape[1]):
            value = reduction_matrix[row_index, column_index]
            ax2.text(
                column_index,
                row_index,
                f"{value:.0f}%",
                ha="center",
                va="center",
                fontsize=FONT_BODY,
                fontweight="bold" if column_index >= 3 else "normal",
                color=COLORS["paper"] if value >= 28 else COLORS["ink"],
            )
    title_left(ax2, "Condition-specific and pooled reduction versus each comparator")
    panel_label(ax2, "b", -0.09, 1.03)
    colorbar = fig.colorbar(image, ax=ax2, orientation="horizontal", fraction=0.08, pad=0.10, aspect=30)
    colorbar.set_ticks(np.arange(0.0, reduction_upper + 0.1, 20.0))
    colorbar.set_label("GeoPRR-Net relative NMAE reduction (%)")
    colorbar.outline.set_visible(False)

    # Panel c: matched-condition gaps against all raw CNNs retain the full comparison.
    y = np.arange(len(CONDITION_ORDER))[::-1].astype(float)
    baseline_offsets = {
        "Raw ResNet-18": 0.16,
        "Raw EfficientNet-B0": 0.0,
        "Raw MobileNetV3-Large": -0.16,
    }
    baseline_markers = {
        "Raw ResNet-18": "o",
        "Raw EfficientNet-B0": "s",
        "Raw MobileNetV3-Large": "^",
    }
    for comparator in baselines:
        comparator_index = methods.index(comparator)
        positions = y + baseline_offsets[comparator]
        for yy, baseline_y, geo_value, comparator_value in zip(y, positions, nmae[0], nmae[comparator_index]):
            ax3.plot(
                [geo_value, comparator_value],
                [yy, baseline_y],
                color=syncg_colors[comparator],
                linewidth=1.45,
                alpha=0.22,
                solid_capstyle="round",
                zorder=1,
            )
        ax3.errorbar(
            nmae[comparator_index],
            positions,
            xerr=nmae_sd[comparator_index],
            fmt=baseline_markers[comparator],
            color=syncg_colors[comparator],
            ecolor=syncg_colors[comparator],
            markerfacecolor=COLORS["paper"],
            markeredgewidth=1.0,
            markersize=4.3,
            capsize=1.8,
            linewidth=0.9,
            label=display_names[comparator],
            zorder=3,
        )
    ax3.errorbar(
        nmae[0],
        y,
        xerr=nmae_sd[0],
        fmt="D",
        color=syncg_colors["GeoPRR-Net"],
        ecolor=syncg_colors["GeoPRR-Net"],
        markeredgecolor=COLORS["paper"],
        markeredgewidth=0.75,
        markersize=5.4,
        capsize=2.1,
        linewidth=1.0,
        label="GeoPRR-Net",
        zorder=4,
    )
    ax3.set_yticks(y, condition_labels)
    for tick, condition in zip(ax3.get_yticklabels(), CONDITION_ORDER):
        label_text = lookup[("GeoPRR-Net", condition)]["label"]
        tick.set_color(condition_color(label_text))
        tick.set_fontweight("bold" if condition_color(label_text) != COLORS["ink"] else "normal")
    ax3.set_xlim(0.65, axis_upper)
    ax3.set_ylim(-0.45, 5.45)
    ax3.set_xlabel("NMAE (%FS; lower is better)")
    title_left(ax3, "Matched gaps to every raw CNN")
    panel_label(ax3, "c", -0.16, 1.03)
    quantitative_axis(ax3, grid_axis="x")
    ax3.legend(loc="upper right", ncol=1, labelspacing=0.35, handletextpad=0.5)

    # Panel d: the full matched error distribution exposes tail behavior.
    n_units = len(distribution_rows)
    quantiles = np.arange(n_units, dtype=float) / float(n_units - 1)
    geo_errors = 100.0 * np.sort(np.array([row[3] for row in distribution_rows]))
    raw_errors = 100.0 * np.sort(np.array([row[4] for row in distribution_rows]))
    geo_p95 = float(np.quantile(geo_errors, 0.95))
    raw_p95 = float(np.quantile(raw_errors, 0.95))
    ax4.axvspan(0.95, 1.0, color="#F7E7E4", zorder=0)
    ax4.plot(quantiles, raw_errors, color="#8C98A4", linewidth=1.55, label="Raw EfficientNet-B0", zorder=2)
    ax4.plot(quantiles, geo_errors, color=COLORS["hero"], linewidth=2.25, label="GeoPRR-Net", zorder=3)
    ax4.axvline(0.95, color="#C78378", linewidth=0.8, linestyle=(0, (3, 2)), zorder=1)
    ax4.set_yscale("log")
    ax4.set_xlim(0.0, 1.0)
    ax4.set_ylim(0.01, 100.0)
    ax4.set_xticks([0.0, 0.25, 0.50, 0.75, 1.0])
    ax4.set_yticks([0.01, 0.1, 1.0, 10.0, 100.0])
    ax4.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax4.set_xlabel("Absolute-error quantile")
    ax4.set_ylabel("Absolute error (%FS; log scale)")
    title_left(ax4, "The full matched distribution retains a wide upper-tail margin")
    panel_label(ax4, "d", -0.055, 1.03)
    quantitative_axis(ax4, grid_axis="y")
    ax4.legend(loc="upper left", bbox_to_anchor=(0.015, 0.985), ncol=2, columnspacing=1.2, handlelength=2.4)
    print(
        "Figure 2d caption statistics: "
        f"n={n_units}; GeoPRR P95={geo_p95:.6f}%FS; Raw EfficientNet-B0 P95={raw_p95:.6f}%FS"
    )

    if png_only:
        save_png(fig, "fig2_syncg_performance")
    else:
        save_all(fig, "fig2_syncg_performance")


def stacked_candidate_bars(
    ax: plt.Axes,
    rows: list[dict[str, str]],
    statistic: str,
    title: str,
    label: str,
    *,
    show_names: bool = False,
) -> None:
    selected = [row for row in rows if row["statistic"] == statistic]
    scopes = [row["scope"] for row in selected]
    y = np.arange(len(scopes))[::-1]
    left = np.zeros(len(selected))
    for key, color, candidate in zip(("base", "polar", "relational"), CANDIDATE_COLORS, CANDIDATE_LABELS):
        values = np.array([number(row, key) for row in selected])
        ax.barh(y, values, left=left, height=0.52, color=color, edgecolor="white", linewidth=0.5, label=candidate, zorder=3)
        for index, (yy, start, value) in enumerate(zip(y, left, values)):
            if value >= 0.10:
                short_name = {"Geometry/base": "Base", "Polar": "Polar", "Relational": "Relational"}[candidate]
                text = f"{short_name}\n{value:.2f}" if show_names and index == 0 else f"{value:.2f}"
                ax.text(start + value / 2, yy, text, ha="center", va="center", fontsize=FONT_BODY, color="white", fontweight="bold", linespacing=1.0)
        left += values
    ax.set_yticks(y, scopes)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Fraction")
    title_left(ax, title)
    panel_label(ax, label)
    quantitative_axis(ax)


def build_ablation_routing(*, png_only: bool = False) -> None:
    factorial = read_csv("../data/figure3/geometry_routing_summary.csv")
    interaction = read_json("../data/figure3/geometry_routing_interaction.json")
    ablation = read_csv("ablation.csv")
    condition_effects = read_csv("ablation_condition_effects.csv")
    routing = read_csv("routing_conditions.csv")
    perspective = read_csv("../data/figure3/perspective_scan_summary.csv")
    variant_order = ["no_geometry_fusion", "fixed_routing", "no_relational_transport", "no_polar_evidence"]
    factorial_by_variant = {row["variant"]: row for row in factorial}
    ablation_by_variant = {row["variant"]: row for row in ablation}

    fig = plt.figure(figsize=(7.20, 8.35), layout="constrained")
    grid = fig.add_gridspec(3, 2, height_ratios=[0.92, 0.82, 1.06])
    ax = fig.add_subplot(grid[0, 0])
    ax2 = fig.add_subplot(grid[0, 1])
    ax3 = fig.add_subplot(grid[1, :])
    ax4 = fig.add_subplot(grid[2, 0])
    ax5 = fig.add_subplot(grid[2, 1])

    # Panel a: the complete Geometry x Routing factorial.
    route_x = np.array([0.0, 1.0])
    factorial_series = [
        (
            "Geometry on",
            [factorial_by_variant["fixed_routing"], factorial_by_variant["full"]],
            COLORS["hero"],
            "o",
        ),
        (
            "Geometry off",
            [
                factorial_by_variant["no_geometry_fixed_routing"],
                factorial_by_variant["no_geometry_fusion"],
            ],
            COLORS["warn"],
            "s",
        ),
    ]
    for label, rows, color, marker in factorial_series:
        values = 100 * np.array([number(row, "seed_nmae_mean") for row in rows])
        errors = 100 * np.array([number(row, "seed_nmae_sd") for row in rows])
        ax.errorbar(
            route_x,
            values,
            yerr=errors,
            color=color,
            marker=marker,
            markersize=5.8,
            linewidth=1.7,
            capsize=2.5,
            label=label,
            zorder=3,
        )
        for xx, value in zip(route_x, values):
            ax.text(
                xx,
                value + 0.035,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=FONT_BODY,
                color=color,
                fontweight="bold",
            )
    bootstrap = interaction["scene_cluster_bootstrap"]
    if not isinstance(bootstrap, dict):
        raise ValueError("invalid Figure 3 interaction bootstrap object")
    interaction_mean = 100 * float(interaction["seed_mean"])
    interaction_low = 100 * float(bootstrap["ci_95_lower"])
    interaction_high = 100 * float(bootstrap["ci_95_upper"])
    ax.text(
        0.04,
        0.06,
        f"Interaction I = {interaction_mean:+.4f}%FS\n95% CI [{interaction_low:+.4f}, {interaction_high:+.4f}]",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=FONT_BODY,
        color=COLORS["ink"],
        bbox={
            "boxstyle": "round,pad=0.28",
            "facecolor": COLORS["neutral_soft"],
            "edgecolor": COLORS["muted"],
            "linewidth": 0.65,
        },
    )
    ax.set_xticks(route_x, ["Fixed routing", "Adaptive routing"])
    ax.set_xlim(-0.18, 1.18)
    ax.set_ylim(0.88, 1.75)
    ax.set_ylabel("NMAE (%FS; lower is better)")
    title_left(ax, "Geometry × routing factorial")
    panel_label(ax, "a", -0.10, 1.03)
    quantitative_axis(ax, grid_axis="y")
    ax.legend(loc="upper right")

    # Panel b: pooled effects retain the relational and polar interventions.
    overall_rows = [ablation_by_variant[variant] for variant in variant_order]
    overall_labels = [
        "No geometry-aware fusion",
        "Fixed routing",
        "No relational transport",
        "No polar evidence",
    ]
    penalties = 100 * np.array([number(row, "penalty") for row in overall_rows])
    lows = 100 * np.array(
        [number(row, "penalty_ci_low") for row in overall_rows]
    )
    highs = 100 * np.array(
        [number(row, "penalty_ci_high") for row in overall_rows]
    )
    overall_y = np.arange(len(overall_labels))[::-1]
    overall_colors = [
        COLORS["warn"],
        COLORS["efficient"],
        COLORS["rel"],
        COLORS["polar"],
    ]
    ax2.axvline(0, color=COLORS["ink"], linewidth=0.8, zorder=1)
    for yy, value, low, high, color in zip(
        overall_y,
        penalties,
        lows,
        highs,
        overall_colors,
    ):
        ax2.errorbar(
            value,
            yy,
            xerr=[[value - low], [high - value]],
            fmt="o",
            color=color,
            ecolor=color,
            markersize=5.7,
            capsize=3,
            linewidth=1.4,
            zorder=3,
        )
        ax2.text(
            high + 0.013,
            yy,
            f"+{value:.4f}",
            va="center",
            fontsize=FONT_BODY,
            color=color,
            fontweight="bold",
        )
    ax2.set_yticks(overall_y, overall_labels)
    ax2.set_xlim(-0.015, 0.59)
    ax2.set_xlabel("Ablation − full NMAE (%FS; positive is worse)")
    title_left(ax2, "Overall ablation effects")
    panel_label(ax2, "b", -0.08, 1.03)
    quantitative_axis(ax2)

    # Panel c: condition localization across all four individual interventions.
    effect_lookup = {
        (row["variant"], row["condition"]): row for row in condition_effects
    }
    heat = np.array(
        [
            [
                100 * number(
                    effect_lookup[(variant, condition)], "penalty_mean"
                )
                for condition in CONDITION_ORDER
            ]
            for variant in variant_order
        ]
    )
    condition_labels = [
        "Clean",
        "Blur M",
        "Blur S",
        "Persp. M",
        "Persp. S",
        "Persp. + blur",
    ]
    heat_labels = ["No geometry", "Fixed routing", "No relational", "No polar"]
    penalty_cmap = LinearSegmentedColormap.from_list(
        "geoprr_penalty",
        [COLORS["hero_soft"], COLORS["paper"], COLORS["warn_soft"], COLORS["warn"]],
    )
    norm = TwoSlopeNorm(vmin=-0.04, vcenter=0.0, vmax=1.35)
    ax3.imshow(
        heat,
        cmap=penalty_cmap,
        norm=norm,
        aspect="auto",
        interpolation="nearest",
    )
    ax3.axvline(2.5, color=COLORS["ink"], linewidth=1.0)
    ax3.set_xticks(
        np.arange(len(condition_labels)),
        condition_labels,
        rotation=24,
        ha="right",
        rotation_mode="anchor",
    )
    for tick, label in zip(ax3.get_xticklabels(), condition_labels):
        tick.set_color(condition_color(label))
        tick.set_fontweight("bold" if condition_color(label) != COLORS["ink"] else "normal")
    ax3.set_yticks(np.arange(len(heat_labels)), heat_labels)
    for row_index in range(heat.shape[0]):
        for column_index in range(heat.shape[1]):
            value = heat[row_index, column_index]
            display = "0.000" if abs(value) < 0.0005 else f"{value:+.3f}"
            ax3.text(
                column_index,
                row_index,
                display,
                ha="center",
                va="center",
                fontsize=FONT_BODY,
                fontweight="bold",
                color="white" if value > 0.7 else COLORS["ink"],
            )
    ax3.set_xlabel("Ablation − full NMAE (%FS)")
    title_left(ax3, "Where each component matters")
    panel_label(ax3, "c", -0.045, 1.03)
    ax3.spines[:].set_color(COLORS["ink"])

    # Panel d: retain the original prespecified-seed routing mechanism view.
    ordered_routing = [
        next(row for row in routing if row["condition"] == condition)
        for condition in CONDITION_ORDER
    ]
    routing_labels = [
        CONDITION_SHORT[row["label"]] for row in ordered_routing
    ]
    routing_y = np.arange(len(ordered_routing))[::-1]
    left = np.zeros(len(ordered_routing))
    for key, color, candidate in zip(
        ("base", "polar", "relational"),
        CANDIDATE_COLORS,
        CANDIDATE_LABELS,
    ):
        values = np.array([number(row, key) for row in ordered_routing])
        ax4.barh(
            routing_y,
            values,
            left=left,
            height=0.58,
            color=color,
            edgecolor="white",
            linewidth=0.45,
            label=candidate,
            zorder=3,
        )
        for yy, start, value in zip(routing_y, left, values):
            if value >= 0.16:
                ax4.text(
                    start + value / 2,
                    yy,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=FONT_BODY,
                    color="white",
                    fontweight="bold",
                )
        left += values
    ax4.set_yticks(routing_y, routing_labels)
    style_condition_ticks(ax4, routing_labels)
    ax4.set_xlim(0, 1)
    ax4.set_xlabel("Mean routing weight")
    title_left(ax4, "Router shifts evidence by condition")
    panel_label(ax4, "d", -0.10, 1.03)
    quantitative_axis(ax4)
    ax4.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=3,
        columnspacing=0.8,
        handlelength=1.3,
    )

    # Panel e: complete angle scan, including the 60-degree collapse to fallback.
    angles = np.array([0, 15, 25, 35, 45, 60], dtype=float)
    perspective_specs = [
        ("Full GeoPRR", "GeoPRR-Net", COLORS["hero"], "o"),
        ("Without geometry-aware fusion", "No geometry", COLORS["warn"], "s"),
        ("Raw EfficientNet-B0", "Raw EfficientNet-B0", COLORS["baseline_dark"], "^"),
    ]
    perspective_by_model_angle = {
        (row["model"], int(row["angle"])): row for row in perspective
    }
    fallback_rows = [
        perspective_by_model_angle[("Full GeoPRR", int(angle))]
        for angle in angles
    ]
    fallback_rate = 100 * np.array(
        [number(row, "identity_fallback_rate") for row in fallback_rows]
    )
    ax5b = ax5.twinx()
    ax5b.bar(
        angles,
        fallback_rate,
        width=6.0,
        color=COLORS["neutral_soft"],
        edgecolor=COLORS["grid"],
        linewidth=0.6,
        alpha=0.78,
        zorder=0,
    )
    ax5b.set_ylim(0, 112)
    ax5b.set_yticks([0, 50, 100])
    ax5b.set_ylabel("Identity fallback (%)", color=COLORS["muted"])
    ax5b.tick_params(axis="y", colors=COLORS["muted"])
    ax5b.spines["top"].set_visible(False)
    ax5b.spines["right"].set_color(COLORS["grid"])
    ax5b.grid(False)
    ax5.set_zorder(ax5b.get_zorder() + 1)
    ax5.patch.set_visible(False)
    for model, label, color, marker in perspective_specs:
        rows = [perspective_by_model_angle[(model, int(angle))] for angle in angles]
        values = 100 * np.array([number(row, "seed_nmae_mean") for row in rows])
        errors = 100 * np.array([number(row, "seed_nmae_sd") for row in rows])
        ax5.errorbar(
            angles,
            values,
            yerr=errors,
            color=color,
            marker=marker,
            markersize=4.7,
            linewidth=1.55,
            capsize=2.0,
            label=label,
            zorder=4,
        )
    ax5.set_yscale("log", base=2)
    ax5.set_yticks(
        [0.8, 1, 2, 4, 8, 16],
        ["0.8", "1", "2", "4", "8", "16"],
    )
    ax5.set_ylim(0.70, 16)
    ax5.set_xlim(-4, 64)
    ax5.set_xticks(angles, [f"{int(angle)}°" for angle in angles])
    ax5.set_xlabel("Perspective angle")
    ax5.set_ylabel("NMAE (%FS; base-2 log scale)")
    title_left(ax5, "Angle stress test and identity fallback")
    panel_label(ax5, "e", -0.10, 1.03)
    quantitative_axis(ax5, grid_axis="y")
    ax5.legend(loc="upper left", ncol=1, handlelength=1.8)
    fig.suptitle(
        "Geometry and conditional routing jointly stabilize projective views",
        fontsize=FONT_HEAD,
        fontweight="bold",
    )
    if png_only:
        save_png(fig, "fig3_ablation_routing")
    else:
        save_pdf_png(fig, "fig3_ablation_routing")


def build_industrial(*, png_only: bool = False) -> None:
    industrial = read_csv("industrial.csv")
    condition_rows = read_csv("industrial_condition_comparison.csv")
    methods = [row["method"] for row in industrial]
    y = np.arange(len(methods))[::-1]
    colors = [METHOD_COLORS[m] for m in methods]

    fig, axes = plt.subplots(1, 3, figsize=(7.20, 4.12), gridspec_kw={"width_ratios": [0.93, 0.93, 1.38]}, layout="constrained")
    ax, ax2, ax3 = axes

    nmae = 100 * np.array([number(row, "nmae_mean") for row in industrial])
    nmae_sd = 100 * np.array([number(row, "nmae_sd") for row in industrial])
    ax.barh(y, nmae, xerr=nmae_sd, color=colors, height=0.60, edgecolor="white", linewidth=0.4, capsize=2.2, zorder=3)
    ax.set_yticks(y, [SHORT_METHOD[m] for m in methods])
    ax.set_xlim(0, 28)
    ax.set_xlabel("NMAE (%FS; lower is better)")
    title_left(ax, "Complete-cohort error")
    panel_label(ax, "a")
    quantitative_axis(ax)
    add_value_labels(ax, nmae, y, fmt="{:.2f}", offset=0.4, x_values=nmae + nmae_sd)
    best_baseline = np.min(nmae[1:])
    relative_gain = 100 * (best_baseline - nmae[0]) / best_baseline
    ax.text(0.5, y[0] + 0.34, f"{relative_gain:.1f}% lower", ha="left", va="bottom", fontsize=FONT_HEAD, fontweight="bold", color=COLORS["hero"], zorder=6)

    acc2 = np.array([number(row, "acc2_mean") for row in industrial])
    acc2_sd = np.array([number(row, "acc2_sd") for row in industrial])
    ax2.barh(y, 100 * acc2, xerr=100 * acc2_sd, color=colors, height=0.60, edgecolor="white", linewidth=0.4, capsize=2.2, zorder=3)
    ax2.set_yticks(y, [SHORT_METHOD[m] for m in methods])
    ax2.set_xlim(0, 24.5)
    ax2.set_xlabel("Acc@2% (%; higher is better)")
    title_left(ax2, "Complete-cohort threshold accuracy")
    panel_label(ax2, "b")
    quantitative_axis(ax2)
    add_value_labels(ax2, 100 * acc2, y, fmt="{:.1f}%", offset=0.35, x_values=100 * (acc2 + acc2_sd))
    best_baseline_acc = np.max(acc2[1:])
    accuracy_gain = 100 * (acc2[0] - best_baseline_acc)
    ax2.text(50 * acc2[0], y[0], f"+{accuracy_gain:.2f} pp", ha="center", va="center", fontsize=FONT_HEAD, fontweight="bold", color="white", zorder=6)

    labels = [CONDITION_SHORT[row["label"]] for row in condition_rows]
    deltas = 100 * np.array([number(row, "delta_nmae") for row in condition_rows])
    lows = 100 * np.array([number(row, "ci_low") for row in condition_rows])
    highs = 100 * np.array([number(row, "ci_high") for row in condition_rows])
    reductions = np.array([number(row, "relative_reduction_percent") for row in condition_rows])
    py = np.arange(len(condition_rows))[::-1]
    ax3.axhspan(-0.5, 2.5, color=COLORS["rel_soft"], alpha=0.68, zorder=0)
    ax3.axvline(0, color=COLORS["ink"], linewidth=0.8, zorder=1)
    for yy, value, low, high, label in zip(py, deltas, lows, highs, labels):
        projective = label.startswith("Perspective")
        color = COLORS["hero"] if projective else condition_color(label)
        ax3.errorbar(
            value,
            yy,
            xerr=[[value - low], [high - value]],
            fmt="o",
            color=color,
            ecolor=color,
            markerfacecolor=color if projective else COLORS["paper"],
            markeredgewidth=1.1,
            markersize=5.2,
            capsize=2.8,
            linewidth=1.3,
            zorder=3,
        )
    ax3.set_yticks(py, labels)
    style_condition_ticks(ax3, labels)
    ax3.set_xlim(-10.8, 0.95)
    ax3.set_xlabel("GeoPRR-Net − EfficientNet-B0 NMAE (%FS)")
    title_left(ax3, "Field advantage by condition")
    panel_label(ax3, "c")
    quantitative_axis(ax3)

    fig.suptitle(
        f"Industrial-1395: the {relative_gain:.1f}% pooled gain is driven by 10.4–39.8% projective gains",
        fontsize=FONT_HEAD,
        fontweight="bold",
    )
    if png_only:
        save_png(fig, "fig4_industrial_1395")
    else:
        save_all(fig, "fig4_industrial_1395")


def build_rf100(*, png_only: bool = False) -> None:
    """Plot the public RF100-VL pooled transfer summary."""
    rows = read_csv("rf100_external.csv")
    methods = [row["method"] for row in rows]
    colors = [METHOD_COLORS[method] for method in methods]
    labels = [SHORT_METHOD[method] for method in methods]
    y = np.arange(len(rows))[::-1]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.20, 3.48),
        gridspec_kw={"width_ratios": [1.0, 1.0]},
        layout="constrained",
    )
    ax, ax2 = axes

    nmae = 100 * np.array([number(row, "nmae_mean") for row in rows])
    nmae_sd = 100 * np.array([number(row, "nmae_sd") for row in rows])
    ax.barh(
        y,
        nmae,
        xerr=nmae_sd,
        color=colors,
        height=0.60,
        edgecolor="white",
        linewidth=0.4,
        capsize=2.2,
        zorder=3,
    )
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 11.8)
    ax.set_xlabel("NMAE (%FS; lower is better)")
    title_left(ax, "Pooled six-condition error")
    panel_label(ax, "a", -0.09, 1.02)
    quantitative_axis(ax)
    add_value_labels(ax, nmae, y, fmt="{:.2f}", offset=0.18, x_values=nmae + nmae_sd)
    best_baseline = np.min(nmae[1:])
    relative_gain = 100 * (best_baseline - nmae[0]) / best_baseline
    ax.text(0.2, y[0] + 0.34, f"{relative_gain:.1f}% lower", ha="left", va="bottom", fontsize=FONT_HEAD, fontweight="bold", color=COLORS["hero"], zorder=6)

    acc2 = 100 * np.array([number(row, "acc2_mean") for row in rows])
    acc2_sd = 100 * np.array([number(row, "acc2_sd") for row in rows])
    ax2.barh(
        y,
        acc2,
        xerr=acc2_sd,
        color=colors,
        height=0.60,
        edgecolor="white",
        linewidth=0.4,
        capsize=2.2,
        zorder=3,
    )
    ax2.set_yticks(y, labels)
    ax2.set_xlim(0, 59.5)
    ax2.set_xlabel("Acc@2% (%; higher is better)")
    title_left(ax2, "Pooled threshold accuracy")
    panel_label(ax2, "b", -0.09, 1.02)
    quantitative_axis(ax2)
    add_value_labels(ax2, acc2, y, fmt="{:.1f}%", offset=0.8, x_values=acc2 + acc2_sd)
    best_baseline_acc = np.max(acc2[1:])
    accuracy_gain = acc2[0] - best_baseline_acc
    ax2.text(1.0, y[0] + 0.34, f"+{accuracy_gain:.2f} pp", ha="left", va="bottom", fontsize=FONT_HEAD, fontweight="bold", color=COLORS["hero"], zorder=6)

    fig.suptitle(
        f"RF100-VL: {relative_gain:.1f}% lower error and +{accuracy_gain:.2f}-point Acc@2%",
        fontsize=FONT_HEAD,
        fontweight="bold",
    )
    if png_only:
        save_png(fig, "fig5_rf100_transfer")
    else:
        save_all(fig, "fig5_rf100_transfer")


def build_cross_domain(*, png_only: bool = False) -> None:
    """Summarize paired error and threshold gains across all three main cohorts."""
    dataset_labels = ["SyncG", "Industrial-1395", "RF100-VL"]
    baseline_methods = ["Raw ResNet-18", "Raw EfficientNet-B0", "Raw MobileNetV3-Large"]
    metric_rows = {
        "SyncG": read_csv("syncg_external.csv"),
        "Industrial-1395": read_csv("industrial.csv"),
        "RF100-VL": read_csv("rf100_external.csv"),
    }
    metric_lookup = {
        dataset: {row["method"]: row for row in rows}
        for dataset, rows in metric_rows.items()
    }
    paired_lookup = {
        "SyncG": {row["comparator"]: row for row in read_csv("paired_syncg.csv")},
        "Industrial-1395": {row["comparator"]: row for row in read_csv("paired_industrial.csv")},
        "RF100-VL": {
            row["comparison"].removeprefix("GeoPRR-Net minus "): row
            for row in read_csv("paired_rf100.csv")
        },
    }
    n_images = {
        "SyncG": int(number(read_csv("syncg_all_models_conditions.csv")[0], "rows")),
        "Industrial-1395": int(number(metric_rows["Industrial-1395"][0], "n_images")),
        "RF100-VL": int(number(read_csv("rf100_condition_effects.csv")[0], "rows")),
    }
    dataset_colors = {
        "SyncG": "#0B5EA8",
        "Industrial-1395": COLORS["rel"],
        "RF100-VL": COLORS["polar"],
    }
    dataset_fills = {
        "SyncG": COLORS["hero_soft"],
        "Industrial-1395": COLORS["rel_soft"],
        "RF100-VL": COLORS["polar_soft"],
    }
    baseline_colors = {
        "Raw ResNet-18": "#7E8B96",
        "Raw EfficientNet-B0": "#C8892B",
        "Raw MobileNetV3-Large": "#947DB4",
    }
    baseline_markers = {"Raw ResNet-18": "o", "Raw EfficientNet-B0": "s", "Raw MobileNetV3-Large": "^"}
    baseline_labels = {
        "Raw ResNet-18": "Raw ResNet-18",
        "Raw EfficientNet-B0": "Raw EfficientNet-B0",
        "Raw MobileNetV3-Large": "Raw MobileNetV3-L",
    }

    reductions: dict[tuple[str, str], tuple[float, float, float]] = {}
    for dataset in dataset_labels:
        for method in baseline_methods:
            row = paired_lookup[dataset][method]
            delta_key = "delta" if "delta" in row else "delta_nmae"
            baseline = number(metric_lookup[dataset][method], "nmae_mean")
            if baseline <= 0:
                raise ValueError(f"NMAE baseline must be positive for {dataset}: {method}")
            delta = number(row, delta_key)
            ci_low = number(row, "ci_low")
            ci_high = number(row, "ci_high")
            reductions[(dataset, method)] = (
                -100.0 * delta / baseline,
                -100.0 * ci_high / baseline,
                -100.0 * ci_low / baseline,
            )

    syncg_rows = seed_averaged_syncg_errors()
    syncg_group_values: dict[str, list[float]] = defaultdict(list)
    for scene_id, _, _, geo_error, raw_error in syncg_rows:
        syncg_group_values[scene_id].append(100.0 * (geo_error - raw_error))
    syncg_effects = [(group_id, float(np.mean(values))) for group_id, values in sorted(syncg_group_values.items())]
    require(len(syncg_effects) == 14, "Expected 14 held-out SyncG scenes")
    industrial_effects = seed_averaged_industrial_group_effects()
    rf100_effects = seed_averaged_rf100_group_effects()

    fig = plt.figure(figsize=(7.20, 6.15), layout="constrained")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.36, 1.0], height_ratios=[1.0, 0.92])
    ax = fig.add_subplot(grid[0, 0])
    ax2 = fig.add_subplot(grid[0, 1])
    ax3 = fig.add_subplot(grid[1, :])

    # Panel a: paired reductions against every raw comparator in every cohort.
    base_y = np.arange(len(dataset_labels))[::-1].astype(float)
    offsets = {"Raw ResNet-18": 0.18, "Raw EfficientNet-B0": 0.0, "Raw MobileNetV3-Large": -0.18}
    for yy, dataset in zip(base_y, dataset_labels):
        ax.axhspan(yy - 0.48, yy + 0.48, color=dataset_fills[dataset], alpha=0.62, zorder=0)
    for method in baseline_methods:
        values = np.array([reductions[(dataset, method)][0] for dataset in dataset_labels])
        lows = np.array([reductions[(dataset, method)][1] for dataset in dataset_labels])
        highs = np.array([reductions[(dataset, method)][2] for dataset in dataset_labels])
        positions = base_y + offsets[method]
        ax.errorbar(
            values,
            positions,
            xerr=np.vstack([values - lows, highs - values]),
            fmt=baseline_markers[method],
            color=baseline_colors[method],
            ecolor=baseline_colors[method],
            markerfacecolor=COLORS["paper"],
            markeredgewidth=1.05,
            markersize=5.0,
            capsize=2.2,
            linewidth=1.05,
            label=baseline_labels[method],
            zorder=3,
        )
        for value, yy in zip(values, positions):
            ax.text(value + 1.15, yy, f"{value:.1f}%", ha="left", va="center", fontsize=FONT_BODY, color=COLORS["ink"])
    ax.set_yticks(base_y, dataset_labels)
    for tick, dataset in zip(ax.get_yticklabels(), dataset_labels):
        tick.set_color(dataset_colors[dataset])
        tick.set_fontweight("bold")
    ax.set_xlim(0, 80)
    ax.set_ylim(-0.52, 2.52)
    ax.set_xlabel("GeoPRR-Net NMAE reduction (%)")
    title_left(ax, "Paired reductions against every raw CNN")
    panel_label(ax, "a", -0.12, 1.03)
    quantitative_axis(ax)
    ax.legend(loc="upper left", bbox_to_anchor=(0.015, 0.985), ncol=1, labelspacing=0.38, handletextpad=0.5)

    # Panel b: two primary metrics against the strongest raw comparator in each cohort.
    point_offsets = {
        "SyncG": (0.0, 0.8),
        "Industrial-1395": (0.0, -1.25),
        "RF100-VL": (0.0, 1.15),
    }
    for dataset in dataset_labels:
        dataset_metrics = metric_lookup[dataset]
        best_nmae_method = min(baseline_methods, key=lambda method: number(dataset_metrics[method], "nmae_mean"))
        best_acc_method = max(baseline_methods, key=lambda method: number(dataset_metrics[method], "acc2_mean"))
        reduction, low, high = reductions[(dataset, best_nmae_method)]
        acc_gain = 100.0 * (
            number(dataset_metrics["GeoPRR-Net"], "acc2_mean")
            - number(dataset_metrics[best_acc_method], "acc2_mean")
        )
        color = dataset_colors[dataset]
        ax2.plot([0, reduction], [acc_gain, acc_gain], color=color, linewidth=0.8, alpha=0.20, zorder=0)
        ax2.plot([reduction, reduction], [0, acc_gain], color=color, linewidth=0.8, alpha=0.20, zorder=0)
        ax2.errorbar(
            reduction,
            acc_gain,
            xerr=[[reduction - low], [high - reduction]],
            fmt="none",
            ecolor=color,
            capsize=2.4,
            linewidth=1.15,
            zorder=2,
        )
        size = 70.0 + 0.11 * n_images[dataset]
        ax2.scatter(
            reduction,
            acc_gain,
            s=size,
            color=color,
            edgecolor=COLORS["paper"],
            linewidth=0.9,
            zorder=3,
        )
        dx, dy = point_offsets[dataset]
        ax2.text(
            reduction + dx,
            acc_gain + dy,
            f"{dataset}\n{n_images[dataset]:,} images",
            ha="center",
            va="bottom" if dy >= 0 else "top",
            fontsize=FONT_BODY,
            fontweight="bold",
            color=color,
            linespacing=1.0,
            zorder=4,
        )
    ax2.set_xlim(0, 70)
    ax2.set_ylim(0, 21)
    ax2.set_xlabel("NMAE reduction vs best raw CNN (%)")
    ax2.set_ylabel("Acc@2% gain vs best raw CNN (pp)")
    title_left(ax2, "Both metrics improve across domains")
    panel_label(ax2, "b", -0.14, 1.03)
    quantitative_axis(ax2, grid_axis="both")

    # Panel c: group-level effects show the distribution beneath pooled gains.
    group_panels = [
        ("SyncG", syncg_effects),
        ("Industrial-1395", industrial_effects),
        ("RF100-VL", rf100_effects),
    ]
    ax3.axhline(0.0, color=COLORS["muted"], linewidth=0.9, linestyle=(0, (4, 2)), zorder=1)
    for x_position, (dataset, effects) in enumerate(group_panels):
        ids = [group_id for group_id, _ in effects]
        values = np.array([value for _, value in effects])
        jitter = deterministic_jitter(ids)
        ax3.scatter(
            np.full(len(values), x_position, dtype=float) + jitter,
            values,
            s=25,
            color=dataset_colors[dataset],
            alpha=0.82,
            edgecolor=COLORS["paper"],
            linewidth=0.55,
            zorder=3,
        )
        median = float(np.median(values))
        ax3.plot(
            [x_position - 0.27, x_position + 0.27],
            [median, median],
            color=COLORS["ink"],
            linewidth=2.3,
            solid_capstyle="butt",
            zorder=4,
        )
        print(
            "Figure 8c caption statistics: "
            f"{dataset} n={len(values)}; groups_below_zero={int((values < 0).sum())}; "
            f"median={median:.6f}%FS; range=[{float(values.min()):.6f}, {float(values.max()):.6f}]%FS"
        )
    ax3.set_xticks(np.arange(len(group_panels)), [dataset for dataset, _ in group_panels])
    for tick, dataset in zip(ax3.get_xticklabels(), dataset_labels):
        tick.set_color(dataset_colors[dataset])
        tick.set_fontweight("bold")
    ax3.set_xlim(-0.55, len(group_panels) - 0.45)
    ax3.set_ylim(-10.1, 4.4)
    ax3.set_yticks([-10, -8, -6, -4, -2, 0, 2, 4])
    ax3.set_ylabel("Per-group six-condition ΔNMAE (%FS)\nGeoPRR-Net − Raw EfficientNet-B0")
    title_left(ax3, "Group-level effects reveal the boundary beneath pooled gains")
    panel_label(ax3, "c", -0.055, 1.03)
    quantitative_axis(ax3, grid_axis="y")

    fig.suptitle(
        "Cross-domain consistency: lower error and higher near-exact accuracy on every cohort",
        fontsize=FONT_HEAD,
        fontweight="bold",
    )
    if png_only:
        save_png(fig, "fig7_cross_domain_summary")
    else:
        save_all(fig, "fig7_cross_domain_summary")


def build_efficiency(*, png_only: bool = False) -> None:
    rows = read_csv("efficiency.csv")
    methods = [row["method"] for row in rows]
    colors = [METHOD_COLORS[m] for m in methods]
    short = [SHORT_METHOD[m] for m in methods]

    fig = plt.figure(figsize=(7.20, 4.05), layout="constrained")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.36, 1.0], height_ratios=[1, 1])
    ax = fig.add_subplot(grid[:, 0])
    ax2 = fig.add_subplot(grid[0, 1])
    ax3 = fig.add_subplot(grid[1, 1])

    latency = np.array([number(row, "p50_ms") for row in rows])
    p95 = np.array([number(row, "p95_ms") for row in rows])
    nmae = 100 * np.array([number(row, "nmae_mean") for row in rows])
    nmae_sd = 100 * np.array([number(row, "nmae_sd") for row in rows])
    params = np.array([number(row, "parameters") / 1e6 for row in rows])
    if np.any(latency <= 0) or np.any(p95 <= 0):
        raise ValueError("Latency values must be positive.")
    marker_size = 48 + params * 8.0
    for i, (method, x, x95, yy, sd, color, size) in enumerate(zip(methods, latency, p95, nmae, nmae_sd, colors, marker_size)):
        ax.plot([x, x95], [yy, yy], color=color, linewidth=1.3, alpha=0.75, zorder=2)
        ax.errorbar(x, yy, yerr=sd, fmt="o", markersize=np.sqrt(size), color=color, ecolor=color, capsize=2.3, linewidth=1.1, markeredgecolor="white", markeredgewidth=0.7, zorder=3)
        offsets = {
            "GeoPRR-Net": (-6, 7),
            "Raw ResNet-18": (5, 8),
            "Raw EfficientNet-B0": (5, -12),
            "Raw MobileNetV3-Large": (5, 8),
        }
        label_color = COLORS["hero"] if method == "GeoPRR-Net" else COLORS["ink"]
        ax.annotate(SHORT_METHOD[method].replace("Raw ", ""), (x, yy), xytext=offsets[method], textcoords="offset points", fontsize=FONT_BODY, color=label_color, fontweight="bold" if method == "GeoPRR-Net" else "normal")
    ax.set_xlim(0, 45)
    ax.set_ylim(0.7, 3.2)
    ax.set_xlabel("P50 latency (ms; segment extends to P95)")
    ax.set_ylabel("SyncG NMAE (%FS; lower is better)")
    title_left(ax, "Accuracy–latency trade-off")
    panel_label(ax, "a")
    quantitative_axis(ax, grid_axis="both")
    ax.annotate("preferred direction", xy=(3.05, 0.80), xytext=(6.5, 1.14), fontsize=FONT_BODY, color=COLORS["hero"], arrowprops={"arrowstyle": "->", "color": COLORS["hero"], "lw": 0.9})
    size_legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=COLORS["muted"], markersize=np.sqrt(48 + p * 8), label=f"{p:.0f} M params")
        for p in (4, 8, 12)
    ]
    ax.legend(handles=size_legend, loc="upper right", title="Marker area", title_fontsize=FONT_BODY, handletextpad=0.7)

    y = np.arange(len(rows))[::-1]
    ax2.barh(y, params, color=colors, height=0.58, edgecolor="white", linewidth=0.4, zorder=3)
    ax2.set_yticks(y, short)
    ax2.set_xlim(0, 12.8)
    ax2.set_xlabel("Active parameters (million)")
    title_left(ax2, "Parameter footprint")
    panel_label(ax2, "b")
    quantitative_axis(ax2)
    add_value_labels(ax2, params, y, fmt="{:.2f}", offset=0.22)

    memory = np.array([number(row, "peak_allocated_mib") for row in rows])
    ax3.barh(y, memory, color=colors, height=0.58, edgecolor="white", linewidth=0.4, zorder=3)
    ax3.set_yticks(y, short)
    ax3.set_xlim(0, 70)
    ax3.set_xlabel("Peak allocated memory (MiB)")
    title_left(ax3, "Matched GPU memory")
    panel_label(ax3, "c")
    quantitative_axis(ax3)
    add_value_labels(ax3, memory, y, fmt="{:.1f}", offset=1.2)

    fig.suptitle("4.89 M parameters, 26.3 images/s, and the lowest SyncG error", fontsize=FONT_HEAD, fontweight="bold")
    if png_only:
        save_png(fig, "fig6_efficiency")
    else:
        save_all(fig, "fig6_efficiency")


def structured_reader_summary() -> tuple[
    list[str],
    list[str],
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Return the validated 3-domain by 4-reader metric tensors."""
    rows = read_data_csv("roi_geometry_comparison_three_seed.csv")
    domains = ["SyncG Scene-Holdout", "Industrial-1395", "RF100-VL"]
    methods = ["GeoPRR-Net", "VDN", "DeepLabV3+-ROI", "YOLO11s-Pose-4KP"]
    indexed = {(row["domain"], row["method"]): row for row in rows}
    require(len(rows) == len(indexed) == 12, "The reader comparison must contain a complete 3 x 4 matrix.")
    require(set(indexed) == {(domain, method) for domain in domains for method in methods}, "The reader comparison matrix is incomplete.")
    require(all(row["seeds"] == "20262020|20262021|20262022" for row in rows), "Unexpected seed roster.")

    adapted_path = HERE.parent / "data" / "industrial1395" / "supervised_feature_head_ensemble_per_sample.json"
    with adapted_path.open("r", encoding="utf-8") as stream:
        adapted = json.load(stream)
    require(adapted["status"] == "complete", "Industrial adapted GeoPRR result is incomplete.")
    require(adapted["rows"] == 8370 and adapted["groups"] == 52, "Industrial adapted roster differs.")
    adapted_pooled = adapted["summary"]["adapted_equal_weight_ensemble"]["pooled"]
    frozen_seed = adapted["summary"]["frozen_single_seed"]["nmae"]
    frozen_row = indexed[("Industrial-1395", "GeoPRR-Net")]
    require(
        np.isclose(number(frozen_row, "nmae_mean"), float(frozen_seed["mean"]), atol=1e-6),
        "Industrial frozen GeoPRR summaries disagree.",
    )

    shape = (len(domains), len(methods))
    nmae = np.zeros(shape, dtype=float)
    nmae_sd = np.zeros(shape, dtype=float)
    acc5 = np.zeros(shape, dtype=float)
    acc5_sd = np.zeros(shape, dtype=float)
    coverage = np.zeros(shape, dtype=float)
    coverage_sd = np.zeros(shape, dtype=float)
    for domain_index, domain in enumerate(domains):
        for method_index, method in enumerate(methods):
            row = indexed[(domain, method)]
            if domain == "Industrial-1395" and method == "GeoPRR-Net":
                nmae[domain_index, method_index] = 100.0 * float(adapted_pooled["nmae"])
                acc5[domain_index, method_index] = 100.0 * float(adapted_pooled["acc_at_5pct"])
                coverage[domain_index, method_index] = 100.0
            else:
                nmae[domain_index, method_index] = 100.0 * number(row, "nmae_mean")
                nmae_sd[domain_index, method_index] = 100.0 * number(row, "nmae_sample_sd")
                acc5[domain_index, method_index] = 100.0 * number(row, "acc_at_5_mean")
                acc5_sd[domain_index, method_index] = 100.0 * number(row, "acc_at_5_sample_sd")
                coverage[domain_index, method_index] = 100.0 * number(row, "coverage_mean")
                coverage_sd[domain_index, method_index] = 100.0 * number(row, "coverage_sample_sd")

    for values, label in (
        (nmae, "NMAE"),
        (nmae_sd, "NMAE SD"),
        (acc5, "Acc@5"),
        (acc5_sd, "Acc@5 SD"),
        (coverage, "coverage"),
        (coverage_sd, "coverage SD"),
    ):
        require(bool(np.isfinite(values).all()), f"Non-finite structured-reader {label}.")
        require(bool((values >= 0).all()), f"Negative structured-reader {label}.")
    require(bool((nmae[:, [0]] < nmae[:, 1:]).all()), "GeoPRR-Net must have the lowest NMAE in every domain.")
    require(bool((acc5[:, [0]] > acc5[:, 1:]).all()), "GeoPRR-Net must have the highest Acc@5 in every domain.")
    require(bool(np.allclose(coverage[:, 0], 100.0)), "GeoPRR-Net coverage must be complete.")
    return domains, methods, nmae, nmae_sd, acc5, acc5_sd, coverage, coverage_sd


def build_vdn(*, png_only: bool = False) -> None:
    """Plot absolute NMAE and Acc@5 for the complete reader matrix."""
    domains, methods, nmae, nmae_sd, acc5, acc5_sd, _, _ = structured_reader_summary()
    labels = {
        "GeoPRR-Net": "GeoPRR-Net",
        "VDN": "VDN",
        "DeepLabV3+-ROI": "DeepLab\nROI",
        "YOLO11s-Pose-4KP": "YOLO-Pose\n4KP",
    }
    colors = {
        "GeoPRR-Net": COLORS["hero"],
        "VDN": COLORS["baseline_dark"],
        "DeepLabV3+-ROI": COLORS["rel"],
        "YOLO11s-Pose-4KP": COLORS["polar"],
    }
    panel_titles = ["SyncG scene holdout", "Industrial-1395", "RF100-VL"]

    fig = plt.figure(figsize=(7.20, 5.55), layout="constrained")
    grid = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.0])
    axes = np.asarray([[fig.add_subplot(grid[row, column]) for column in range(3)] for row in range(2)])
    xpos = np.arange(len(methods))
    method_colors = [colors[method] for method in methods]

    for domain_index, (domain, title) in enumerate(zip(domains, panel_titles)):
        nmae_ax = axes[0, domain_index]
        nmae_ax.bar(
            xpos,
            nmae[domain_index],
            yerr=nmae_sd[domain_index],
            capsize=2.6,
            color=method_colors,
            width=0.64,
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        nmae_upper = float(np.max(nmae[domain_index] + nmae_sd[domain_index]))
        nmae_ylim = nmae_upper * 1.24
        nmae_ax.set_ylim(0, nmae_ylim)
        nmae_ax.set_xticks(xpos, [])
        nmae_ax.set_ylabel("Pooled NMAE (%FS)" if domain_index == 0 else "NMAE (%FS)")
        title_left(nmae_ax, title)
        panel_label(nmae_ax, chr(ord("a") + domain_index), -0.14, 1.03)
        quantitative_axis(nmae_ax, grid_axis="y")
        for x, value, sd, method in zip(xpos, nmae[domain_index], nmae_sd[domain_index], methods):
            nmae_ax.text(
                x,
                value + sd + 0.021 * nmae_ylim,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=FONT_BODY,
                fontweight="bold" if method == "GeoPRR-Net" else "normal",
                color=COLORS["hero"] if method == "GeoPRR-Net" else COLORS["ink"],
            )

        acc_ax = axes[1, domain_index]
        acc_ax.bar(
            xpos,
            acc5[domain_index],
            yerr=acc5_sd[domain_index],
            capsize=2.6,
            color=method_colors,
            width=0.64,
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        acc_ax.set_ylim(0, 110)
        acc_ax.set_xticks(xpos, [labels[method] for method in methods])
        acc_ax.set_ylabel("Acc@5 (%)" if domain_index == 0 else "Acc@5 (%)")
        panel_label(acc_ax, chr(ord("d") + domain_index), -0.14, 1.03)
        quantitative_axis(acc_ax, grid_axis="y")
        for x, value, sd, method in zip(xpos, acc5[domain_index], acc5_sd[domain_index], methods):
            acc_ax.text(
                x,
                min(value + sd + 2.0, 107.0),
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=FONT_BODY,
                fontweight="bold" if method == "GeoPRR-Net" else "normal",
                color=COLORS["hero"] if method == "GeoPRR-Net" else COLORS["ink"],
            )

    fig.suptitle(
        "GeoPRR-Net combines lower pooled error with higher Acc@5 across three domains",
        fontsize=FONT_HEAD,
        fontweight="bold",
    )
    if png_only:
        save_png(fig, "fig6_vdn_comparison")
    else:
        save_pdf_png(fig, "fig6_vdn_comparison")


def build_reader_advantage(*, png_only: bool = False) -> None:
    """Plot effect-size and valid-output maps for the complete reader matrix."""
    domains, methods, nmae, _, acc5, _, coverage, _ = structured_reader_summary()
    domain_labels = ["SyncG", "Industrial-1395", "RF100-VL"]
    comparator_labels = ["VDN", "DeepLab", "YOLO-Pose"]
    method_labels = ["GeoPRR", "VDN", "DLV3+", "YOLO-Pose"]

    reductions = 100.0 * (nmae[:, 1:] - nmae[:, [0]]) / nmae[:, 1:]
    acc5_gains = acc5[:, [0]] - acc5[:, 1:]
    require(bool((reductions > 0).all()), "Every relative NMAE reduction must be positive.")
    require(bool((acc5_gains > 0).all()), "Every Acc@5 gain must be positive.")

    fig = plt.figure(figsize=(7.20, 3.35), layout="constrained")
    grid = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.18])
    axes = [fig.add_subplot(grid[0, index]) for index in range(3)]
    matrices = [reductions, acc5_gains, coverage]
    xlabels = [comparator_labels, comparator_labels, method_labels]
    titles = ["Relative NMAE reduction", "Acc@5 gain", "Valid-output coverage"]
    colorbar_labels = ["Reduction (%)", "Gain (percentage points)", "Coverage (%)"]
    vmax_values = [100.0, 60.0, 100.0]
    cmaps = [
        LinearSegmentedColormap.from_list("reader_reduction", ["#F2F6F9", "#A9CBE2", "#4E8FC2", "#0F4D92"]),
        LinearSegmentedColormap.from_list("reader_acc_gain", ["#F1F8F7", "#A7D9D3", "#4BB3A8", "#168A82"]),
        LinearSegmentedColormap.from_list("reader_coverage", ["#F6F3FA", "#C8BCE0", "#8A75B5", "#5D478F"]),
    ]

    for panel_index, (ax, matrix, labels, title, cbar_label, vmax, cmap) in enumerate(
        zip(axes, matrices, xlabels, titles, colorbar_labels, vmax_values, cmaps)
    ):
        image = ax.imshow(
            matrix,
            cmap=cmap,
            vmin=0,
            vmax=vmax,
            aspect="auto",
            interpolation="nearest",
        )
        ax.set_xticks(np.arange(len(labels)), labels)
        ax.set_yticks(np.arange(len(domains)), domain_labels)
        ax.set_xticks(np.arange(-0.5, len(labels), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(domains), 1), minor=True)
        ax.grid(which="minor", color=COLORS["paper"], linewidth=1.1)
        ax.tick_params(which="both", length=0)
        title_left(ax, title)
        panel_label(ax, chr(ord("a") + panel_index), -0.15, 1.03)
        for row_index in range(matrix.shape[0]):
            for column_index in range(matrix.shape[1]):
                value = float(matrix[row_index, column_index])
                if panel_index == 0:
                    label = f"{value:.1f}%"
                elif panel_index == 1:
                    label = f"+{value:.1f}"
                else:
                    label = f"{value:.1f}%"
                ax.text(
                    column_index,
                    row_index,
                    label,
                    ha="center",
                    va="center",
                    fontsize=FONT_BODY,
                    fontweight="bold" if (panel_index < 2 or column_index == 0) else "normal",
                    color=COLORS["paper"] if value / vmax >= 0.58 else COLORS["ink"],
                )
        if panel_index == 2:
            ax.add_patch(
                Rectangle(
                    (-0.5, -0.5),
                    1.0,
                    len(domains),
                    fill=False,
                    edgecolor=COLORS["hero"],
                    linewidth=1.5,
                )
            )
        colorbar = fig.colorbar(image, ax=ax, orientation="horizontal", fraction=0.075, pad=0.12, aspect=24)
        colorbar.set_label(cbar_label)
        colorbar.outline.set_visible(False)

    fig.suptitle(
        "GeoPRR-Net delivers consistent effect-size gains with complete output coverage",
        fontsize=FONT_HEAD,
        fontweight="bold",
    )
    if png_only:
        save_png(fig, "fig7_reader_advantage")
    else:
        save_pdf_png(fig, "fig7_reader_advantage")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--figure",
        choices=(
            "all",
            "architecture",
            "syncg",
            "ablation",
            "industrial",
            "rf100",
            "cross_domain",
            "vdn",
            "reader_advantage",
            "efficiency",
        ),
        default="all",
        help="Build one figure or the complete figure set.",
    )
    parser.add_argument(
        "--png-only",
        action="store_true",
        help="Write only PNG review assets for the selected figure set.",
    )
    args = parser.parse_args()
    configure_style()
    if args.figure in ("all", "architecture"):
        build_architecture(png_only=args.png_only)
    if args.figure in ("all", "syncg"):
        build_syncg(png_only=args.png_only)
    if args.figure in ("all", "ablation"):
        build_ablation_routing(png_only=args.png_only)
    if args.figure in ("all", "industrial"):
        build_industrial(png_only=args.png_only)
    if args.figure in ("all", "rf100"):
        build_rf100(png_only=args.png_only)
    if args.figure in ("all", "cross_domain"):
        build_cross_domain(png_only=args.png_only)
    if args.figure in ("all", "vdn"):
        build_vdn(png_only=args.png_only)
    if args.figure in ("all", "reader_advantage"):
        build_reader_advantage(png_only=args.png_only)
    if args.figure in ("all", "efficiency"):
        build_efficiency(png_only=args.png_only)
    if args.png_only:
        print(f"Built GeoPRR-Net {args.figure} review figure: PNG only.")
    else:
        print("Built GeoPRR-Net figures: SVG, PDF, PNG, and LZW TIFF.")


if __name__ == "__main__":
    main()
