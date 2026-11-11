import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import agreement  # noqa: E402
import validate  # noqa: E402

PAIRS = validate.load(ROOT / "data" / "pairs.jsonl")


def test_dataset_is_valid():
    errors, warnings = validate.validate(PAIRS)
    assert errors == []
    assert warnings == []


def test_position_is_balanced():
    r = validate.bias_report(PAIRS)
    assert abs(r["preferred_A"] - r["preferred_B"]) <= 0.25 * r["n"]


def test_every_tag_in_taxonomy_is_documented():
    guidelines = (ROOT / "GUIDELINES.md").read_text(encoding="utf-8")
    for tag in validate.TAXONOMY:
        assert f"`{tag}`" in guidelines, tag


def _pair(**kw):
    base = dict(id="X-1", domain="d", prompt="p", response_a="a", response_b="b",
                preferred="A", strength=2, error_tags=["unit_error"], critique="c")
    base.update(kw)
    return base


@pytest.mark.parametrize("bad", [
    {"preferred": "C"}, {"strength": 5}, {"error_tags": ["made_up"]},
    {"critique": "  "}, {"response_b": "a"},
])
def test_validator_catches_errors(bad):
    errors, _ = validate.validate([_pair(**bad)])
    assert errors


def test_validator_catches_duplicate_ids():
    errors, _ = validate.validate([_pair(), _pair()])
    assert any("duplicate" in e for e in errors)


def test_strength_tag_consistency_warnings():
    _, w1 = validate.validate([_pair(strength=3, error_tags=[])])
    _, w2 = validate.validate([_pair(strength=1, error_tags=["unit_error"])])
    assert w1 and w2


def test_kappa_perfect_and_chance():
    assert agreement.cohens_kappa(list("ABAB"), list("ABAB")) == pytest.approx(1.0)
    # Agreement no better than chance gives kappa 0
    assert agreement.cohens_kappa(list("AABB"), list("ABAB")) == pytest.approx(0.0)


def test_kappa_known_value():
    a = list("AAAAAAABBB")
    b = list("AAAAAABBBA")
    # po = 0.8, pe = 0.7*0.7 + 0.3*0.3 = 0.58, kappa = 0.22/0.42
    assert agreement.cohens_kappa(a, b) == pytest.approx(0.22 / 0.42)


def test_sample_annotations():
    ann = agreement.load_annotations(ROOT / "data" / "annotations.csv")
    ids = sorted(ann["annotator_1"])
    k = agreement.cohens_kappa([ann["annotator_1"][i] for i in ids], [ann["annotator_2"][i] for i in ids])
    assert k == pytest.approx(0.68, abs=0.01)
