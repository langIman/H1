# UAV 情报矛盾检测 - 预实验

基于 DeBERTa-v3-large 的 NLI（自然语言推理）方法，对多 UAV 上报情报进行矛盾检测。

---

## 项目结构

```
NLI_UAVS/
├── data/
│   └── uav_nli_dataset.json        # 数据集：矛盾组（label=1）与非矛盾组（label=0）
├── results/
│   ├── nli_test_record.json        # 各阈值评估指标记录（追加写入）
│   ├── nli_inference_detail.json   # 逐样本推理概率详情（三类概率）
│   └── roc_curve.png               # ROC 曲线图
├── DataGen.py                      # 数据集生成脚本
├── DeBV3L_detect.py                # 模型推理与评估脚本
├── Draw_Roc.py                     # ROC 曲线绘制脚本
└── README.md
```

---

## 文件说明

### 脚本

| 文件 | 作用 |
|------|------|
| `DataGen.py` | 基于词库模板生成 UAV 情报文本对，支持独立控制矛盾组与非矛盾组数量，输出至 `data/uav_nli_dataset.json` |
| `DeBV3L_detect.py` | 加载预训练 DeBERTa-v3-large，对数据集进行 NLI 推理；支持多线程并行计算多个阈值下的评估指标（Accuracy / Precision / Recall / F1），结果追加写入 `results/nli_test_record.json`；可选输出逐样本三类概率至 `results/nli_inference_detail.json` |
| `Draw_Roc.py` | 读取 `results/nli_inference_detail.json`，绘制 ROC 曲线并计算最优 F1 阈值，图片保存至 `results/roc_curve.png` |

### 数据文件

| 文件 | 说明 |
|------|------|
| `data/uav_nli_dataset.json` | 数据集，每条包含 `premise`（UAV-A 报告）、`hypothesis`（UAV-B 报告）、`label`（1=矛盾，0=非矛盾） |
| `results/nli_test_record.json` | 每次运行的评估记录列表，每条包含时间戳、推理参数（模型名、阈值）、评估指标（TP/FP/TN/FN 及 Accuracy/Precision/Recall/F1） |
| `results/nli_inference_detail.json` | 逐样本推理结果，每条包含原文、真实标签、三类概率（contradiction / entailment / neutral） |
| `results/roc_curve.png` | ROC 曲线图，标注最优 F1 阈值及对应工作点 |

---

## 运行流程

```bash
# 1. 生成数据集
python DataGen.py

# 2. 模型推理与评估
python DeBV3L_detect.py

# 3. 绘制 ROC 曲线
python Draw_Roc.py
```

---

## 模型说明

- 模型：`cross-encoder/nli-deberta-v3-large`
- 矛盾判定：`contradiction` 概率 >= 阈值 则判定为矛盾
- 阈值列表在 `DeBV3L_detect.py` 的 `THRESHOLDS` 配置项中修改
