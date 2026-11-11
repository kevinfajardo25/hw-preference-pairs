"""Validate a preference-pair dataset and report annotation quality signals.

Checks:
  * schema: required fields, unique ids, preferred in {A, B}, strength in 1..3
  * taxonomy: every error tag is in the allowed list (TAXONOMY)
  * consistency: strength 1 (near tie) pairs carry no error tags; strength 3 pairs do
  * bias signals: position balance (A vs B) and length bias (preferred = longer)

Usage:  python tools/validate.py data/pairs.jsonl
Exit code is 1 if any hard error is found, so it can run in CI.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REQUIRED = {"id", "domain", "prompt", "response_a", "response_b", "preferred",
            "strength", "error_tags", "critique"}

TAXONOMY = {
    "omitted_term": "a term or factor left out of an otherwise correct formula",
    "wrong_formula": "a different formula or quantity was used",
    "wrong_constant": "correct formula, wrong coefficient or table value",
    "unit_error": "wrong unit, missing conversion, or mislabeled unit",
    "ignored_loading": "ignored source or load impedance, or another interaction",
    "misread_datasheet": "a datasheet parameter used for something it does not mean",
    "rule_of_thumb_misapplied": "a heuristic used outside its valid range",
    "misconception": "a physical misconception about how something works",
    "reversed_logic": "the rule applied backwards",
    "overgeneralization": "a conditional rule stated as always true",
    "ignored_requirement": "the response ignores a constraint stated in the prompt",
    "unsafe": "advice that could damage hardware or injure someone",
}


def load(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def validate(pairs: list[dict]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    seen = set()
    for i, p in enumerate(pairs, 1):
        pid = p.get("id", f"<line {i}>")
        missing = REQUIRED - p.keys()
        if missing:
            errors.append(f"{pid}: missing fields {sorted(missing)}")
            continue
        if pid in seen:
            errors.append(f"{pid}: duplicate id")
        seen.add(pid)
        if p["preferred"] not in ("A", "B"):
            errors.append(f"{pid}: preferred must be 'A' or 'B'")
        if p["strength"] not in (1, 2, 3):
            errors.append(f"{pid}: strength must be 1, 2 or 3")
        for tag in p["error_tags"]:
            if tag not in TAXONOMY:
                errors.append(f"{pid}: unknown error tag '{tag}'")
        if not p["critique"].strip():
            errors.append(f"{pid}: empty critique")
        if p["response_a"].strip() == p["response_b"].strip():
            errors.append(f"{pid}: responses are identical")
        if p["strength"] == 3 and not p["error_tags"]:
            warnings.append(f"{pid}: strong preference but no error tag explains it")
        if p["strength"] == 1 and p["error_tags"]:
            warnings.append(f"{pid}: near tie but error tags present, check the strength")
    return errors, warnings


def bias_report(pairs: list[dict]) -> dict:
    pos = Counter(p["preferred"] for p in pairs)
    longer = sum(
        len(p["response_a" if p["preferred"] == "A" else "response_b"])
        > len(p["response_b" if p["preferred"] == "A" else "response_a"])
        for p in pairs)
    n = len(pairs)
    return {"n": n, "preferred_A": pos["A"], "preferred_B": pos["B"],
            "preferred_is_longer": longer, "length_bias_rate": longer / n if n else 0.0,
            "tags": dict(Counter(t for p in pairs for t in p["error_tags"]).most_common()),
            "domains": dict(Counter(p["domain"] for p in pairs))}


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/pairs.jsonl")
    pairs = load(path)
    errors, warnings = validate(pairs)
    report = bias_report(pairs)

    print(f"{report['n']} pairs in {path}")
    print(f"position: A preferred {report['preferred_A']}, B preferred {report['preferred_B']}")
    print(f"preferred response is the longer one in {report['preferred_is_longer']}/{report['n']} "
          f"pairs ({report['length_bias_rate']:.0%})")
    if report["length_bias_rate"] > 0.8:
        print("  note: high length correlation; a reward model may learn 'longer is better'. "
              "Add pairs where the shorter answer wins.")
    print("domains:", report["domains"])
    print("error tags:", report["tags"])
    for w in warnings:
        print("WARNING", w)
    for e in errors:
        print("ERROR  ", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
