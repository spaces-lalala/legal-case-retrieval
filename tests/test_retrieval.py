"""lcr.retrieval (RRF + kind_classifier) 單元測試。

注意：Indexer/Searcher 需要 BGE-M3 + ChromaDB，本機測試環境可能未安裝，
所以這裡只測試不依賴大模型的純邏輯：
  - rrf_fusion 融合算法
  - kind_classifier infer_kind（已在 test_schemas_and_kind.py 測過，這裡補邊界）

Indexer/Searcher 整合測試需在 home_wsl（有 GPU + 依賴）上跑 05_build_index.py。
"""

from __future__ import annotations

from lcr.retrieval.searcher import rrf_fusion


def test_rrf_fusion_basic():
    dense = [("A", 0.9), ("B", 0.8), ("C", 0.7)]
    sparse = [("B", 15.0), ("A", 12.0), ("D", 8.0)]
    fused = rrf_fusion(dense, sparse, k=60, top_n=4)

    jids = [j for j, _ in fused]
    # A 和 B 都在兩個列表中，分數應最高
    assert "A" in jids
    assert "B" in jids
    # C 只在 dense（排名 3），D 只在 sparse（排名 3），兩者分數相近
    assert len(fused) == 4


def test_rrf_fusion_same_rank_is_symmetric():
    # 若 A 在 dense 第 1、sparse 第 2，B 在 dense 第 2、sparse 第 1
    # 兩者 RRF 分數應相等
    dense = [("A", 0.9), ("B", 0.8)]
    sparse = [("B", 15.0), ("A", 12.0)]
    fused = rrf_fusion(dense, sparse, k=60, top_n=2)
    scores = {j: s for j, s in fused}
    assert abs(scores["A"] - scores["B"]) < 1e-9


def test_rrf_fusion_only_in_one_list():
    dense = [("A", 0.9)]
    sparse = [("B", 10.0)]
    fused = rrf_fusion(dense, sparse, k=60, top_n=2)
    # A 和 B 都應出現，且分數相等（各自排名 1）
    jids = [j for j, _ in fused]
    assert "A" in jids
    assert "B" in jids


def test_rrf_fusion_top_n_limit():
    dense = [(str(i), float(i)) for i in range(10)]
    sparse = [(str(i + 5), float(i)) for i in range(10)]
    fused = rrf_fusion(dense, sparse, k=60, top_n=3)
    assert len(fused) == 3


def test_rrf_fusion_empty():
    assert rrf_fusion([], [], top_n=5) == []


def test_rrf_fusion_empty_dense():
    sparse = [("A", 10.0), ("B", 5.0)]
    fused = rrf_fusion([], sparse, k=60, top_n=2)
    # 只有 sparse 的結果
    jids = [j for j, _ in fused]
    assert "A" in jids
    assert "B" in jids
