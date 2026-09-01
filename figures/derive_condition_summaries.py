"""Derive compact condition-wise CSVs from the public GeoPRR-Net data release.

The public ledgers contain every SyncG sample, condition, and training seed.
Industrial-1395 combines the released supervised five-fold OOF GeoPRR-Net
predictions with the anonymized raw-CNN group summaries.  The script keeps the
published rosters intact, averages comparator errors across the three fitted
seeds, and bootstraps the declared scene/source groups.
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any, Iterable

import numpy as np

HERE = Path(__file__).resolve().parent
PAPER_ROOT = HERE.parent
DATA_ROOT = PAPER_ROOT / "data"
REPORT_PATH = DATA_ROOT / "public_results_summary.json"
SYNCG_GEOPRR_PATH = DATA_ROOT / "syncg" / "geoprr_predictions.csv.gz"
SYNCG_EXTERNAL_PATH = DATA_ROOT / "syncg" / "external_cnn_predictions.csv.gz"
INDUSTRIAL_GROUP_PATH = DATA_ROOT / "industrial1395" / "group_metrics.csv.gz"
INDUSTRIAL_OOF_PATH = DATA_ROOT / "industrial1395" / "supervised_feature_head_ensemble_per_sample.json"
SEEDS = (20262020, 20262021, 20262022)
CONDITIONS = (
    "clean",
    "blur_moderate",
    "blur_severe",
    "perspective_moderate",
    "perspective_severe",
    "combined_severe",
)
CONDITION_LABELS = {
    "clean": "Clean",
    "blur_moderate": "Blur moderate",
    "blur_severe": "Blur severe",
    "perspective_moderate": "Perspective moderate",
    "perspective_severe": "Perspective severe",
    "combined_severe": "Perspective severe + blur",
}
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20260828
SYNCG_ROWS_PER_SEED = 9_348
SYNCG_ROWS_PER_CONDITION = 1_558
SYNCG_SCENES = 14
INDUSTRIAL_IMAGES = 1_395
INDUSTRIAL_GROUPS = 52
INDUSTRIAL_RAW_METHODS = (
    "Raw ResNet-18",
    "Raw EfficientNet-B0",
    "Raw MobileNetV3-Large",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def read_gzip_csv(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def quantile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    require(bool(ordered), "cannot calculate a quantile of an empty sample")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def paired_group_bootstrap_fast(
    candidate_errors: Iterable[float],
    comparator_errors: Iterable[float],
    groups: Iterable[str],
    *,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    candidate = np.asarray(list(candidate_errors), dtype=np.float64)
    comparator = np.asarray(list(comparator_errors), dtype=np.float64)
    group_values = list(groups)
    require(
        len(candidate) == len(comparator) == len(group_values) and bool(group_values),
        "paired bootstrap arrays are misaligned",
    )
    group_ids = sorted(set(group_values))
    require(len(group_ids) >= 2, "paired bootstrap needs at least two groups")
    group_index = {group_id: index for index, group_id in enumerate(group_ids)}
    deltas = candidate - comparator
    candidate_group_sums = np.zeros(len(group_ids), dtype=np.float64)
    comparator_group_sums = np.zeros(len(group_ids), dtype=np.float64)
    group_sums = np.zeros(len(group_ids), dtype=np.float64)
    group_sizes = np.zeros(len(group_ids), dtype=np.int64)
    for row_index, group_id in enumerate(group_values):
        index = group_index[group_id]
        candidate_group_sums[index] += candidate[row_index]
        comparator_group_sums[index] += comparator[row_index]
        group_sums[index] += deltas[row_index]
        group_sizes[index] += 1

    rng = random.Random(seed)
    draws: list[float] = []
    relative_draws: list[float] = []
    batch_size = 4_096
    completed = 0
    while completed < replicates:
        batch = min(batch_size, replicates - completed)
        choices = np.fromiter(
            (rng.randrange(len(group_ids)) for _ in range(batch * len(group_ids))),
            dtype=np.int64,
            count=batch * len(group_ids),
        ).reshape(batch, len(group_ids))
        counts = np.zeros((batch, len(group_ids)), dtype=np.int32)
        np.add.at(
            counts,
            (np.repeat(np.arange(batch), len(group_ids)), choices.reshape(-1)),
            1,
        )
        draws.extend(((counts @ group_sums) / (counts @ group_sizes)).tolist())
        candidate_sums = counts @ candidate_group_sums
        comparator_sums = counts @ comparator_group_sums
        require(bool((comparator_sums > 0).all()), "relative bootstrap comparator mean must be positive")
        relative_draws.extend((100.0 * (comparator_sums - candidate_sums) / comparator_sums).tolist())
        completed += batch
    comparator_mean = float(np.mean(comparator))
    require(comparator_mean > 0, "relative reduction comparator mean must be positive")
    return {
        "delta_nmae_candidate_minus_comparator": float(np.mean(deltas)),
        "relative_reduction_percent": 100.0 * (comparator_mean - float(np.mean(candidate))) / comparator_mean,
        "paired_group_bootstrap_ci95": {
            "low": quantile(draws, 0.025),
            "high": quantile(draws, 0.975),
        },
        "paired_group_bootstrap_relative_ci95": {
            "low": quantile(relative_draws, 0.025),
            "high": quantile(relative_draws, 0.975),
        },
        "groups": len(group_ids),
        "replicates": replicates,
        "seed": seed,
    }


def distribution(values: Iterable[float]) -> tuple[float, float]:
    numbers = [float(value) for value in values]
    return statistics.fmean(numbers), statistics.stdev(numbers)


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with (HERE / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize_condition(
    *,
    condition: str,
    proposed_seed_errors: list[np.ndarray],
    baseline_seed_errors: list[np.ndarray],
    groups: list[str],
    bootstrap_seed: int,
) -> dict[str, Any]:
    proposed_seed_nmae = [float(values.mean()) for values in proposed_seed_errors]
    baseline_seed_nmae = [float(values.mean()) for values in baseline_seed_errors]
    proposed_mean, proposed_sd = distribution(proposed_seed_nmae)
    baseline_mean, baseline_sd = distribution(baseline_seed_nmae)
    paired = paired_group_bootstrap_fast(
        np.asarray(proposed_seed_errors, dtype=np.float64).mean(axis=0),
        np.asarray(baseline_seed_errors, dtype=np.float64).mean(axis=0),
        groups,
        replicates=BOOTSTRAP_REPLICATES,
        seed=bootstrap_seed,
    )
    interval = paired["paired_group_bootstrap_ci95"]
    return {
        "condition": condition,
        "label": CONDITION_LABELS[condition],
        "geo_nmae_mean": proposed_mean,
        "geo_nmae_sd": proposed_sd,
        "baseline_nmae_mean": baseline_mean,
        "baseline_nmae_sd": baseline_sd,
        "relative_reduction_percent": 100.0 * (baseline_mean - proposed_mean) / baseline_mean,
        "delta_nmae": paired["delta_nmae_candidate_minus_comparator"],
        "ci_low": interval["low"],
        "ci_high": interval["high"],
        "rows": len(groups),
        "groups": paired["groups"],
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
    }


def load_syncg_sources() -> tuple[
    list[tuple[str, str, str]],
    dict[int, dict[tuple[str, str, str], float]],
    dict[str, dict[int, dict[tuple[str, str, str], float]]],
]:
    """Load the full-EMA GeoPRR and explicitly raw CNN public ledgers."""
    geoprr = {seed: {} for seed in SEEDS}
    targets: dict[tuple[str, str, str], float] = {}
    for row in read_gzip_csv(SYNCG_GEOPRR_PATH):
        if row["variant"] != "full" or row["weight_variant"] != "ema":
            continue
        seed = int(row["seed"])
        require(seed in geoprr, "unexpected GeoPRR-Net seed")
        key = (row["scene_id"], row["image_id"], row["condition"])
        require(key not in geoprr[seed], "duplicate GeoPRR-Net SyncG key")
        geoprr[seed][key] = float(row["absolute_error"])
        target = float(row["target"])
        if key in targets:
            require(abs(targets[key] - target) <= 1e-12, "GeoPRR-Net target differs across seeds")
        else:
            targets[key] = target

    raw = {
        model: {seed: {} for seed in SEEDS}
        for model in ("ResNet-18", "EfficientNet-B0", "MobileNetV3-Large")
    }
    for row in read_gzip_csv(SYNCG_EXTERNAL_PATH):
        if row["preprocessing"] != "raw":
            continue
        model = row["model"]
        seed = int(row["seed"])
        require(model in raw and seed in raw[model], "unexpected Raw CNN arm")
        key = (row["scene_id"], row["image_id"], row["condition"])
        require(key not in raw[model][seed], "duplicate Raw CNN SyncG key")
        require(key in targets, "Raw CNN row is absent from the GeoPRR-Net roster")
        require(abs(targets[key] - float(row["target"])) <= 1e-12, "Raw CNN target differs")
        raw[model][seed][key] = float(row["absolute_error"])

    reference_keys = sorted(geoprr[SEEDS[0]])
    require(len(reference_keys) == SYNCG_ROWS_PER_SEED, "GeoPRR-Net SyncG denominator differs")
    require(len({key[0] for key in reference_keys}) == SYNCG_SCENES, "SyncG scene count differs")
    for condition in CONDITIONS:
        require(
            sum(key[2] == condition for key in reference_keys) == SYNCG_ROWS_PER_CONDITION,
            f"SyncG condition denominator differs: {condition}",
        )
    reference_set = set(reference_keys)
    for seed in SEEDS:
        require(set(geoprr[seed]) == reference_set, "GeoPRR-Net SyncG roster differs across seeds")
    for model in raw:
        for seed in SEEDS:
            require(set(raw[model][seed]) == reference_set, f"Raw {model} SyncG roster differs")
    return reference_keys, geoprr, raw


def derive_syncg() -> list[dict[str, Any]]:
    reference_keys, geoprr, raw = load_syncg_sources()
    output: list[dict[str, Any]] = []
    for index, condition in enumerate(CONDITIONS):
        selected = [key for key in reference_keys if key[2] == condition]
        proposed = [
            np.asarray([geoprr[seed][key] for key in selected], dtype=np.float64)
            for seed in SEEDS
        ]
        baseline = [
            np.asarray([raw["EfficientNet-B0"][seed][key] for key in selected], dtype=np.float64)
            for seed in SEEDS
        ]
        output.append(
            summarize_condition(
                condition=condition,
                proposed_seed_errors=proposed,
                baseline_seed_errors=baseline,
                groups=[key[0] for key in selected],
                bootstrap_seed=BOOTSTRAP_SEED + index,
            )
        )
    return output


def derive_syncg_all_models() -> list[dict[str, Any]]:
    """Summarize GeoPRR-Net and every truly raw CNN on one paired roster."""
    reference_keys, geoprr, raw = load_syncg_sources()
    model_keys = (
        ("GeoPRR-Net", None),
        ("Raw ResNet-18", "ResNet-18"),
        ("Raw EfficientNet-B0", "EfficientNet-B0"),
        ("Raw MobileNetV3-Large", "MobileNetV3-Large"),
    )
    output: list[dict[str, Any]] = []
    for condition_index, condition in enumerate(CONDITIONS):
        selected = [key for key in reference_keys if key[2] == condition]
        groups = [key[0] for key in selected]
        proposed = [
            np.asarray([geoprr[seed][key] for key in selected], dtype=np.float64)
            for seed in SEEDS
        ]
        proposed_seed_nmae = [float(values.mean()) for values in proposed]
        proposed_mean, proposed_sd = distribution(proposed_seed_nmae)
        for model_index, (method, external_key) in enumerate(model_keys):
            if external_key is None:
                seed_errors = proposed
                mean, sd = proposed_mean, proposed_sd
                relative_reduction = 0.0
                delta, ci_low, ci_high = 0.0, 0.0, 0.0
            else:
                seed_errors = [
                    np.asarray([raw[external_key][seed][key] for key in selected], dtype=np.float64)
                    for seed in SEEDS
                ]
                seed_nmae = [float(values.mean()) for values in seed_errors]
                mean, sd = distribution(seed_nmae)
                paired = paired_group_bootstrap_fast(
                    np.asarray(proposed, dtype=np.float64).mean(axis=0),
                    np.asarray(seed_errors, dtype=np.float64).mean(axis=0),
                    groups,
                    replicates=BOOTSTRAP_REPLICATES,
                    seed=BOOTSTRAP_SEED + 200 + 10 * condition_index + model_index,
                )
                interval = paired["paired_group_bootstrap_ci95"]
                relative_reduction = 100.0 * (mean - proposed_mean) / mean
                delta = paired["delta_nmae_candidate_minus_comparator"]
                ci_low, ci_high = interval["low"], interval["high"]
            seed_acc2 = [float(np.mean(values <= 0.02)) for values in seed_errors]
            acc2_mean, acc2_sd = distribution(seed_acc2)
            output.append(
                {
                    "method": method,
                    "condition": condition,
                    "label": CONDITION_LABELS[condition],
                    "nmae_mean": mean,
                    "nmae_sd": sd,
                    "acc2_mean": acc2_mean,
                    "acc2_sd": acc2_sd,
                    "geo_reduction_percent": relative_reduction,
                    "delta_geo_minus_method": delta,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "rows": len(groups),
                    "groups": len(set(groups)),
                    "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                }
            )
    return output


def load_industrial_adapted_sources() -> tuple[
    dict[tuple[str, int, str], dict[str, dict[str, str]]],
    dict[tuple[str, str], list[float]],
]:
    """Join OOF predictions to the public alias roster without releasing its map."""
    rows = read_gzip_csv(INDUSTRIAL_GROUP_PATH)
    cells: dict[tuple[str, int, str], dict[str, dict[str, str]]] = {}
    for row in rows:
        key = (row["method"], int(row["seed"]), row["scope"])
        cells.setdefault(key, {})[row["group_id"]] = row

    payload = load_json(INDUSTRIAL_OOF_PATH)
    oof_rows = payload["oof_rows"]
    require(isinstance(oof_rows, list), "Industrial OOF rows must be a list")
    require(len(oof_rows) == INDUSTRIAL_IMAGES * len(CONDITIONS), "Industrial OOF denominator differs")
    require(payload["groups"] == INDUSTRIAL_GROUPS, "Industrial OOF group count differs")

    # The public group table replaces source group names with group_001 ...
    # group_052. Recover the internal one-to-one join by matching row counts
    # and the three frozen-seed NMAEs carried by both released ledgers. Only
    # aliases are written to the derived plotting files.
    frozen_errors: dict[str, list[list[float]]] = {}
    original_rows: dict[str, int] = {}
    for row in oof_rows:
        original_group = str(row["group_id"])
        target = float(row["target"])
        predictions = row["frozen_seed_predictions"]
        require(len(predictions) == len(SEEDS), "Industrial frozen seed roster differs")
        group_errors = frozen_errors.setdefault(original_group, [[] for _ in SEEDS])
        for index, prediction in enumerate(predictions):
            group_errors[index].append(abs(float(prediction) - target))
        original_rows[original_group] = original_rows.get(original_group, 0) + 1

    alias_reference = cells[("GeoPRR-Net", SEEDS[0], "all_conditions")]
    require(len(alias_reference) == INDUSTRIAL_GROUPS, "Industrial public alias count differs")
    alias_vectors = {
        alias: tuple(
            float(cells[("GeoPRR-Net", seed, "all_conditions")][alias]["nmae"])
            for seed in SEEDS
        )
        for alias in alias_reference
    }
    alias_rows = {alias: int(row["rows"]) for alias, row in alias_reference.items()}
    aliases: dict[str, str] = {}
    used_aliases: set[str] = set()
    for original_group, per_seed in sorted(frozen_errors.items()):
        vector = tuple(float(np.mean(values)) for values in per_seed)
        candidates = [
            alias
            for alias, count in alias_rows.items()
            if count == original_rows[original_group]
        ]
        require(bool(candidates), "Industrial OOF group has no size-matched public alias")
        scored = sorted(
            (max(abs(left - right) for left, right in zip(vector, alias_vectors[alias])), alias)
            for alias in candidates
        )
        error, alias = scored[0]
        require(error < 1e-3, "Industrial OOF group could not be matched to the public alias roster")
        require(alias not in used_aliases, "Industrial OOF alias matching is not one-to-one")
        aliases[original_group] = alias
        used_aliases.add(alias)
    require(len(aliases) == len(used_aliases) == INDUSTRIAL_GROUPS, "Industrial alias map is incomplete")

    adapted_errors: dict[tuple[str, str], list[float]] = {}
    for row in oof_rows:
        alias = aliases[str(row["group_id"])]
        condition = str(row["condition"])
        require(condition in CONDITIONS, "Unexpected Industrial OOF condition")
        error = abs(float(row["adapted_equal_weight_prediction"]) - float(row["target"]))
        adapted_errors.setdefault((alias, condition), []).append(error)
        adapted_errors.setdefault((alias, "all_conditions"), []).append(error)
    require(
        sum(len(values) for (alias, scope), values in adapted_errors.items() if scope == "all_conditions")
        == INDUSTRIAL_IMAGES * len(CONDITIONS),
        "Industrial adapted errors do not recover the complete roster",
    )
    return cells, adapted_errors


def industrial_group_arrays(
    *,
    cells: dict[tuple[str, int, str], dict[str, dict[str, str]]],
    adapted_errors: dict[tuple[str, str], list[float]],
    scope: str,
    comparator: str,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Expand group means to row weights for the declared cluster bootstrap."""
    reference = cells[(comparator, SEEDS[0], scope)]
    group_ids = sorted(reference)
    require(len(group_ids) == INDUSTRIAL_GROUPS, "Industrial comparator group count differs")
    candidate_parts: list[np.ndarray] = []
    comparator_parts: list[np.ndarray] = []
    groups: list[str] = []
    for group_id in group_ids:
        candidate_values = adapted_errors[(group_id, scope)]
        row_count = len(candidate_values)
        require(row_count == int(reference[group_id]["rows"]), "Industrial paired group size differs")
        candidate_mean = float(np.mean(candidate_values))
        comparator_mean = statistics.fmean(
            float(cells[(comparator, seed, scope)][group_id]["nmae"])
            for seed in SEEDS
        )
        candidate_parts.append(np.full(row_count, candidate_mean, dtype=np.float64))
        comparator_parts.append(np.full(row_count, comparator_mean, dtype=np.float64))
        groups.extend([group_id] * row_count)
    return np.concatenate(candidate_parts), np.concatenate(comparator_parts), groups


