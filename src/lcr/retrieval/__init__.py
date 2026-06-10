"""搜尋時的 kind 判斷：從使用者事由推斷要搜刑事、民事、或兩者。

設計依據：docs/design_change_v1.md 第 3 節
"""

from __future__ import annotations

from typing import Literal

KindType = Literal["criminal", "civil", "both"]

# 明確指向刑事的關鍵字
_CRIMINAL_KW: tuple[str, ...] = (
    "罪", "起訴", "刑責", "判刑", "坐牢", "傷人", "竊盜", "詐騙",
    "毒品", "強盜", "殺人", "傷害", "公共危險",
)

# 明確指向民事的關鍵字
_CIVIL_KW: tuple[str, ...] = (
    "賠償", "求償", "損失", "退款", "給付", "違約",
    "返還", "損害", "侵權", "補償",
)


def infer_kind(
    query: str,
    collected: dict | None = None,
) -> KindType:
    """從使用者事由推斷要搜哪種判決。

    Args:
        query:     使用者輸入的口語事由
        collected: clarify 階段蒐集到的結構化要件（可選）
                   例如 {"injury": False, "damage": "後照鏡"}

    Returns:
        "criminal" | "civil" | "both"
        - both 時，搜尋層各取 top-3，前端分 tab 顯示
    """
    if collected is None:
        collected = {}

    has_injury = collected.get("injury") is True
    pure_property = (
        collected.get("injury") is False
        and collected.get("damage") is not None
    )

    has_criminal_kw = any(kw in query for kw in _CRIMINAL_KW)
    has_civil_kw = any(kw in query for kw in _CIVIL_KW)

    # 明確刑事：有刑事關鍵字且無純財損訊號
    if has_criminal_kw and not pure_property:
        return "criminal"

    # 明確民事：純財損 或 有賠償關鍵字且無刑事關鍵字
    if pure_property or (has_civil_kw and not has_criminal_kw):
        return "civil"

    # 有受傷：刑事（過失傷害）+ 民事（損害賠償）同時相關
    if has_injury:
        return "both"

    # 預設：兩邊都搜
    return "both"
