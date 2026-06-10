"""實驗 02：結構切段。

讀 subset.jsonl（或 corpus.jsonl），對每筆回讀 JFULL 做結構切段，輸出：
  1. data/processed/segmented.jsonl — 每行含 jid/metadata + main/facts/reasoning + layout
  2. 終端統計：layout 分布、完整率

用法（repo 根目錄；資料在 home_wsl，建議 tmux）：
    # 從 corpus.jsonl（推薦，已過濾程序性案件）
    LCR_DATASET_ROOT=/home/mrfrog/code/lawundry_test/Dataset \\
    LCR_PROCESSED_DIR=/home/mrfrog/data/processed \\
      uv run python experiments/02_segment.py --input corpus

    # 從原始 subset.jsonl（舊版）
    LCR_DATASET_ROOT=... LCR_PROCESSED_DIR=... \\
      uv run python experiments/02_segment.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lcr.config import settings  # noqa: E402
from lcr.data.segment import segment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        choices=["subset", "corpus"],
        default="subset",
        help="輸入來源：subset.jsonl（舊版）或 corpus.jsonl（推薦）",
    )
    args = parser.parse_args()

    if args.input == "corpus":
        input_path = settings.processed_dir / "corpus.jsonl"
        input_label = "corpus.jsonl"
    else:
        input_path = settings.processed_dir / "subset.jsonl"
        input_label = "subset.jsonl"

    if not input_path.exists():
        print(f"[錯誤] 找不到 {input_path}")
        return 1

    dataset_root = settings.dataset_root
    if not dataset_root.exists():
        print(f"[錯誤] 找不到資料根目錄：{dataset_root}")
        return 1

    out_path = settings.processed_dir / "segmented.jsonl"
    print(f"輸入：{input_label}（{input_path}）")
    print(f"輸出：{out_path}")

    total = 0
    read_fail = 0
    kept = 0
    layout_counter: Counter[str] = Counter()
    complete = 0

    with input_path.open(encoding="utf-8") as fin, out_path.open(
        "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            total += 1
            r = json.loads(line)

            src = dataset_root / r["source_path"]
            try:
                with src.open(encoding="utf-8") as fp:
                    d = json.loads(fp.read(), strict=False)
            except (OSError, ValueError, UnicodeDecodeError):
                read_fail += 1
                continue

            seg = segment(d.get("JFULL", ""))
            layout_counter[seg.layout] += 1
            if seg.is_complete:
                complete += 1

            kept += 1
            fout.write(
                json.dumps(
                    {
                        "jid": r["jid"],
                        "title": r.get("title", r.get("JTITLE", "")),
                        "jcase": r.get("jcase", r.get("JCASE", "")),
                        "court": r.get("court", ""),
                        "jdate": r.get("jdate", r.get("JDATE", "")),
                        "kind": r.get("kind", "criminal"),
                        "main": seg.main,
                        "facts": seg.facts,
                        "reasoning": seg.reasoning,
                        "layout": seg.layout,
                        "is_complete": seg.is_complete,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            if total % 5000 == 0:
                print(f"  進度：{total:,} / 失敗：{read_fail} / 完成：{kept:,}")

    print("\n" + "=" * 50)
    print(f"輸入：{total:,}")
    print(f"讀取失敗：{read_fail:,}")
    print(f"切段輸出：{kept:,}")

    print("\n--- layout 分布 ---")
    for lay, c in layout_counter.most_common():
        print(f"  {lay}: {c:,} ({c / kept * 100:.1f}%)")

    print(
        f"\n--- 完整率：{complete:,}/{kept:,} "
        f"({complete / kept * 100:.1f}%) ---"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