def derive_industrial() -> list[dict[str, Any]]:
    cells, adapted_errors = load_industrial_adapted_sources()
    output: list[dict[str, Any]] = []
    for index, condition in enumerate(CONDITIONS):
        reference = cells[("Raw EfficientNet-B0", SEEDS[0], condition)]
        group_ids = sorted(reference)
        require(len(group_ids) == INDUSTRIAL_GROUPS, "Industrial public group count differs")
        group_sizes = {group_id: int(reference[group_id]["rows"]) for group_id in group_ids}
        require(sum(group_sizes.values()) == INDUSTRIAL_IMAGES, "Industrial public denominator differs")

        baseline: list[np.ndarray] = []
        for seed in SEEDS:
            baseline_cell = cells[("Raw EfficientNet-B0", seed, condition)]
            require(set(baseline_cell) == set(group_ids), "Industrial baseline group roster differs")
            require(
                all(int(baseline_cell[group]["rows"]) == group_sizes[group] for group in group_ids),
                "Industrial baseline group sizes differ",
            )
            baseline.append(
                np.concatenate(
                    [
                        np.full(group_sizes[group], float(baseline_cell[group]["nmae"]), dtype=np.float64)
                        for group in group_ids
                    ]
                )
            )
        proposed = np.concatenate(
            [np.asarray(adapted_errors[(group, condition)], dtype=np.float64) for group in group_ids]
        )
        groups = [group for group in group_ids for _ in range(group_sizes[group])]
        baseline_mean, baseline_sd = distribution(float(values.mean()) for values in baseline)
        paired = paired_group_bootstrap_fast(
            proposed,
            np.asarray(baseline, dtype=np.float64).mean(axis=0),
            groups,
            replicates=BOOTSTRAP_REPLICATES,
            seed=BOOTSTRAP_SEED + 100 + index,
        )
        interval = paired["paired_group_bootstrap_ci95"]
        proposed_mean = float(proposed.mean())
        output.append(
            {
                "condition": condition,
                "label": CONDITION_LABELS[condition],
                "geo_nmae_mean": proposed_mean,
                "geo_nmae_sd": 0.0,
                "baseline_nmae_mean": baseline_mean,
                "baseline_nmae_sd": baseline_sd,
                "relative_reduction_percent": 100.0 * (baseline_mean - proposed_mean) / baseline_mean,
                "delta_nmae": paired["delta_nmae_candidate_minus_comparator"],
                "ci_low": interval["low"],
                "ci_high": interval["high"],
                "rows": len(groups),
                "groups": paired["groups"],
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            }
        )
    return output


