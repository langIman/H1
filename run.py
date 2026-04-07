"""
UAV NLI 矛盾检测 - 一键运行脚本
自动完成：数据集生成（按需）→ 模型推理 → ROC 曲线绘制

用法：
  python run.py --dataset easy
  python run.py -d en_complex -m cross-encoder/nli-deberta-v3-large -b 8
"""

import argparse
import importlib.util
import os

_DATA_FILES = {
    "easy":       "data/uav_nli_dataset.json",
    "complex":    "data/uav_nli_dataset_complex.json",
    "en_easy":    "data/uav_nli_dataset_en_easy.json",
    "en_complex": "data/uav_nli_dataset_en_complex.json",
}
_DATA_GEN_SCRIPTS = {
    "easy":       "data_gen/DataGen.py",
    "complex":    "data_gen/DataGen_complex.py",
    "en_easy":    "data_gen/DataGen_en_easy.py",
    "en_complex": "data_gen/DataGen_en_complex.py",
}


def _load(name, path):
    """从文件路径加载 Python 模块并执行其顶层代码。"""
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _banner(step, title):
    print(f"\n{'='*60}\n[{step}/3] {title}\n{'='*60}")


def step_data_gen(dataset):
    _banner(1, f"生成数据集: {_DATA_GEN_SCRIPTS[dataset]}")
    _load("datagen", _DATA_GEN_SCRIPTS[dataset])


def step_infer(dataset, model, batch_size):
    _banner(2, "模型推理")
    mod = _load("infer", "inference/infer.py")
    mod.DATASET_TYPE = dataset
    mod.MODEL_NAME   = model
    mod.BATCH_SIZE   = batch_size
    mod.DATA_PATH    = _DATA_FILES[dataset]
    mod.RESULT_DIR   = f"results/{dataset}"
    return mod.main()  # 返回生成的 infer_{timestamp}.json 路径


def step_roc(dataset, infer_path):
    _banner(3, "绘制 ROC 曲线")
    mod = _load("draw_roc", "visualization/Draw_Roc.py")
    mod.DATASET_TYPE = dataset
    mod.RESULT_DIR   = f"results/{dataset}"
    mod.INFER_PATH   = infer_path  # 与本次推理结果绑定
    mod.main()


def main():
    parser = argparse.ArgumentParser(
        description="UAV NLI 矛盾检测一键运行",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset", "-d",
        choices=["easy", "complex", "en_easy", "en_complex"],
        required=True,
        help="数据集类型",
    )
    parser.add_argument(
        "--model", "-m",
        default="cross-encoder/nli-deberta-v3-large",
        help="HuggingFace NLI 模型名",
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=16,
        help="推理 batch size，显存不足时调小",
    )
    args = parser.parse_args()

    # 步骤一：数据集（已存在则跳过）
    if os.path.exists(_DATA_FILES[args.dataset]):
        print(f"[1/3] 数据集已存在，跳过生成: {_DATA_FILES[args.dataset]}")
    else:
        step_data_gen(args.dataset)

    # 步骤二：模型推理
    infer_path = step_infer(args.dataset, args.model, args.batch_size)

    # 步骤三：ROC 曲线（与本次推理结果时间戳对应）
    step_roc(args.dataset, infer_path)

    print(f"\n全部完成！结果保存在 results/{args.dataset}/")


if __name__ == "__main__":
    main()
