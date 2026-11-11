"""Inter-annotator agreement for pairwise preference labels.

Reports raw agreement and Cohen's kappa for every pair of annotators, plus each
annotator's accuracy against the gold label in pairs.jsonl, and lists the items
they disagree on so a reviewer can adjudicate them.

Usage:  python tools/agreement.py data/pairs.jsonl data/annotations.csv
"""
from __future__ import annotations

import csv
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path


def cohens_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's kappa for two raters over the same items."""
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty label lists")
    n = len(a)
    labels = set(a) | set(b)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in labels)
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def load_annotations(path: Path) -> dict[str, dict[str, str]]:
    by_annotator: dict[str, dict[str, str]] = defaultdict(dict)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_annotator[row["annotator"]][row["pair_id"]] = row["preferred"].strip()
    return dict(by_annotator)


def main() -> None:
    pairs_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/pairs.jsonl")
    ann_path = Path(sys.argv[2] if len(sys.argv) > 2 else "data/annotations.csv")
    gold = {}
    with open(pairs_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                p = json.loads(line)
                gold[p["id"]] = p["preferred"]
    ann = load_annotations(ann_path)

    print("Accuracy against gold")
    for name, labels in sorted(ann.items()):
        ids = [i for i in labels if i in gold]
        acc = sum(labels[i] == gold[i] for i in ids) / len(ids)
        print(f"  {name:<14} {acc:6.1%}  ({len(ids)} items)")

    print("\nPairwise agreement")
    for (n1, l1), (n2, l2) in itertools.combinations(sorted(ann.items()), 2):
        common = sorted(set(l1) & set(l2))
        a, b = [l1[i] for i in common], [l2[i] for i in common]
        raw = sum(x == y for x, y in zip(a, b)) / len(common)
        print(f"  {n1} vs {n2}: raw {raw:.1%}, Cohen's kappa {cohens_kappa(a, b):.2f}")
        diffs = [i for i in common if l1[i] != l2[i]]
        if diffs:
            print("  disagreements to adjudicate: " + ", ".join(
                f"{i} ({n1}={l1[i]}, {n2}={l2[i]}, gold={gold.get(i, '?')})" for i in diffs))


if __name__ == "__main__":
    main()