def derive_industrial_pooled() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    cells, adapted_errors = load_industrial_adapted_sources()
    group_ids = sorted(cells[("Raw EfficientNet-B0", SEEDS[0], "all_conditions")])
    candidate_errors = np.concatenate(
        [np.asarray(adapted_errors[(group, "all_conditions")], dtype=np.float64) for group in group_ids]
    )
    require(len(candidate_errors) == INDUSTRIAL_IMAGES * len(CONDITIONS), "Industrial pooled denominator differs")
    metric_rows: list[dict[str, Any]] = [
        {
            "cohort": "industrial_1395",
            "cohort_label": "Industrial-1395",
            "method": "GeoPRR-Net",
            "nmae_mean": float(candidate_errors.mean()),
            "nmae_sd": 0.0,
            "acc2_mean": float(np.mean(candidate_errors <= 0.02)),
            "acc2_sd": 0.0,
            "n_images": INDUSTRIAL_IMAGES,
            "n_conditions": len(CONDITIONS),
        }
    ]
    paired_rows: list[dict[str, Any]] = []
    group_effect_rows: list[dict[str, Any]] = []
    for method_index, method in enumerate(INDUSTRIAL_RAW_METHODS):
        seed_nmae: list[float] = []
        seed_acc2: list[float] = []
        for seed in SEEDS:
            cell = cells[(method, seed, "all_conditions")]
            total_rows = sum(int(cell[group]["rows"]) for group in group_ids)
            require(total_rows == len(candidate_errors), "Industrial raw-CNN denominator differs")
            seed_nmae.append(
                sum(float(cell[group]["nmae"]) * int(cell[group]["rows"]) for group in group_ids) / total_rows
            )
            seed_acc2.append(
                sum(float(cell[group]["acc_at_2_percent"]) * int(cell[group]["rows"]) for group in group_ids)
                / total_rows
            )
        nmae_mean, nmae_sd = distribution(seed_nmae)
        acc2_mean, acc2_sd = distribution(seed_acc2)
        metric_rows.append(
            {
                "cohort": "industrial_1395",
                "cohort_label": "Industrial-1395",
                "method": method,
                "nmae_mean": nmae_mean,
                "nmae_sd": nmae_sd,
                "acc2_mean": acc2_mean,
                "acc2_sd": acc2_sd,
                "n_images": INDUSTRIAL_IMAGES,
                "n_conditions": len(CONDITIONS),
            }
        )
        candidate_grouped, comparator_grouped, groups = industrial_group_arrays(
            cells=cells,
            adapted_errors=adapted_errors,
            scope="all_conditions",
            comparator=method,
        )
        paired = paired_group_bootstrap_fast(
            candidate_grouped,
            comparator_grouped,
            groups,
            replicates=BOOTSTRAP_REPLICATES,
            seed=20260927 + method_index,
        )
        interval = paired["paired_group_bootstrap_ci95"]
        relative_interval = paired["paired_group_bootstrap_relative_ci95"]
        paired_rows.append(
            {
                "comparator": method,
                "label": method,
                "delta": paired["delta_nmae_candidate_minus_comparator"],
                "ci_low": interval["low"],
                "ci_high": interval["high"],
                "relative_reduction_percent": paired["relative_reduction_percent"],
                "relative_ci_low": relative_interval["low"],
                "relative_ci_high": relative_interval["high"],
                "clusters": paired["groups"],
                "replicates": BOOTSTRAP_REPLICATES,
            }
        )
        if method == "Raw EfficientNet-B0":
            for group_id in group_ids:
                candidate_group = adapted_errors[(group_id, "all_conditions")]
                comparator_group = statistics.fmean(
                    float(cells[(method, seed, "all_conditions")][group_id]["nmae"])
                    for seed in SEEDS
                )
                group_effect_rows.append(
                    {
                        "group_id": group_id,
                        "delta_nmae_percent_fs": 100.0 * (float(np.mean(candidate_group)) - comparator_group),
                        "rows": len(candidate_group),
                    }
                )
    return metric_rows, paired_rows, group_effect_rows


