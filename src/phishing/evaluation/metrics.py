"""Binary counts and validation-only threshold selection for score >= threshold."""

from dataclasses import dataclass
import math


def validate_scores(labels, scores):
    if len(labels) != len(scores) or not labels:
        raise ValueError('Labels and scores must be nonempty and equally sized')
    if any(label not in (0, 1) for label in labels):
        raise ValueError('Binary labels must be 0 or 1')
    if any(isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
        raise ValueError('Scores must be finite numbers in [0, 1]')


@dataclass(frozen=True)
class Metrics:
    tp: int
    fn: int
    fp: int
    tn: int
    recall: float | None
    fpr: float | None
    precision: float | None
    f1: float | None


def binary_metrics(labels, scores, threshold: float) -> Metrics:
    validate_scores(labels, scores)
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Threshold must be finite and in [0, 1]')
    tp = fn = fp = tn = 0
    for label, score in zip(labels, scores):
        warning = score >= threshold
        if label == 1:
            tp += warning
            fn += not warning
        else:
            fp += warning
            tn += not warning
    return Metrics(tp, fn, fp, tn,
        tp / (tp + fn) if tp + fn else None,
        fp / (fp + tn) if fp + tn else None,
        tp / (tp + fp) if tp + fp else None,
        2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None)


@dataclass(frozen=True)
class OperatingPoint:
    threshold: float
    validation_metrics: Metrics
    target_fpr: float


def select_validation_threshold(labels, scores, target_fpr: float) -> OperatingPoint | None:
    """Never pass test scores here. Return None when no [0,1] point is feasible.

    Select maximum recall subject to measured validation FPR, breaking recall
    ties with the higher threshold. Missing classes cannot support this choice.
    """
    validate_scores(labels, scores)
    if not math.isfinite(target_fpr) or not 0 <= target_fpr <= 1:
        raise ValueError('Target FPR must be in [0, 1]')
    if set(labels) != {0, 1}:
        raise ValueError('Both classes are required in threshold validation')
    choices = []
    for threshold in sorted(set(scores) | {1.0}):
        metrics = binary_metrics(labels, scores, threshold)
        if metrics.fpr <= target_fpr:
            choices.append(OperatingPoint(threshold, metrics, target_fpr))
    return max(choices, key=lambda point: (point.validation_metrics.recall, point.threshold), default=None)
