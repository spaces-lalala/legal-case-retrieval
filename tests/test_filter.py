"""lcr.data.filter 單元測試。"""

from __future__ import annotations

from lcr.data.filter import (
    FilterCriteria,
    is_district_court,
    match_case_prefix,
    match_title,
    should_keep,
)

CRITERIA = FilterCriteria(
    title_keywords=("過失傷害", "公共危險"),
    case_prefixes=("交易", "交訴"),
    district_court_only=True,
)


def test_is_district_court():
    assert is_district_court("臺灣士林地方法院")
    assert not is_district_court("最高法院")
    assert not is_district_court("臺灣高等法院")


def test_match_title():
    assert match_title("過失傷害", CRITERIA.title_keywords)
    assert match_title("業務過失傷害", CRITERIA.title_keywords)
    assert not match_title("竊盜", CRITERIA.title_keywords)


def test_match_case_prefix():
    assert match_case_prefix("交易", CRITERIA.case_prefixes)
    assert not match_case_prefix("易", CRITERIA.case_prefixes)


def test_should_keep_title_hit_in_district():
    assert should_keep(
        title="過失傷害", jcase="易", court_name="臺灣宜蘭地方法院", criteria=CRITERIA
    )


def test_should_keep_case_prefix_hit():
    assert should_keep(
        title="妨害名譽", jcase="交訴", court_name="臺灣士林地方法院", criteria=CRITERIA
    )


def test_should_drop_non_district_court():
    # 案由命中但非地方法院 → 排除
    assert not should_keep(
        title="公共危險", jcase="台上", court_name="最高法院", criteria=CRITERIA
    )


def test_should_drop_no_match():
    assert not should_keep(
        title="竊盜", jcase="易", court_name="臺灣臺北地方法院", criteria=CRITERIA
    )


def test_district_court_only_false_allows_supreme():
    relaxed = FilterCriteria(
        title_keywords=("公共危險",), case_prefixes=(), district_court_only=False
    )
    assert should_keep(
        title="公共危險", jcase="台上", court_name="最高法院", criteria=relaxed
    )