def derive_ablation(report: dict[str, Any]) -> list[dict[str, Any]]:
    variants = (
        ("no_geometry_fusion", "No geometry-aware fusion"),
        ("fixed_routing", "Fixed routing"),
        ("no_relational_transport", "No relational transport"),
        ("no_polar_evidence", "No polar evidence"),
    )
    output: list[dict[str, Any]] = []
    full = report["syncg"]["ablation"]["full"]["conditions"]
    for variant, variant_label in variants:
        conditions = report["syncg"]["ablation"][variant]["conditions"]
        for condition in CONDITIONS:
            penalties = np.asarray(conditions[condition]["per_seed"], dtype=np.float64) - np.asarray(
                full[condition]["per_seed"], dtype=np.float64
            )
            output.append(
                {
                    "variant": variant,
                    "variant_label": variant_label,
                    "condition": condition,
                    "label": CONDITION_LABELS[condition],
                    "penalty_mean": float(penalties.mean()),
                    "penalty_sd": float(penalties.std(ddof=1)),
                }
            )
    return output


def derive_routing(report: dict[str, Any]) -> list[dict[str, Any]]:
    payload = report["syncg"]["routing_mechanism_summary"]
    output: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        summary = payload[condition]
        weights = summary["mean_routing_weights"]
        oracle = summary["oracle_candidate_fraction"]
        output.append(
            {
                "condition": condition,
                "label": CONDITION_LABELS[condition],
                "base": weights["base"],
                "polar": weights["polar_evidence"],
                "relational": weights["relational_transport"],
                "oracle_base": oracle["base"],
                "oracle_polar": oracle["polar_evidence"],
                "oracle_relational": oracle["relational_transport"],
                "routing_gain": -float(summary["adaptive_minus_fixed_prior_nmae"]),
                "seed": SEEDS[0],
            }
        )
    return output


