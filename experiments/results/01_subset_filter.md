# 實驗 01：子集篩選 — 結果筆記

腳本：`experiments/01_subset_filter.py`
核心邏輯：`src/lcr/data/filter.py`

## 執行環境

資料在 `home_wsl:/home/mrfrog/code/lawundry_test/Dataset`，
於該機 tmux 中以 uv venv 執行（資料量大、SSH 易斷，務必用 tmux）。

```bash
LCR_DATASET_ROOT=/home/mrfrog/code/lawundry_test/Dataset \
  uv run python experiments/01_subset_filter.py
```

## 結果（首次完整執行）

| 指標 | 數值 |
|------|------|
| 掃描刑事判決總數 | 532,276 |
| 命中子集 | **59,819（11.2%）** |
| 涵蓋法院數 | 21（地方法院） |

### Top 案由

公共危險 29,554 / 過失傷害 9,717 / 過失致死 2,015 / 業務過失傷害 1,255 / 業務過失致死 818…

### 資料結構（重要，修正過）

實際為**兩層**：`Dataset/<院別>刑事/<年月批次>/<判決>.json`
（非最初誤判的三層。`iter_criminal_files` 已對應修正。）

## 發現與待辦

1. **「聲明異議」類佔約 1 萬筆需再過濾**：
   「違反道路交通管理處罰條例聲明異議」(4,102)、「聲明異議」(3,690)、
   「交管條例聲異」(2,144) 等，是「對交通裁罰不服的程序案件」，
   非事故實體判決，與使用者需求不符。
   → 下一階段（切段/抽取）以 JCASE 含「聲」或案由含「聲明異議」排除。

2. **少數檔案編碼損壞**：遇 UnicodeDecodeError，已在 except 加入該例外略過。

3. **子集偏大（5.98 萬）**：若實驗階段嫌大，可進一步限制案由
   （去掉聲明異議後約 4.5 萬），或抽樣。

## 產物

`data/processed/subset.jsonl`（每行一筆 metadata + source_path），
不進版控（.gitignore data/）。下一步切段需依 source_path 回讀 JFULL。
