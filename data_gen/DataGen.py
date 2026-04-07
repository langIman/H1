"""
UAV 情报数据集生成（简单中文） —— 场景驱动 + 改述系统
所有对子从同一场景出发，矛盾对翻转一个字段，非矛盾对保持一致。
双风格模板（原始 / 改述）使 Jaccard 分布与 label 完全无关，迫使模型理解语义。
移除 UAV-A/B 前缀，统一使用"侦察报告："，消除实体名干扰。
"""

import json
import random

random.seed(42)

# ─── 基础词库 ────────────────────────────────────────────────────────────────

locations = [
    "X区域", "Y区域", "Z高地", "河谷北侧", "废弃工厂", "3号公路交叉口", "机场跑道末端",
    "A阵地", "B高地", "C渡口", "D村庄", "东侧山脊", "西侧洼地", "南部林区", "北部平原",
    "铁路桥西端", "水库大坝南侧", "油库附近", "码头区域", "山顶观测点",
    "隧道入口", "峡谷出口", "工业园区", "变电站北侧", "雷达站周边",
]
targets = [
    "轻型卡车", "装甲运兵车", "单兵无人机", "雷达站", "通信中继车", "指挥所", "补给车队",
    "自行火炮", "反坦克导弹阵地", "野战医疗队", "无人机蜂群", "电子战车辆",
    "防空导弹系统", "工程保障车", "燃油补给车", "步兵战车", "侦察无人机",
    "火箭炮阵地", "通信基站", "装甲指挥车",
]
directions = ["北", "南", "东", "西", "东北", "西南", "西北", "东南"]
counts = ["1辆", "2辆", "3辆", "4辆", "5辆", "少量", "大量"]
statuses_active = ["正在移动", "正在装卸", "频繁启停", "正在部署", "原地待命"]
statuses_dead   = ["已摧毁", "已沉默", "无生命迹象"]
statuses_alive  = ["仍在活动", "热信号清晰", "持续发射信号"]
statuses_all    = statuses_active + statuses_dead + statuses_alive
altitudes = ["100米", "200米", "300米", "500米", "800米", "1000米", "1500米", "2000米"]
weather_good = ["晴朗", "多云", "阴天"]
weather_bad  = ["暴雨", "大雾", "浓雾", "沙尘", "雷暴"]
complements = [
    "东侧有临时掩体", "风速15节", "地面有车辙", "周边有平民活动",
    "南侧桥梁完好", "热信号微弱", "电磁环境复杂", "北侧有疑似哨位",
    "通信信号间歇中断", "地面潮湿有泥泞", "发现伪装网覆盖",
    "探测到低频振动", "发现新挖掘痕迹", "周边有废弃建筑",
]

# 字段名 → 词库映射（用于翻转时取不同值）
_VOCABS = {
    "location":  locations,
    "target":    targets,
    "count":     counts,
    "direction": directions,
    "status":    statuses_all,
    "altitude":  altitudes,
}

# ─── 配置 ───────────────────────────────────────────────────────────────────
TARGET_CONTRA     = 500
TARGET_NON_CONTRA = 500
MAX_TRIES         = 20000
# ────────────────────────────────────────────────────────────────────────────


def gen_scene():
    """随机生成一个场景（各字段的真值）。"""
    wth = random.choice(weather_good + weather_bad)
    return {
        "location":  random.choice(locations),
        "target":    random.choice(targets),
        "count":     random.choice(counts),
        "direction": random.choice(directions),
        "status":    random.choice(statuses_all),
        "altitude":  random.choice(altitudes),
        "weather":   wth,
        "visibility": "能见度良好" if wth in weather_good else "能见度极低",
    }


# ─── 双风格报告模板 ──────────────────────────────────────────────────────────

