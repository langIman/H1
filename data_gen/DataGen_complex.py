"""
复杂版 UAV 情报数据集生成
句子包含多字段组合（位置、目标、状态、时间、天气、附加观测等），
信息量更大，矛盾更隐蔽，贴近真实情报描述风格。
统一使用"侦察报告："前缀，双风格模板 + Jaccard 对齐采样。
"""

import json
import random
import re

import numpy as np

random.seed(42)

# ─── 词库 ────────────────────────────────────────────────────────────────────
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
counts = ["1辆", "2辆", "3辆", "4辆", "5辆", "多辆", "少量", "大批"]
statuses_active   = ["持续移动", "快速机动", "正在部署", "频繁启停", "原地待命", "正在装卸"]
statuses_inactive = ["已摧毁", "已沉默", "失去热信号", "无生命迹象", "停止活动"]
statuses_alive    = ["仍在活动", "热信号清晰", "持续发射信号", "恢复机动", "重新出现"]
times = ["06:00", "08:20", "10:30", "12:00", "13:45", "14:15",
         "16:40", "18:00", "19:30", "20:10", "22:00", "23:50"]
altitudes = ["100米", "200米", "300米", "500米", "800米", "1000米", "1200米", "1500米", "2000米"]
weather_good = ["晴朗", "多云", "微风"]
weather_bad  = ["大雾", "浓雾", "暴雨", "沙尘", "雷暴"]
visibility_good = ["能见度良好", "视野开阔", "目标清晰"]
visibility_bad  = ["能见度极低", "视野受阻", "目标模糊"]
obstacles = [
    "大量障碍物", "临时路障", "桥梁损毁", "雷区标识", "树木倒伏", "车辆残骸",
    "壕沟拦截", "铁丝网围栏", "混凝土路墩", "积水漫道",
]
signals = ["强烈电磁辐射", "间歇性通信信号", "跳频通信特征", "雷达扫描波束", "无线电静默"]
supplements = [
    "周边有平民活动", "发现伪装网覆盖", "探测到低频振动", "地面有新挖掘痕迹",
    "附近存在热源异常", "观测到车辙印迹", "发现疑似哨位", "区域内有牲畜活动",
    "信号强度偏弱", "GPS精度下降", "发现红外干扰弹残骸", "空中有无人机干扰",
]
# ────────────────────────────────────────────────────────────────────────────

# ─── 配置 ────────────────────────────────────────────────────────────────────
TARGET_CONTRA     = 500
TARGET_NON_CONTRA = 500
MAX_TRIES         = 30000
POOL_MULTIPLIER   = 6
# ────────────────────────────────────────────────────────────────────────────


def _report(content):
    """统一前缀，消除 UAV-A/B 实体名干扰。"""
    return f"侦察报告：{content}"


# ─── 双风格模板函数 ──────────────────────────────────────────────────────────

def _loc_phrase(loc, style):
    return f"在{loc}" if style == "A" else f"{loc}方向"


def _tgt_phrase(cnt, tgt, style):
    return f"发现{cnt}{tgt}" if style == "A" else f"探测到{cnt}{tgt}"


def _dir_phrase(d, style):
    return f"正向{d}方向机动" if style == "A" else f"朝{d}方向行进"


def _weather_phrase(w, vis, style):
    return f"天气{w}，{vis}" if style == "A" else f"气象条件{w}，{vis}"


def _alt_phrase(alt, style):
    return f"飞行高度约{alt}" if style == "A" else f"高度{alt}"


def _status_phrase(s, style):
    return f"目标{s}" if style == "A" else f"状态为{s}"


# ─── 矛盾对模板 ──────────────────────────────────────────────────────────────

