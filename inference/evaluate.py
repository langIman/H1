"""
UAV 情报矛盾检测 - 步骤二：阈值评估
读取步骤一保存的推理概率文件，对多个阈值并行计算分类指标，结果保存为独立文件。
无需重新加载模型，可反复调整 THRESHOLDS 快速对比不同阈值效果。
"""

import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ─── 配置 ───────────────────────────────────────────────────────────────────
# [可选] 数据集类型，须与 infer.py 中的 DATASET_TYPE 保持一致
#   "easy" | "complex" | "en_easy" | "en_complex"
DATASET_TYPE = "en_complex"

RESULT_DIR  = f"results/{DATASET_TYPE}"
# [可选] 指定推理结果文件路径；None 表示自动使用 RESULT_DIR 下最新的 infer_*.json
INFER_PATH  = None

# [可选] 矛盾概率阈值列表，每个阈值独立计算一组指标，可自由增减
THRESHOLDS  = [0.05, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2]
# ────────────────────────────────────────────────────────────────────────────


def compute_metrics(threshold, all_probs, true_labels):
    """给定阈值，基于矛盾概率列表计算分类指标。纯 CPU 运算，线程安全。"""
    tp = fp = tn = fn = 0
    for true_label, prob in zip(true_labels, all_probs):
        pred_label = 1 if prob >= threshold else 0
        if   true_label == 1 and pred_label == 1: tp += 1
        elif true_label == 0 and pred_label == 1: fp += 1
        elif true_label == 0 and pred_label == 0: tn += 1
        else:                                      fn += 1

    total     = len(true_labels)
    accuracy  = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "params": {
            "model":     MODEL_NAME,
            "threshold": threshold,
        },
        "metrics": {
            "total":     total,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "accuracy":  round(accuracy,  4),
            "precision": round(precision, 4),
            "recall":    round(recall,    4),
            "f1":        round(f1,        4),
        },
    }


def find_latest_infer(result_dir: str) -> str:
    """返回 result_dir 下最新的 infer_*.json 文件路径。"""
    files = sorted(glob.glob(os.path.join(result_dir, "infer_*.json")))
    if not files:
        raise FileNotFoundError(
            f"在 {result_dir} 下未找到推理结果文件，请先运行 infer.py。"
        )
    return files[-1]


def main():
    # 1. 确定并读取推理结果文件
    infer_path = INFER_PATH or find_latest_infer(RESULT_DIR)
    print(f"读取推理文件: {infer_path}")
    with open(infer_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    infer_meta  = data["metadata"]
    samples     = data["samples"]
    all_probs   = [s["probs"]["contradiction"] for s in samples]
    true_labels = [s["true_label"]             for s in samples]
    print(f"样本数: {len(samples)} | 模型: {infer_meta['model']}")
    print(f"推理设备: {infer_meta['device']} | "
          f"batch_size: {infer_meta['batch_size']} | "
          f"平均延迟: {infer_meta['avg_latency_ms']} ms/样本")

    # 2. 多线程并行计算各阈值指标
    print(f"启动 {len(THRESHOLDS)} 个线程，并行计算各阈值指标...")
    new_records = [None] * len(THRESHOLDS)

    with ThreadPoolExecutor(max_workers=len(THRESHOLDS)) as executor:
        future_to_idx = {
            executor.submit(compute_metrics, thr, all_probs, true_labels): i
            for i, thr in enumerate(THRESHOLDS)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            new_records[idx] = future.result()

    # 将推理设备和延迟信息注入每条记录的 params
    for r in new_records:
        r["params"]["device"]         = infer_meta["device"]
        r["params"]["avg_latency_ms"] = infer_meta["avg_latency_ms"]

    # 3. 打印汇总
    print("\n─── 各阈值评估结果 ──────────────────────────────────────────────")
    print(f"{'阈值':>6}  {'Acc':>6}  {'Prec':>6}  {'Rec':>6}  {'F1':>6}")
    for r in new_records:
        p, m = r["params"], r["metrics"]
        print(f"{p['threshold']:>6.2f}  {m['accuracy']:>6.4f}  "
              f"{m['precision']:>6.4f}  {m['recall']:>6.4f}  {m['f1']:>6.4f}")
    print("─────────────────────────────────────────────────────────────────")

    # 4. 保存为独立文件（文件名含时间戳，每次运行互不覆盖）
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(RESULT_DIR, f"eval_{timestamp}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_records, f, ensure_ascii=False, indent=2)

    print(f"{len(new_records)} 条记录已保存至: {output_path}")


if __name__ == "__main__":
    main()
