"""Metric utilities that intentionally require supplied labels; no fabricated benchmarks."""
from collections.abc import Iterable

def precision_recall_f1(predicted: Iterable[str], expected: Iterable[str]) -> dict[str, float]:
    predicted, expected = set(predicted), set(expected)
    tp = len(predicted & expected)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}
