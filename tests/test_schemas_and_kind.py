"""lcr.extract.schemas 與 lcr.retrieval.kind_classifier 測試。"""

from __future__ import annotations

from lcr.extract.schemas import get_schema, get_user_template
from lcr.retrieval.kind_classifier import infer_kind

# --- schemas ---

def test_criminal_schema_has_required_fields():
    s = get_schema("criminal")
    assert "verdict" in s["properties"]
    assert "subjective" in s["properties"]   # 刑事才有
    assert "sentence" in s["properties"]     # 刑事才有
    assert "dispute_type" not in s["properties"]  # 民事才有


def test_civil_schema_has_required_fields():
    s = get_schema("civil")
    assert "verdict" in s["properties"]
    assert "dispute_type" in s["properties"]  # 民事才有
    assert "compensation" in s["properties"]
    assert "subjective" not in s["properties"]  # 刑事才有，民事沒有


def test_criminal_verdict_enum():
    enums = get_schema("criminal")["properties"]["verdict"]["enum"]
    assert "有罪" in enums
    assert "無罪" in enums
    assert "原告勝訴" not in enums  # 民事才有


def test_civil_verdict_enum():
    enums = get_schema("civil")["properties"]["verdict"]["enum"]
    assert "原告勝訴" in enums
    assert "原告敗訴" in enums
    assert "有罪" not in enums  # 刑事才有


def test_unknown_kind_defaults_to_criminal():
    s = get_schema("unknown")
    assert "subjective" in s["properties"]  # 刑事 schema


def test_user_template_criminal_mentions_subjective():
    t = get_user_template("criminal")
    assert "故意/過失" in t


def test_user_template_civil_mentions_dispute_type():
    t = get_user_template("civil")
    assert "dispute_type" in t
    assert "損害賠償" in t


# --- kind_classifier ---

def test_infer_criminal_keyword():
    assert infer_kind("被告涉嫌詐騙") == "criminal"
    assert infer_kind("傷人案件") == "criminal"


def test_infer_civil_pure_property():
    # 純財損（無受傷）→ civil
    result = infer_kind(
        "我開車擦撞後照鏡",
        collected={"injury": False, "damage": "後照鏡"},
    )
    assert result == "civil"


def test_infer_civil_compensation_keyword():
    assert infer_kind("對方要求賠償損失") == "civil"


def test_infer_both_with_injury():
    result = infer_kind(
        "我開車撞到人",
        collected={"injury": True},
    )
    assert result == "both"


def test_infer_both_default():
    # 無明確關鍵字 → both
    assert infer_kind("我跟鄰居有糾紛") == "both"


def test_civil_overrides_criminal_if_pure_property():
    # 就算 query 有「傷害」字眼，但 collected 明確是純財損
    result = infer_kind(
        "發生車禍有損害",
        collected={"injury": False, "damage": "車輛"},
    )
    assert result == "civil"
