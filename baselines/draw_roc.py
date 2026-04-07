"""
基线方法 ROC 曲线绘制
读取 baselines/results/{DATASET_TYPE}/baseline_{METHOD}_*.json，绘制 ROC 曲线。
输出文件名与推理结果时间戳对应：roc_{METHOD}_{timestamp}.png
"""

import glob
import json
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve

matplotlib.rcParams["axes.unicode_minus"] = False

# ─── 配置 ───────────────────────────────────────────────────────────────────
# [可选] 数据集类型
#   "easy" | "complex" | "en_easy" | "en_complex"
DATASET_TYPE = "easy"

# [可选] 基线方法
#   "jaccard"   - A 组：Jaccard + 否定词
#   "embedding" - B 组：sentence-transformers 余弦相似度
METHOD = "jaccard"

RESULT_DIR = f"baselines/results/{DATASET_TYPE}"
# [可选] 指定结果文件路径；None 表示自动使用 RESULT_DIR 下最新的对应文件
BASELINE_PATH = None
# ────────────────────────────────────────────────────────────────────────────


def find_latest(result_dir: str, method: str) -> str:
    """返回 result_dir 下最新的 baseline_{method}_*.json 文件路径。"""
    files = sorted(glob.glob(os.path.join(result_dir, f"baseline_{method}_*.json")))
    if not files:
        raise FileNotFoundError(
            f"在 {result_dir} 下未找到 {method} 基线结果，请先运行对应基线脚本。"
        )
    return files[-1]


def load_data(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    samples      = data["samples"]
    true_labels  = np.array([s["true_label"]            for s in samples])
    contra_probs = np.array([s["probs"]["contradiction"] for s in samples])
    return true_labels, contra_probs, data["metadata"]


def find_best_f1_threshold(true_labels, contra_probs):
    precision, recall, thresholds = precision_recall_curve(true_labels, contra_probs)
    f1_scores  = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-8)
    best_idx   = np.argmax(f1_scores)
    return thresholds[best_idx], f1_scores[best_idx], precision[best_idx], recall[best_idx]


def plot_roc(true_labels, contra_probs, best_threshold, best_f1, output_path, meta):
    fpr, tpr, thresholds = roc_curve(true_labels, contra_probs)
    roc_auc  = auc(fpr, tpr)
    best_idx = np.argmin(np.abs(thresholds - best_threshold))
    best_fpr, best_tpr = fpr[best_idx], tpr[best_idx]

    method_label = {
        "jaccard":          "Jaccard Similarity",
        "embedding_cosine": "Embedding Cosine",
    }.get(meta.get("method", ""), meta.get("method", "Baseline"))

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(fpr, tpr, color="steelblue", lw=2,
            label=f"ROC Curve (AUC = {roc_auc:.4f})")
    ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--", label="Random Baseline")
    ax.scatter(best_fpr, best_tpr, color="crimson", zorder=5, s=80,
               label=f"Best F1 Threshold = {best_threshold:.4f}\n"
                     f"(FPR={best_fpr:.4f}, TPR={best_tpr:.4f})")
    ax.annotate(f"  threshold={best_threshold:.4f}\n  Best F1={best_f1:.4f}",
                xy=(best_fpr, best_tpr), fontsize=9, color="crimson")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (FPR)", fontsize=12)
    ax.set_ylabel("True Positive Rate (TPR)", fontsize=12)
    ax.set_title(f"ROC Curve - {method_label}", fontsize=13)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"ROC 曲线已保存至: {output_path}")
    return roc_auc


def main():
    baseline_path = BASELINE_PATH or find_latest(RESULT_DIR, METHOD)
    print(f"读取基线结果: {baseline_path}")

    basename    = os.path.basename(baseline_path)
    # baseline_{method}_{timestamp}.json → roc_{method}_{timestamp}.png
    timestamp   = basename[len(f"baseline_{METHOD}_"):-len(".json")]
    output_path = os.path.join(RESULT_DIR, f"roc_{METHOD}_{timestamp}.png")

    true_labels, contra_probs, meta = load_data(baseline_path)
    print(f"样本数: {len(true_labels)} | 方法: {meta.get('method')}")

    best_threshold, best_f1, best_precision, best_recall = \
        find_best_f1_threshold(true_labels, contra_probs)

    print(f"\n─── 最优 F1 阈值 ───────────────────────────────")
    print(f"  阈值      : {best_threshold:.4f}")
    print(f"  F1        : {best_f1:.4f}")
    print(f"  Precision : {best_precision:.4f}")
    print(f"  Recall    : {best_recall:.4f}")
    print(f"────────────────────────────────────────────────")

    roc_auc = plot_roc(true_labels, contra_probs, best_threshold, best_f1, output_path, meta)
    print(f"AUC       : {roc_auc:.4f}")


if __name__ == "__main__":
    main()
