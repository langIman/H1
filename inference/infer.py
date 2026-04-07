"""
UAV 情报矛盾检测 - 步骤一：模型推理
读取数据集，运行 DeBERTa-v3-large NLI 推理，将每个样本的三类概率保存至文件。
推理结果与阈值无关，保存后可反复用于步骤二的指标计算，无需重复跑模型。
"""

import json
import os
import platform
import time
import torch
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
from tqdm import tqdm

# ─── 配置 ───────────────────────────────────────────────────────────────────
# [可选] 数据集类型，决定读取哪个数据集文件及结果保存路径
#   "easy"       - 简单中文数据集
#   "complex"    - 复杂中文数据集
#   "en_easy"    - 简单英文数据集
#   "en_complex" - 复杂英文数据集
DATASET_TYPE = "easy"

_DATA_FILES = {
    "easy":       "data/uav_nli_dataset.json",
    "complex":    "data/uav_nli_dataset_complex.json",
    "en_easy":    "data/uav_nli_dataset_en_easy.json",
    "en_complex": "data/uav_nli_dataset_en_complex.json",
}

# [可选] HuggingFace 模型名，可替换为其他 NLI cross-encoder 模型
# [可选] HuggingFace 模型名，可替换为其他 NLI cross-encoder 模型
MODEL_NAME  = "cross-encoder/nli-deberta-v3-large"
DATA_PATH   = _DATA_FILES[DATASET_TYPE]
RESULT_DIR  = f"results/{DATASET_TYPE}"
# [可选] 每批推理样本数，显存不足时调小
BATCH_SIZE  = 1
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
# ────────────────────────────────────────────────────────────────────────────


def get_device_info() -> str:
    """返回当前推理设备的描述字符串（GPU 型号或 CPU 名称）。"""
    if torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    name = platform.processor()
    return f"CPU: {name}" if name else "CPU"


def load_model(model_name: str):
    """加载分词器和 NLI 分类模型，切换至推理模式。"""
    print(f"加载模型: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model     = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.to(DEVICE)
    model.eval()
    label_names = model.config.id2label
    print(f"设备: {DEVICE} | 标签映射: {label_names}")
    return tokenizer, model, label_names


def predict_batch(premises, hypotheses, tokenizer, model, label_names):
    """对一个 batch 做 NLI 推理，返回每个样本的完整概率字典列表。"""
    enc = tokenizer(
        premises, hypotheses,
        padding=True, truncation=True,
        max_length=512, return_tensors="pt"
    )
    enc = {k: v.to(DEVICE) for k, v in enc.items()}

    with torch.no_grad():
        logits = model(**enc).logits

    probs = softmax(logits, dim=-1).cpu()
    return [
        {label_names[i]: round(p.item(), 4) for i, p in enumerate(row)}
        for row in probs
    ]


def main():
    # 1. 加载数据集
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"加载数据: {len(data)} 条样本，数据集类型: {DATASET_TYPE}")

    premises    = [d["premise"]    for d in data]
    hypotheses  = [d["hypothesis"] for d in data]
    true_labels = [d["label"]      for d in data]

    # 2. 加载模型
    tokenizer, model, label_names = load_model(MODEL_NAME)

    # 3. 批量推理，计时（GPU 需 synchronize 确保异步操作完成后再停表）
    all_prob_dicts = []
    t_start = time.perf_counter()
    for i in tqdm(range(0, len(data), BATCH_SIZE), desc="推理中"):
        batch = predict_batch(
            premises[i:i+BATCH_SIZE],
            hypotheses[i:i+BATCH_SIZE],
            tokenizer, model, label_names
        )
        all_prob_dicts.extend(batch)
    if DEVICE == "cuda":
        torch.cuda.synchronize()
    t_end = time.perf_counter()

    total_time_s      = round(t_end - t_start, 3)
    avg_latency_ms    = round(total_time_s / len(data) * 1000, 3)
    print(f"推理耗时: {total_time_s} s | 平均每样本: {avg_latency_ms} ms")

    # 4. 保存推理结果：metadata + 逐样本概率（文件名含时间戳，每次独立存档）
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    detail_path = os.path.join(RESULT_DIR, f"infer_{timestamp}.json")
    os.makedirs(RESULT_DIR, exist_ok=True)

    output = {
        "metadata": {
            "model":          MODEL_NAME,
            "device":         get_device_info(),
            "batch_size":     BATCH_SIZE,
            "total_samples":  len(data),
            "total_time_s":   total_time_s,
            "avg_latency_ms": avg_latency_ms,
        },
        "samples": [
            {
                "premise":    premises[i],
                "hypothesis": hypotheses[i],
                "true_label": true_labels[i],
                "probs":      all_prob_dicts[i],
            }
            for i in range(len(data))
        ],
    }
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"推理完成，{len(data)} 条结果已保存至: {detail_path}")
    print("可运行 evaluate.py 对不同阈值计算分类指标。")
    return detail_path


if __name__ == "__main__":
    main()
