# AGENT.md — 專案索引

法律判決類案搜尋系統（生成式 AI 的人文導論期末專題）

從口語事由出發，於台灣刑事判決書中檢索事實相似的歷史案例，
彙整呈現「過去法院怎麼判、賠償範圍、為什麼」。#Law #RAG #刑法

## 文件清單（docs/）

- `docs/design_v1.md` — 系統初版設計。新成員先讀這份。內容包含：
  - 專題目標與系統定位（類案檢索工具，非法律建議）
  - 資料分析（53 萬刑事判決實測、選擇性偏差等真實數字）
  - 系統架構（離線預處理 + 線上查詢兩階段）
  - 四層可驗證要素抽取管線（Outlines + regex + 一致性投票 + NLI）
  - RAG 架構（BGE-M3 + BM25 + RRF + bge-reranker）
  - 評估設計（合成評估集、Recall@5/MRR、消融實驗、RAGAS）
  - 可信度與法律正當性（citation grounding、4 個法律地雷）
  - 可引用文獻地圖（9 篇論文對應設計決策）

## 資料

- 來源：司法院開放資料（opendata.judicial.gov.tw）
- 位置：`ssh home_wsl:/home/mrfrog/code/lawundry_test/Dataset`
- 規模：刑事判決 53 萬筆；目標子集（過失傷害/公共危險/肇逃）約 10 萬筆

## 開發規範

- 系統定位為「類案檢索工具」，非法律建議；禁止對個案做預測。
- 資料有選擇性偏差：純財損（如僅後照鏡損壞）在刑事上多不起訴，須主動揭露。
- Python 一律用 uv（`uv run`、`uv add`），依賴權威來源為 pyproject.toml。
- 每個任務開新分支（feat/... 或 fix/...），不在 main 開發。
- Conventional Commits，commit message 一行英文寫重點。

## 文件慣例

- 專案架構、流程、設計決策一律寫在 docs/。
- 新設計文件命名 `<type>_v<number>.md`（如 design_v2.md），並在本檔補上連結與一句話摘要。
