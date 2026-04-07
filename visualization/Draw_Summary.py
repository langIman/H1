"""
实验总结图：简单数据集 vs 复杂数据集对比
布局：ROC 曲线（上）| 指标小表（中）| 文字总结（下）
"""

import glob
import json
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.metrics import roc_curve, auc, precision_recall_curve

matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["font.family"] = "Noto Sans CJK JP"
matplotlib.rcParams["font.size"]   = 9

# ─── 配置 ───────────────────────────────────────────────────────────────────
# [可选] 参与对比的数据集，key 为图表显示名称，value 中：
#   "dataset_type" 对应 results/ 下的子目录名
#   "infer_path"   指定推理文件路径，None 表示自动使用该目录下最新的 infer_*.json
DATASETS = {
    "简单数据集": {
        "dataset_type": "easy",
        "infer_path":   None,
        "color":        "steelblue",
    },
    "复杂数据集": {
        "dataset_type": "complex",
        "infer_path":   None,
        "color":        "darkorange",
    },
}
OUTPUT_PATH = "results/experiment_summary.png"
# ────────────────────────────────────────────────────────────────────────────


def find_latest_infer(result_dir: str) -> str:
    """返回 result_dir 下最新的 infer_*.json 文件路径。"""
    files = sorted(glob.glob(os.path.join(result_dir, "infer_*.json")))
    if not files:
        raise FileNotFoundError(
            f"在 {result_dir} 下未找到推理结果文件，请先运行 infer.py。"
        )
    return files[-1]


def load_detail(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    samples      = data["samples"]
    true_labels  = np.array([s["true_label"]            for s in samples])
    contra_probs = np.array([s["probs"]["contradiction"] for s in samples])
    return true_labels, contra_probs


def best_f1_info(true_labels, contra_probs):
    precision, recall, thresholds = precision_recall_curve(true_labels, contra_probs)
    f1  = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-8)
    idx = np.argmax(f1)
    return {
        "threshold": thresholds[idx],
        "f1":        f1[idx],
        "precision": precision[idx],
        "recall":    recall[idx],
    }


def draw_roc(ax, true_labels, contra_probs, best, color, title):
    fpr, tpr, thresholds = roc_curve(true_labels, contra_probs)
    roc_auc  = auc(fpr, tpr)
    best_idx = np.argmin(np.abs(thresholds - best["threshold"]))
    bfpr, btpr = fpr[best_idx], tpr[best_idx]

    ax.plot(fpr, tpr, color=color, lw=2, label=f"AUC = {roc_auc:.4f}")
    ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--", label="随机基线")
    ax.scatter(bfpr, btpr, color="crimson", zorder=5, s=55)
    ax.annotate(f" 阈值={best['threshold']:.4f}\n F1={best['f1']:.4f}",
                xy=(bfpr, btpr), fontsize=8, color="crimson")

    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    ax.set_xlabel("假正率 (FPR)", fontsize=9)
    ax.set_ylabel("真正率 (TPR)", fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=5)
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    return roc_auc


def draw_metric_table(ax, best, roc_auc):
    ax.axis("off")
    rows = [
        ["AUC",        f"{roc_auc:.4f}"],
        ["最优阈值",   f"{best['threshold']:.4f}"],
        ["最优 F1",    f"{best['f1']:.4f}"],
        ["Precision",  f"{best['precision']:.4f}"],
        ["Recall",     f"{best['recall']:.4f}"],
    ]
    tbl = ax.table(
        cellText=rows,
        colLabels=["指标", "数值"],
        loc="center", cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1.1, 1.35)
    for col in range(2):
        tbl[(0, col)].set_facecolor("#d0e4f7")
        tbl[(0, col)].set_text_props(fontweight="bold")


def main():
    results = {}
    for name, cfg in DATASETS.items():
        result_dir = f"results/{cfg['dataset_type']}"
        infer_path = cfg["infer_path"] or find_latest_infer(result_dir)
        print(f"{name}: 读取推理文件 {infer_path}")
        true_labels, contra_probs = load_detail(infer_path)
        results[name] = {
            "true_labels":  true_labels,
            "contra_probs": contra_probs,
            "best":         best_f1_info(true_labels, contra_probs),
            "color":        cfg["color"],
            "auc":          None,
        }

    # 行比例：ROC(3) : 小表(1.6) : 文字(1)
    fig = plt.figure(figsize=(12, 9.5))
    gs  = gridspec.GridSpec(
        3, 2,
        height_ratios=[3, 1.6, 1],
        hspace=0.45, wspace=0.3,
        left=0.07, right=0.96, top=0.94, bottom=0.04,
    )

    names = list(results.keys())

    # 第一行：ROC 曲线
    for col, name in enumerate(names):
        d = results[name]
        ax = fig.add_subplot(gs[0, col])
        results[name]["auc"] = draw_roc(
            ax, d["true_labels"], d["contra_probs"],
            d["best"], d["color"], f"ROC 曲线 — {name}",
        )

    # 第二行：指标小表
    for col, name in enumerate(names):
        ax = fig.add_subplot(gs[1, col])
        draw_metric_table(ax, results[name]["best"], results[name]["auc"])
        ax.set_title(f"{name} — 最优 F1 指标", fontsize=9, fontweight="bold", pad=3)

    # 第三行：文字总结
    ax_txt = fig.add_subplot(gs[2, :])
    ax_txt.axis("off")

    easy_b = results["简单数据集"]["best"]
    comp_b = results["复杂数据集"]["best"]
    # 手动换行：matplotlib 对中文不自动折行，每句单独一行
    summary = "\n".join([
        "实验总结：两组实验均使用预训练 DeBERTa-v3-large 模型对 UAV 情报文本对进行自然语言推理（NLI）矛盾检测。",
        f"简单数据集由单字段短句构成，矛盾特征显著，模型取得 AUC={results['简单数据集']['auc']:.4f}、"
        f"最优 F1={easy_b['f1']:.4f}（阈值={easy_b['threshold']:.4f}），表现较好。",
        f"复杂数据集包含多字段长句，矛盾更隐蔽，AUC 下降至 {results['复杂数据集']['auc']:.4f}，"
        f"最优 F1 降至 {comp_b['f1']:.4f}（阈值={comp_b['threshold']:.4f}）。",
        f"复杂集的 Recall 更高（{comp_b['recall']:.4f} vs {easy_b['recall']:.4f}），"
        f"说明模型在信息密集的句子中倾向于更宽松的矛盾判定，漏检减少但误报增多。",
    ])
    ax_txt.text(
        0.5, 0.5, summary,
        ha="center", va="center", fontsize=9,
        transform=ax_txt.transAxes, multialignment="left",
        linespacing=1.8,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f5f5f5", edgecolor="#cccccc"),
    )

    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"实验总结图已保存至: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
