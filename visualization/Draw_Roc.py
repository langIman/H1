"""
ROC 曲线绘制 & 最优 F1 阈值分析
数据来源：nli_inference_detail.json
- 正类概率：contradiction
- 负类概率：entailment + neutral
"""

import glob
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from sklearn.metrics import roc_curve, auc, precision_recall_curve

# ─── 配置 ───────────────────────────────────────────────────────────────────
# [可选] 数据集类型，须与 infer.py 中的 DATASET_TYPE 保持一致
#   "easy" | "complex" | "en_easy" | "en_complex"
DATASET_TYPE = "en_complex"

RESULT_DIR  = f"results/{DATASET_TYPE}"
# [可选] 指定推理结果文件路径；None 表示自动使用 RESULT_DIR 下最新的 infer_*.json
INFER_PATH  = None
# 输出文件名由推理文件时间戳自动派生：roc_{timestamp}.png
# ────────────────────────────────────────────────────────────────────────────

matplotlib.rcParams["axes.unicode_minus"] = False


def find_latest_infer(result_dir: str) -> str:
    """返回 result_dir 下最新的 infer_*.json 文件路径。"""
    files = sorted(glob.glob(os.path.join(result_dir, "infer_*.json")))
    if not files:
        raise FileNotFoundError(
            f"在 {result_dir} 下未找到推理结果文件，请先运行 infer.py。"
        )
    return files[-1]


def load_data(path):
    """读取推理详情，提取真实标签和矛盾概率。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data["samples"]
    true_labels  = np.array([s["true_label"]              for s in samples])
    contra_probs = np.array([s["probs"]["contradiction"]   for s in samples])
    return true_labels, contra_probs


def find_best_f1_threshold(true_labels, contra_probs):
    """遍历 precision-recall 曲线上的所有阈值，找到 F1 最大时对应的阈值。"""
    precision, recall, thresholds = precision_recall_curve(true_labels, contra_probs)

    # precision_recall_curve 返回的 thresholds 比 precision/recall 少一个元素
    # 最后一个点对应"全部预测为正"，无实际阈值意义，截掉对齐
    f1_scores = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-8)

    best_idx       = np.argmax(f1_scores)
    best_threshold = thresholds[best_idx]
    best_f1        = f1_scores[best_idx]
    best_precision = precision[best_idx]
    best_recall    = recall[best_idx]

    return best_threshold, best_f1, best_precision, best_recall


def plot_roc(true_labels, contra_probs, best_threshold, best_f1, output_path):
    """绘制 ROC 曲线，并在最优 F1 阈值对应的工作点上标注。"""
    fpr, tpr, thresholds = roc_curve(true_labels, contra_probs)
    roc_auc = auc(fpr, tpr)

    # 找到最优阈值在 ROC 曲线上对应的点（取最近邻）
    best_idx = np.argmin(np.abs(thresholds - best_threshold))
    best_fpr = fpr[best_idx]
    best_tpr = tpr[best_idx]

    fig, ax = plt.subplots(figsize=(7, 6))

    # ROC 曲线
    ax.plot(fpr, tpr, color="steelblue", lw=2,
            label=f"ROC Curve (AUC = {roc_auc:.4f})")

    # 对角随机猜测基线
    ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--", label="Random Baseline")

    # 最优 F1 工作点
    ax.scatter(best_fpr, best_tpr, color="crimson", zorder=5, s=80,
               label=f"Best F1 Threshold = {best_threshold:.4f}\n"
                     f"(FPR={best_fpr:.4f}, TPR={best_tpr:.4f})")
    ax.annotate(f"  threshold={best_threshold:.4f}\n  Best F1={best_f1:.4f}",
                xy=(best_fpr, best_tpr),
                fontsize=9, color="crimson")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (FPR)", fontsize=12)
    ax.set_ylabel("True Positive Rate (TPR)", fontsize=12)
    ax.set_title("ROC Curve - UAV NLI Contradiction Detection", fontsize=13)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"ROC 曲线已保存至: {output_path}")
    return roc_auc


def main():
    infer_path = INFER_PATH or find_latest_infer(RESULT_DIR)
    print(f"读取推理文件: {infer_path}")

    # 从 infer_{timestamp}.json 提取时间戳，输出 roc_{timestamp}.png
    basename    = os.path.basename(infer_path)
    timestamp   = basename[len("infer_"):-len(".json")]
    output_path = os.path.join(RESULT_DIR, f"roc_{timestamp}.png")

    true_labels, contra_probs = load_data(infer_path)
    print(f"加载数据: {len(true_labels)} 条  "
          f"(矛盾: {true_labels.sum()}  非矛盾: {(true_labels==0).sum()})")

    best_threshold, best_f1, best_precision, best_recall = \
        find_best_f1_threshold(true_labels, contra_probs)

    print(f"\n─── 最优 F1 阈值 ───────────────────────────────")
    print(f"  阈值      : {best_threshold:.4f}")
    print(f"  F1        : {best_f1:.4f}")
    print(f"  Precision : {best_precision:.4f}")
    print(f"  Recall    : {best_recall:.4f}")
    print(f"────────────────────────────────────────────────")

    roc_auc = plot_roc(true_labels, contra_probs, best_threshold, best_f1, output_path)
    print(f"AUC       : {roc_auc:.4f}")


if __name__ == "__main__":
    main()