def main() -> None:
    report = load_json(REPORT_PATH)
    condition_fields = [
        "condition",
        "label",
        "geo_nmae_mean",
        "geo_nmae_sd",
        "baseline_nmae_mean",
        "baseline_nmae_sd",
        "relative_reduction_percent",
        "delta_nmae",
        "ci_low",
        "ci_high",
        "rows",
        "groups",
        "bootstrap_replicates",
    ]
    write_csv("syncg_condition_comparison.csv", condition_fields, derive_syncg())
    write_csv(
        "syncg_all_models_conditions.csv",
        [
            "method",
            "condition",
            "label",
            "nmae_mean",
            "nmae_sd",
            "acc2_mean",
            "acc2_sd",
            "geo_reduction_percent",
            "delta_geo_minus_method",
            "ci_low",
            "ci_high",
            "rows",
            "groups",
            "bootstrap_replicates",
        ],
        derive_syncg_all_models(),
    )
    industrial_rows, paired_industrial_rows, industrial_group_rows = derive_industrial_pooled()
    write_csv(
        "industrial.csv",
        [
            "cohort",
            "cohort_label",
            "method",
            "nmae_mean",
            "nmae_sd",
            "acc2_mean",
            "acc2_sd",
            "n_images",
            "n_conditions",
        ],
        industrial_rows,
    )
    write_csv(
        "paired_industrial.csv",
        [
            "comparator",
            "label",
            "delta",
            "ci_low",
            "ci_high",
            "relative_reduction_percent",
            "relative_ci_low",
            "relative_ci_high",
            "clusters",
            "replicates",
        ],
        paired_industrial_rows,
    )
    write_csv(
        "industrial_group_effects.csv",
        ["group_id", "delta_nmae_percent_fs", "rows"],
        industrial_group_rows,
    )
    write_csv("industrial_condition_comparison.csv", condition_fields, derive_industrial())
    write_csv(
        "ablation_condition_effects.csv",
        ["variant", "variant_label", "condition", "label", "penalty_mean", "penalty_sd"],
        derive_ablation(report),
    )
    write_csv(
        "routing_conditions.csv",
        [
            "condition",
            "label",
            "base",
            "polar",
            "relational",
            "oracle_base",
            "oracle_polar",
            "oracle_relational",
            "routing_gain",
            "seed",
        ],
        derive_routing(report),
    )
    print("Derived all-model SyncG, adapted Industrial-1395, ablation, and routing summaries.")


if __name__ == "__main__":
    main()
