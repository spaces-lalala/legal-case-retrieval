"""子集篩選：從 53 萬筆刑事判決中篩出目標案件。

目標：過失傷害 / 公共危險(交通類) / 肇事逃逸，限地方法院，壓到約 1-3 萬筆。
詳見 docs/design_v1.md 第 3.1 節。

本模組只放純邏輯（可單元測試、工程階段可重用），不負責 I/O 遍歷；
遍歷與統計輸出在 experiments/01_subset_filter.py。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FilterCriteria:
    """篩選條件。預設值對齊 config.settings，但保持模組獨立可測。"""

    title_keywords: tuple[str, ...]
    case_prefixes: tuple[str, ...]
    district_court_only: bool = True


def is_district_court(court_name: str) -> bool:
    """是否為地方法院（排除最高法院、高等法院、簡易庭以外的上級審）。"""
    return "地方法院" in court_name


def match_title(title: str, keywords: tuple[str, ...]) -> bool:
    """JTITLE 是否含任一目標關鍵字。"""
    return any(kw in title for kw in keywords)


def match_case_prefix(jcase: str, prefixes: tuple[str, ...]) -> bool:
    """JCASE 是否為目標案件類別（交通相關）。"""
    return jcase in prefixes


def should_keep(
    *,
    title: str,
    jcase: str,
    court_name: str,
    criteria: FilterCriteria,
) -> bool:
    """判斷單筆判決是否納入子集。

    規則：(案由命中關鍵字 OR 案件類別為交通類) AND (若限定則須為地方法院)。
    """
    if criteria.district_court_only and not is_district_court(court_name):
        return False
    return match_title(title, criteria.title_keywords) or match_case_prefix(
        jcase, criteria.case_prefixes
    )


def criteria_from_settings(settings) -> FilterCriteria:
    """由全域 settings 建構 FilterCriteria。"""
    return FilterCriteria(
        title_keywords=settings.target_title_keywords,
        case_prefixes=settings.target_case_prefixes,
        district_court_only=settings.district_court_only,
    )
