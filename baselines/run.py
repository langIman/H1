"""
基线方法一键运行脚本
自动完成：基线推理 → ROC 曲线绘制

用法：
  python baselines/run.py -d easy                      # 同时跑两组基线
  python baselines/run.py -d easy -m jaccard           # 只跑 A 组
  python baselines/run.py -d en_complex -m embedding   # 只跑 B 组
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


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _banner(step, total, title):
    print(f"\n{'='*60}\n[{step}/{total}] {title}\n{'='*60}")


def step_jaccard(dataset, step, total):
    _banner(step, total, "A 组：Jaccard + 否定词基线推理")
    mod = _load("jaccard_baseline", "baselines/jaccard_baseline.py")
    mod.DATASET_TYPE = dataset
    mod.DATA_PATH    = _DATA_FILES[dataset]
    mod.RESULT_DIR   = f"baselines/results/{dataset}"
    return mod.main()


def step_embedding(dataset, step, total):
    _banner(step, total, "B 组：嵌入余弦相似度基线推理")
    mod = _load("embedding_baseline", "baselines/embedding_baseline.py")
    mod.DATASET_TYPE = dataset
    mod.DATA_PATH    = _DATA_FILES[dataset]
    mod.RESULT_DIR   = f"baselines/results/{dataset}"
    return mod.main()


def step_roc(dataset, method, baseline_path, step, total):
    _banner(step, total, f"绘制 ROC 曲线：{method}")
    mod = _load("draw_roc", "baselines/draw_roc.py")
    mod.DATASET_TYPE  = dataset
    mod.METHOD        = method
    mod.RESULT_DIR    = f"baselines/results/{dataset}"
    mod.BASELINE_PATH = baseline_path
    mod.main()


def main():
    parser = argparse.ArgumentParser(
        description="基线方法一键运行",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset", "-d",
        choices=["easy", "complex", "en_easy", "en_complex"],
        required=True,
        help="数据集类型",
    )
    parser.add_argument(
        "--method", "-m",
        choices=["jaccard", "embedding", "all"],
        default="all",
        help="运行的基线方法，默认同时运行两组",
    )
    args = parser.parse_args()

    methods  = ["jaccard", "embedding"] if args.method == "all" else [args.method]
    total    = len(methods) * 2  # 每组：推理 + 可视化

    step = 1
    paths = {}
    for m in methods:
        if m == "jaccard":
            paths[m] = step_jaccard(args.dataset, step, total)
        else:
            paths[m] = step_embedding(args.dataset, step, total)
        step += 1

    for m in methods:
        step_roc(args.dataset, m, paths[m], step, total)
        step += 1

    print(f"\n全部完成！结果保存在 baselines/results/{args.dataset}/")


if __name__ == "__main__":
    main()
