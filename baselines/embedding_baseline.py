"""
基线方法 B：sentence-transformers 余弦相似度
矛盾得分 = 1 - cosine_similarity(premise_emb, hypothesis_emb)
语义距离越大，越可能是矛盾。
输出格式与 infer.py 一致，可直接用 Draw_Roc.py 可视化。
"""

import json
import os
import time
import numpy as np
import torch
from datetime import datetime
from sentence_transformers import SentenceTransformer

# ─── 配置 ───────────────────────────────────────────────────────────────────
# [可选] 数据集类型
#   "easy" | "complex" | "en_easy" | "en_complex"
DATASET_TYPE = "easy"

_DATA_FILES = {
    "easy":       "data/uav_nli_dataset.json",
    "complex":    "data/uav_nli_dataset_complex.json",
    "en_easy":    "data/uav_nli_dataset_en_easy.json",
    "en_complex": "data/uav_nli_dataset_en_complex.json",
}
# [可选] sentence-transformers 模型名
#   多语言（中英均适用）：sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
#   纯英文（更快）：sentence-transformers/all-MiniLM-L6-v2
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DATA_PATH  = _DATA_FILES[DATASET_TYPE]
RESULT_DIR = f"baselines/results/{DATASET_TYPE}"
# [可选] 编码 batch size，显存不足时调小
BATCH_SIZE = 64
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"
# ────────────────────────────────────────────────────────────────────────────


def get_device_info() -> str:
    if torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    return f"CPU"


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"加载数据: {len(data)} 条样本，数据集类型: {DATASET_TYPE}")

    premises    = [d["premise"]    for d in data]
    hypotheses  = [d["hypothesis"] for d in data]
    true_labels = [d["label"]      for d in data]

    print(f"加载模型: {MODEL_NAME}")
    model       = SentenceTransformer(MODEL_NAME, device=DEVICE)
    device_info = get_device_info()
    print(f"设备: {device_info}")

    # 分别编码 premise 和 hypothesis，GPU 需 synchronize 后再停表
    t_start = time.perf_counter()
    emb_p = model.encode(premises,   batch_size=BATCH_SIZE,
                         show_progress_bar=True, convert_to_numpy=True)
    emb_h = model.encode(hypotheses, batch_size=BATCH_SIZE,
                         show_progress_bar=True, convert_to_numpy=True)
    if DEVICE == "cuda":
        torch.cuda.synchronize()
    t_end = time.perf_counter()

    # 矛盾得分 = 1 - 余弦相似度（语义越远越可能矛盾）
    norm_p    = np.linalg.norm(emb_p, axis=1, keepdims=True) + 1e-8
    norm_h    = np.linalg.norm(emb_h, axis=1, keepdims=True) + 1e-8
    cos_sims  = (emb_p / norm_p * emb_h / norm_h).sum(axis=1)
    contra_scores = [round(float(1 - s), 4) for s in cos_sims]

    total_time_s   = round(t_end - t_start, 3)
    avg_latency_ms = round(total_time_s / len(data) * 1000, 3)
    print(f"耗时: {total_time_s} s | 平均每样本: {avg_latency_ms} ms")

    samples = [
        {
            "premise":    premises[i],
            "hypothesis": hypotheses[i],
            "true_label": true_labels[i],
            "probs": {"contradiction": contra_scores[i]},  # 兼容 Draw_Roc.py
        }
        for i in range(len(data))
    ]

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(RESULT_DIR, f"baseline_embedding_{timestamp}.json")
    os.makedirs(RESULT_DIR, exist_ok=True)

    output = {
        "metadata": {
            "method":         "embedding_cosine",
            "model":          MODEL_NAME,
            "device":         device_info,
            "batch_size":     BATCH_SIZE,
            "total_samples":  len(data),
            "total_time_s":   total_time_s,
            "avg_latency_ms": avg_latency_ms,
        },
        "samples": samples,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"结果已保存至: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
