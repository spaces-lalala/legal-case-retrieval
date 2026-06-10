# 設計變更 v1：刑民分流 schema 與搜尋判斷

> 決策日期：2026-06-10
> 觸發原因：GPT batch 50 筆評估結果顯示，單一 schema 套民事案件時，
> `verdict` 欄位 54% 回傳「其他」、`subjective` 84% 回傳「不明」——
> 因為原始 schema 的 enum 是為刑事設計的，民事案件的判決結果類型完全不同。

---

## 1. 問題根源

原始 `EXTRACTION_SCHEMA`（`src/lcr/extract/openai_extractor.py`）：

```
verdict enum: 有罪/無罪/不受理/緩刑/免刑/駁回/其他/不明
```

這是刑事的分類。民事判決結果是「原告勝訴/敗訴/部分勝訴/調解成立」，
完全不在 enum 裡，GPT 只能回「其他」。
`subjective`（故意/過失）也是刑事概念，民事不適用。

corpus 裡民事佔 **76.9%**，所以影響範圍大。

---

## 2. 設計決策：方案 B（刑民各自 schema）

不採用方案 A（擴充 enum），原因：
- 民事和刑事的核心欄位本質上不同，硬塞進一個 schema 語意混亂
- 分開 schema 讓每個欄位的意義清晰，LLM 輸出更準

### 2.1 刑事 schema（`criminal`）

| 欄位 | 型別 | 說明 |
|------|------|------|
| verdict | enum | 有罪/無罪/不受理/緩刑/免刑/不明 |
| sentence | str\|null | 刑度（有期徒刑/拘役/罰金） |
| compensation | int\|null | 附帶民事賠償金額（元） |
| subjective | enum | 故意/過失/不明 |
| facts_summary | str | 100-150 字事實摘要 |

### 2.2 民事 schema（`civil`）

| 欄位 | 型別 | 說明 |
|------|------|------|
| verdict | enum | 原告勝訴/原告敗訴/部分勝訴/調解成立/駁回/不明 |
| compensation | int\|null | 判賠金額（元） |
| dispute_type | str | 爭議類型（損害賠償/債務/所有權/其他） |
| facts_summary | str | 100-150 字事實摘要 |

注意：民事移除 `sentence`（刑度）和 `subjective`（主觀要素），新增 `dispute_type`。

---

## 3. 搜尋時的 kind 判斷邏輯

使用者輸入口語事由，系統需判斷要搜刑事、民事、或兩邊都搜。

### 策略：規則 + fallback both

```python
def infer_kind(query: str, collected: dict) -> Literal["criminal", "civil", "both"]:
    # 有明確刑事關鍵字 → criminal
    CRIMINAL_KW = ["罪", "起訴", "刑責", "判刑", "坐牢", "傷人", "竊盜", "詐騙"]
    # 有明確民事關鍵字 → civil
    CIVIL_KW    = ["賠償", "求償", "損失", "退款", "給付", "違約", "返還"]

    has_injury  = collected.get("injury") is True
    is_pure_property = not has_injury and collected.get("damage") is not None

    if any(kw in query for kw in CRIMINAL_KW) and not is_pure_property:
        return "criminal"
    if is_pure_property or any(kw in query for kw in CIVIL_KW):
        return "civil"
    return "both"  # 預設兩邊都搜，前端分 tab 顯示
```

`both` 時：刑事索引 top-3 + 民事索引 top-3，合併回傳 6 筆。

---

## 4. API 變更（小幅）

`POST /api/v1/search` response 新增欄位：

```json
{
  "kind_hint": "both",        // 新增：系統判斷的事由類型
  "cases": [
    { "jid": "...", "kind": "criminal", ... },  // kind 欄位已存在於 corpus
    { "jid": "...", "kind": "civil", ... }
  ]
}
```

前端拿到 `kind` 欄位可以分組顯示（兩個 tab 或兩個區塊）。
`api_v1.md` 需要更新 `/search` 的 response schema。

---

## 5. 受影響的檔案清單

| 檔案 | 異動類型 | 說明 |
|------|---------|------|
| `src/lcr/extract/openai_extractor.py` | 修改 | 拆成兩個 schema + `build_batch_request` 加 kind 參數 |
| `src/lcr/extract/schemas.py` | 新增 | 兩個 schema 的定義獨立成模組 |
| `src/lcr/retrieval/kind_classifier.py` | 新增 | `infer_kind()` 邏輯 |
| `experiments/04a_openai_batch.py` | 修改 | 依 kind 選 schema |
| `experiments/04b_llama_extract.py` | 修改 | 依 kind 選 prompt |
| `docs/api_v1.md` | 修改 | `/search` response 加 `kind_hint` |
| `mock/search.json` | 修改 | 更新 mock 加 `kind_hint` |

---

## 6. 不受影響的部分

- corpus.jsonl 已有 `kind` 欄位，不需重跑
- embedding 流程（之後做）直接用 `kind` 決定存哪個 collection
- 切段邏輯（`segment.py`）不變

---

## 7. GPT batch 評估結果（觸發此次改動的證據）

50 筆測試，單一 schema 結果：

| 欄位 | 問題 |
|------|------|
| verdict | 54% 回「其他」（民事案件超出 enum） |
| subjective | 84% 回「不明」（民事案件無此概念） |
| facts_summary | 正常，avg 124 字 ✓ |
| compensation | 18/50 有值（合理，僅部分案件有金額） |