def _render_field_a(scene, f):
    """风格 A（原始模板）"""
    if f == "location":
        return f"目标位于{scene['location']}"
    elif f == "count_target":
        return f"发现{scene['count']}{scene['target']}"
    elif f == "direction":
        return f"正向{scene['direction']}移动"
    elif f == "status":
        return f"目标{scene['status']}"
    elif f == "altitude":
        return f"高度{scene['altitude']}"
    elif f == "weather":
        return f"天气{scene['weather']}，{scene['visibility']}"


def _render_field_b(scene, f):
    """风格 B（改述模板，语义相同但用词不同）"""
    if f == "location":
        return f"在{scene['location']}观测到目标"
    elif f == "count_target":
        return f"探测到{scene['count']}{scene['target']}"
    elif f == "direction":
        return f"向{scene['direction']}方向行进"
    elif f == "status":
        return f"目标状态为{scene['status']}"
    elif f == "altitude":
        return f"飞行高度{scene['altitude']}"
    elif f == "weather":
        return f"气象条件{scene['weather']}，{scene['visibility']}"


def scene_to_report(scene, fields, style="A"):
    """将场景按选定的字段和风格组装成一条报告。"""
    render = _render_field_a if style == "A" else _render_field_b
    parts = [render(scene, f) for f in fields]
    return f"侦察报告：{'，'.join(parts)}。"


# 可用于报告的字段
_CORE_FIELDS = ["location", "count_target", "direction", "status", "altitude", "weather"]

# 字段 → 场景 key 的映射（用于翻转值）
_FIELD_TO_KEY = {
    "location":     "location",
    "count_target": "count",
    "direction":    "direction",
    "status":       "status",
    "altitude":     "altitude",
    "weather":      "weather",
}


def flip_field(scene, field):
    """复制场景并翻转指定字段的值，确保新值与原值不同。"""
    scene_b = dict(scene)
    key = _FIELD_TO_KEY[field]

    if key == "status":
        if scene[key] in statuses_dead:
            scene_b[key] = random.choice(statuses_alive)
        else:
            scene_b[key] = random.choice(statuses_dead)
    elif key == "weather":
        if scene[key] in weather_good:
            scene_b[key] = random.choice(weather_bad)
            scene_b["visibility"] = "能见度极低"
        else:
            scene_b[key] = random.choice(weather_good)
            scene_b["visibility"] = "能见度良好"
    else:
        vocab = _VOCABS[key]
        scene_b[key] = random.choice([v for v in vocab if v != scene[key]])

    return scene_b


def _gen_pair(label):
    """统一的对子生成逻辑。
    矛盾对（label=1）：翻转一个字段值。
    非矛盾对（label=0）：保持字段值一致。
    风格和补充观察随机组合，产生丰富的 Jaccard 分布；
    后续 rejection sampling 确保两个 label 的 Jaccard 分布一致。"""
    scene = gen_scene()
    n_fields = random.randint(3, min(5, len(_CORE_FIELDS)))
    fields = random.sample(_CORE_FIELDS, n_fields)

    # 随机选择风格组合
    use_cross_style = random.random() < 0.5
    style_p = "A"
    style_h = "B" if use_cross_style else "A"

    # 随机决定是否添加不同的补充观察
    use_comp = random.random() < 0.5

    if label == 1:
        flip = random.choice(fields)
        scene_h = flip_field(scene, flip)
    else:
        scene_h = scene

    premise    = scene_to_report(scene,   fields, style=style_p)
    hypothesis = scene_to_report(scene_h, fields, style=style_h)

    if use_comp:
        comp_pair = random.sample(complements, 2)
        premise    = premise.rstrip("。") + f"，{comp_pair[0]}。"
        hypothesis = hypothesis.rstrip("。") + f"，{comp_pair[1]}。"

    return {"premise": premise, "hypothesis": hypothesis, "label": label}


def gen_contradictory():
    return _gen_pair(1)


def gen_non_contradictory():
    return _gen_pair(0)