def gen_contradictory():
    kind = random.randint(0, 6)
    sa, sb = "A", random.choice(["A", "B"])  # 随机跨风格

    if kind == 0:
        # 位置矛盾
        loc1, loc2 = random.sample(locations, 2)
        tgt, cnt, t = random.choice(targets), random.choice(counts), random.choice(times)
        p = _report(f"{t}，{_loc_phrase(loc1, sa)}{_tgt_phrase(cnt, tgt, sa)}，{_status_phrase(random.choice(statuses_active), sa)}，{random.choice(supplements)}。")
        h = _report(f"{t}，{_loc_phrase(loc2, sb)}{_tgt_phrase(cnt, tgt, sb)}，{_status_phrase(random.choice(statuses_active), sb)}，{random.choice(supplements)}。")

    elif kind == 1:
        # 存活状态矛盾
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        w = random.choice(weather_good)
        p = _report(f"{t}，{loc}的{tgt}{random.choice(statuses_inactive)}，{_weather_phrase(w, random.choice(visibility_good), sa)}，{random.choice(supplements)}。")
        h = _report(f"{t}，{loc}的{tgt}{random.choice(statuses_alive)}，{_weather_phrase(w, random.choice(visibility_good), sb)}，{random.choice(supplements)}。")

    elif kind == 2:
        # 移动方向矛盾
        dir1, dir2 = random.sample(directions, 2)
        loc, tgt, cnt, t = random.choice(locations), random.choice(targets), random.choice(counts), random.choice(times)
        p = _report(f"{t}，{loc}{_tgt_phrase(cnt, tgt, sa)}{_dir_phrase(dir1, sa)}，速度较快，{random.choice(supplements)}。")
        h = _report(f"{t}，{loc}{_tgt_phrase(cnt, tgt, sb)}{_dir_phrase(dir2, sb)}，速度较快，{random.choice(supplements)}。")

    elif kind == 3:
        # 高度矛盾
        alt1, alt2 = random.sample(altitudes, 2)
        tgt = random.choice(["侦察无人机", "单兵无人机", "无人机蜂群"])
        loc, t = random.choice(locations), random.choice(times)
        p = _report(f"{t}，{loc}上空发现{tgt}，{_alt_phrase(alt1, sa)}，{random.choice(signals)}，{random.choice(supplements)}。")
        h = _report(f"{t}，{loc}上空发现{tgt}，{_alt_phrase(alt2, sb)}，{random.choice(signals)}，{random.choice(supplements)}。")

    elif kind == 4:
        # 天气/能见度矛盾
        t, loc, tgt = random.choice(times), random.choice(locations), random.choice(targets)
        w1, w2 = random.choice(weather_good), random.choice(weather_bad)
        p = _report(f"{t}，{loc}{_weather_phrase(w1, random.choice(visibility_good), sa)}，{_tgt_phrase('', tgt, sa).replace('发现', '发现').replace('探测到', '探测到')}{_status_phrase(random.choice(statuses_active), sa)}。")
        h = _report(f"{t}，{loc}{_weather_phrase(w2, random.choice(visibility_bad), sb)}，{_tgt_phrase('', tgt, sb).replace('发现', '发现').replace('探测到', '探测到')}{_status_phrase(random.choice(statuses_active), sb)}。")

    elif kind == 5:
        # 数量矛盾
        cnt1, cnt2 = random.sample(counts, 2)
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        p = _report(f"{t}，{loc}共{_tgt_phrase(cnt1, tgt, sa)}，{_status_phrase(random.choice(statuses_active), sa)}，{random.choice(supplements)}。")
        h = _report(f"{t}，{loc}共{_tgt_phrase(cnt2, tgt, sb)}，{_status_phrase(random.choice(statuses_active), sb)}，{random.choice(supplements)}。")

    else:
        # 时间矛盾
        t1, t2 = random.sample(times, 2)
        loc, tgt = random.choice(locations), random.choice(targets)
        p = _report(f"本次侦察时间{t1}，{_loc_phrase(loc, sa)}确认{tgt}存在，{_status_phrase(random.choice(statuses_active), sa)}，{random.choice(supplements)}。")
        h = _report(f"本次侦察时间{t2}，{_loc_phrase(loc, sb)}确认{tgt}存在，{_status_phrase(random.choice(statuses_active), sb)}，{random.choice(supplements)}。")

    return {"premise": p, "hypothesis": h, "label": 1}


