"""
基线方法 A：Jaccard 词汇重叠（纯规则，无领域知识）
矛盾得分 = Jaccard(premise, hypothesis)

假设：矛盾对描述同一目标，词汇重叠较高；非矛盾对话题不同，重叠较低。
不使用任何否定词表或领域先验，完全无监督。
输出格式与 infer.py 一致，可直接用 draw_roc.py 可视化。
"""

import json
import os
import re
import time
from datetime import datetime

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
DATA_PATH  = _DATA_FILES[DATASET_TYPE]
RESULT_DIR = f"baselines/results/{DATASET_TYPE}"
# ────────────────────────────────────────────────────────────────────────────


def tokenize(text: str) -> set:
    """中文按字符分词，英文按空格分词，统一小写。"""
    if re.search(r"[\u4e00-\u9fff]", text):
        return set(text.replace(" ", ""))
    return set(text.lower().split())


def jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"加载数据: {len(data)} 条样本，数据集类型: {DATASET_TYPE}")

    t_start = time.perf_counter()
    samples = []
    for d in data:
        score = round(jaccard(tokenize(d["premise"]), tokenize(d["hypothesis"])), 4)
        samples.append({
            "premise":    d["premise"],
            "hypothesis": d["hypothesis"],
            "true_label": d["label"],
            "probs": {"contradiction": score},  # 兼容 draw_roc.py
        })
    t_end = time.perf_counter()

    total_time_s   = round(t_end - t_start, 3)
    avg_latency_ms = round(total_time_s / len(data) * 1000, 3)
    print(f"耗时: {total_time_s} s | 平均每样本: {avg_latency_ms} ms")

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(RESULT_DIR, f"baseline_jaccard_{timestamp}.json")
    os.makedirs(RESULT_DIR, exist_ok=True)

    output = {
        "metadata": {
            "method":         "jaccard",
            "dataset_type":   DATASET_TYPE,
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