# ─── Jaccard 工具 ─────────────────────────────────────────────────────────────

import re

def _tokenize(text):
    if re.search(r"[\u4e00-\u9fff]", text):
        return set(text.replace(" ", ""))
    return set(text.lower().split())


def _jaccard(text_a, text_b):
    sa, sb = _tokenize(text_a), _tokenize(text_b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ─── 生成数据集（Jaccard 对齐采样）──────────────────────────────────────────

seen = set()
POOL_MULTIPLIER = 6  # 候选池 = 目标数 × 倍率


def collect_pool(gen_func, pool_size):
    """生成候选池，去重。"""
    items = []
    for _ in range(pool_size * 3):
        item = gen_func()
        key = item["premise"] + "||" + item["hypothesis"]
        if key not in seen:
            seen.add(key)
            item["_jaccard"] = _jaccard(item["premise"], item["hypothesis"])
            items.append(item)
        if len(items) >= pool_size:
            break
    return items


def jaccard_matched_sample(contra_pool, non_contra_pool, target):
    """从两个候选池中按 Jaccard 直方图匹配采样，确保两个 label 的 Jaccard 分布一致。"""
    import numpy as np
    N_BINS = 20

    c_scores = np.array([x["_jaccard"] for x in contra_pool])
    n_scores = np.array([x["_jaccard"] for x in non_contra_pool])

    # 使用两个池合并后的分位数作为 bin 边界，确保每个 bin 都有样本
    all_scores = np.concatenate([c_scores, n_scores])
    bin_edges = np.linspace(all_scores.min() - 1e-6, all_scores.max() + 1e-6, N_BINS + 1)

    c_bin_idx = np.digitize(c_scores, bin_edges) - 1
    n_bin_idx = np.digitize(n_scores, bin_edges) - 1

    selected_c, selected_n = [], []

    for b in range(N_BINS):
        c_in_bin = [i for i, bi in enumerate(c_bin_idx) if bi == b]
        n_in_bin = [i for i, bi in enumerate(n_bin_idx) if bi == b]
        k = min(len(c_in_bin), len(n_in_bin))
        if k > 0:
            selected_c.extend(random.sample(c_in_bin, k))
            selected_n.extend(random.sample(n_in_bin, k))

    # 如果不够 target，按比例从各 bin 补充
    if len(selected_c) > target:
        selected_c = random.sample(selected_c, target)
        selected_n = random.sample(selected_n, target)
    elif len(selected_c) < target:
        # 尽力匹配，不足部分随机补
        shortfall = target - len(selected_c)
        remaining_c = [i for i in range(len(contra_pool)) if i not in set(selected_c)]
        remaining_n = [i for i in range(len(non_contra_pool)) if i not in set(selected_n)]
        extra = min(shortfall, len(remaining_c), len(remaining_n))
        selected_c.extend(random.sample(remaining_c, extra))
        selected_n.extend(random.sample(remaining_n, extra))

    result_c = [contra_pool[i] for i in selected_c[:target]]
    result_n = [non_contra_pool[i] for i in selected_n[:target]]

    # 清理临时字段
    for item in result_c + result_n:
        item.pop("_jaccard", None)

    return result_c, result_n


pool_contra     = collect_pool(gen_contradictory,     TARGET_CONTRA * POOL_MULTIPLIER)
pool_non_contra = collect_pool(gen_non_contradictory, TARGET_NON_CONTRA * POOL_MULTIPLIER)

contra_samples, non_contra_samples = jaccard_matched_sample(
    pool_contra, pool_non_contra, TARGET_CONTRA
)

dataset = contra_samples + non_contra_samples
random.shuffle(dataset)

with open("data/uav_nli_dataset.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"矛盾组   (label=1): {n_contra} 条")
print(f"非矛盾组 (label=0): {n_non_contra} 条")
print(f"合计:               {len(dataset)} 条，已保存至 data/uav_nli_dataset.json")