# ─── 非矛盾对模板 ─────────────────────────────────────────────────────────────

def gen_non_contradictory():
    kind = random.randint(0, 3)
    sa, sb = "A", random.choice(["A", "B"])

    if kind == 0:
        # 不同区域，不同目标
        loc1, loc2 = random.sample(locations, 2)
        tgt1, tgt2 = random.sample(targets, 2)
        t = random.choice(times)
        p = _report(f"{t}，{_loc_phrase(loc1, sa)}{_tgt_phrase(random.choice(counts), tgt1, sa)}，{_status_phrase(random.choice(statuses_active), sa)}，{random.choice(supplements)}。")
        h = _report(f"{t}，{_loc_phrase(loc2, sb)}{_tgt_phrase(random.choice(counts), tgt2, sb)}，{_status_phrase(random.choice(statuses_active), sb)}，{random.choice(supplements)}。")

    elif kind == 1:
        # 互补信息
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        p = _report(f"{t}，{_loc_phrase(loc, sa)}{_tgt_phrase(random.choice(counts), tgt, sa)}，{_status_phrase(random.choice(statuses_active), sa)}，{random.choice(signals)}。")
        h = _report(f"{loc}附近{random.choice(obstacles)}，{random.choice(supplements)}，建议规避。")

    elif kind == 2:
        # 不同时间段
        t1, t2 = random.sample(times, 2)
        loc = random.choice(locations)
        tgt1, tgt2 = random.sample(targets, 2)
        p = _report(f"{t1}，{loc}发现{tgt1}{random.choice(statuses_active)}，{random.choice(supplements)}。")
        h = _report(f"{t2}，{loc}发现{tgt2}{random.choice(statuses_active)}，{random.choice(supplements)}。")

    else:
        # 天气 + 目标（正交信息）
        loc, t = random.choice(locations), random.choice(times)
        w = random.choice(weather_good + weather_bad)
        tgt = random.choice(targets)
        p = _report(f"{t}，{loc}{_weather_phrase(w, random.choice(visibility_good + visibility_bad), sa)}，{random.choice(signals)}。")
        h = _report(f"{t}，{_loc_phrase(loc, sb)}{_tgt_phrase(random.choice(counts), tgt, sb)}，{_status_phrase(random.choice(statuses_active), sb)}，{random.choice(supplements)}。")

    return {"premise": p, "hypothesis": h, "label": 0}


# ─── Jaccard 工具 ─────────────────────────────────────────────────────────────

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


def collect_pool(gen_func, pool_size):
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
    N_BINS = 20
    c_scores = np.array([x["_jaccard"] for x in contra_pool])
    n_scores = np.array([x["_jaccard"] for x in non_contra_pool])

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

    if len(selected_c) > target:
        selected_c = random.sample(selected_c, target)
        selected_n = random.sample(selected_n, target)
    elif len(selected_c) < target:
        shortfall = target - len(selected_c)
        remaining_c = [i for i in range(len(contra_pool)) if i not in set(selected_c)]
        remaining_n = [i for i in range(len(non_contra_pool)) if i not in set(selected_n)]
        extra = min(shortfall, len(remaining_c), len(remaining_n))
        selected_c.extend(random.sample(remaining_c, extra))
        selected_n.extend(random.sample(remaining_n, extra))

    result_c = [contra_pool[i] for i in selected_c[:target]]
    result_n = [non_contra_pool[i] for i in selected_n[:target]]

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

with open("data/uav_nli_dataset_complex.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"矛盾组   (label=1): {n_contra} 条")
print(f"非矛盾组 (label=0): {n_non_contra} 条")
print(f"合计:               {len(dataset)} 条，已保存至 data/uav_nli_dataset_complex.json")
