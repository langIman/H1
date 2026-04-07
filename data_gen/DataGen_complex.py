"""
复杂版 UAV 情报数据集生成
句子包含多字段组合（位置、目标、状态、时间、天气、附加观测等），
信息量更大，矛盾更隐蔽，贴近真实情报描述风格。
"""

import json
import random

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


def uav_report(uav_id, content):
    return f"UAV-{uav_id}报告：{content}"


# ─── 矛盾对模板 ──────────────────────────────────────────────────────────────

def gen_contradictory():
    """生成矛盾对，核心字段互斥，其余字段可相同或不同以增加干扰。"""
    kind = random.randint(0, 6)

    if kind == 0:
        # 位置矛盾：两架 UAV 对同一目标报告了不同位置
        loc1, loc2 = random.sample(locations, 2)
        tgt = random.choice(targets)
        cnt = random.choice(counts)
        t   = random.choice(times)
        p = uav_report("A", f"{t}，在{loc1}发现{cnt}{tgt}，目标{random.choice(statuses_active)}，{random.choice(supplements)}。")
        h = uav_report("B", f"{t}，在{loc2}发现{cnt}{tgt}，目标{random.choice(statuses_active)}，{random.choice(supplements)}。")

    elif kind == 1:
        # 存活状态矛盾：一方报告目标已失效，另一方报告仍活跃
        loc = random.choice(locations)
        tgt = random.choice(targets)
        t   = random.choice(times)
        w   = random.choice(weather_good)
        p = uav_report("A", f"{t}，{loc}的{tgt}{random.choice(statuses_inactive)}，{w}，{random.choice(visibility_good)}，{random.choice(supplements)}。")
        h = uav_report("B", f"{t}，{loc}的{tgt}{random.choice(statuses_alive)}，{w}，{random.choice(visibility_good)}，{random.choice(supplements)}。")

    elif kind == 2:
        # 移动方向矛盾
        dir1, dir2 = random.sample(directions, 2)
        loc = random.choice(locations)
        tgt = random.choice(targets)
        cnt = random.choice(counts)
        t   = random.choice(times)
        p = uav_report("A", f"{t}，{loc}发现{cnt}{tgt}正向{dir1}方向机动，速度较快，{random.choice(supplements)}。")
        h = uav_report("B", f"{t}，{loc}发现{cnt}{tgt}正向{dir2}方向机动，速度较快，{random.choice(supplements)}。")

    elif kind == 3:
        # 高度矛盾（适用于飞行目标）
        alt1, alt2 = random.sample(altitudes, 2)
        tgt = random.choice(["侦察无人机", "单兵无人机", "无人机蜂群"])
        loc = random.choice(locations)
        t   = random.choice(times)
        p = uav_report("A", f"{t}，{loc}上空发现{tgt}，飞行高度约{alt1}，{random.choice(signals)}，{random.choice(supplements)}。")
        h = uav_report("B", f"{t}，{loc}上空发现{tgt}，飞行高度约{alt2}，{random.choice(signals)}，{random.choice(supplements)}。")

    elif kind == 4:
        # 天气/能见度矛盾（同一时间同一地点天气描述相反）
        t   = random.choice(times)
        loc = random.choice(locations)
        tgt = random.choice(targets)
        w1  = random.choice(weather_good)
        w2  = random.choice(weather_bad)
        p = uav_report("A", f"{t}，{loc}天气{w1}，{random.choice(visibility_good)}，发现{tgt}{random.choice(statuses_active)}。")
        h = uav_report("B", f"{t}，{loc}天气{w2}，{random.choice(visibility_bad)}，发现{tgt}{random.choice(statuses_active)}。")

    elif kind == 5:
        # 数量矛盾
        cnt1, cnt2 = random.sample(counts, 2)
        loc = random.choice(locations)
        tgt = random.choice(targets)
        t   = random.choice(times)
        p = uav_report("A", f"{t}，{loc}共发现{cnt1}{tgt}，{random.choice(statuses_active)}，{random.choice(supplements)}。")
        h = uav_report("B", f"{t}，{loc}共发现{cnt2}{tgt}，{random.choice(statuses_active)}，{random.choice(supplements)}。")

    else:
        # 侦察时间矛盾（同一事件两架 UAV 报告的时间不同）
        t1, t2 = random.sample(times, 2)
        loc = random.choice(locations)
        tgt = random.choice(targets)
        p = uav_report("A", f"本次侦察时间{t1}，在{loc}确认{tgt}存在，{random.choice(statuses_active)}，{random.choice(supplements)}。")
        h = uav_report("B", f"本次侦察时间{t2}，在{loc}确认{tgt}存在，{random.choice(statuses_active)}，{random.choice(supplements)}。")

    return {"premise": p, "hypothesis": h, "label": 1}


# ─── 非矛盾对模板 ─────────────────────────────────────────────────────────────

def gen_non_contradictory():
    """生成非矛盾对：两架 UAV 报告内容正交（不同目标、不同区域、互补信息）。"""
    kind = random.randint(0, 3)

    if kind == 0:
        # 不同区域，不同目标，互不干涉
        loc1, loc2 = random.sample(locations, 2)
        tgt1, tgt2 = random.sample(targets, 2)
        t = random.choice(times)
        p = uav_report("A", f"{t}，{loc1}发现{random.choice(counts)}{tgt1}，{random.choice(statuses_active)}，{random.choice(supplements)}。")
        h = uav_report("B", f"{t}，{loc2}发现{random.choice(counts)}{tgt2}，{random.choice(statuses_active)}，{random.choice(supplements)}。")

    elif kind == 1:
        # 一方报告目标，另一方报告该区域环境/障碍信息（互补）
        loc = random.choice(locations)
        tgt = random.choice(targets)
        t   = random.choice(times)
        p = uav_report("A", f"{t}，{loc}发现{random.choice(counts)}{tgt}，{random.choice(statuses_active)}，{random.choice(signals)}。")
        h = uav_report("B", f"{loc}附近{random.choice(obstacles)}，{random.choice(supplements)}，建议规避。")

    elif kind == 2:
        # 不同时间段侦察，内容无冲突
        t1, t2 = random.sample(times, 2)
        loc = random.choice(locations)
        tgt1, tgt2 = random.sample(targets, 2)
        p = uav_report("A", f"{t1}，{loc}发现{tgt1}{random.choice(statuses_active)}，{random.choice(supplements)}。")
        h = uav_report("B", f"{t2}，{loc}发现{tgt2}{random.choice(statuses_active)}，{random.choice(supplements)}。")

    else:
        # 一方报告天气/环境，另一方报告目标情况（完全正交）
        loc = random.choice(locations)
        t   = random.choice(times)
        w   = random.choice(weather_good + weather_bad)
        tgt = random.choice(targets)
        p = uav_report("A", f"{t}，{loc}天气{w}，{random.choice(visibility_good + visibility_bad)}，{random.choice(signals)}。")
        h = uav_report("B", f"{t}，{loc}发现{random.choice(counts)}{tgt}，{random.choice(statuses_active)}，{random.choice(supplements)}。")

    return {"premise": p, "hypothesis": h, "label": 0}


# ─── 生成 & 去重 ──────────────────────────────────────────────────────────────
TARGET_CONTRA     = 500
TARGET_NON_CONTRA = 500
MAX_TRIES         = 30000

seen = set()

def collect(gen_func, target):
    items = []
    for _ in range(MAX_TRIES):
        item = gen_func()
        key  = item["premise"] + "||" + item["hypothesis"]
        if key not in seen:
            seen.add(key)
            items.append(item)
        if len(items) >= target:
            break
    return items

contra_samples     = collect(gen_contradictory,     TARGET_CONTRA)
non_contra_samples = collect(gen_non_contradictory, TARGET_NON_CONTRA)

dataset = contra_samples + non_contra_samples
random.shuffle(dataset)

with open("data/uav_nli_dataset_complex.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"矛盾组   (label=1): {n_contra} 条")
print(f"非矛盾组 (label=0): {n_non_contra} 条")
print(f"合计:               {len(dataset)} 条，已保存至 data/uav_nli_dataset_complex.json")

# 打印样例
print("\n─── 矛盾样例 ───────────────────────────────────────────────")
for s in random.sample([d for d in dataset if d["label"]==1], 2):
    print(f"  P: {s['premise']}")
    print(f"  H: {s['hypothesis']}")
    print()
print("─── 非矛盾样例 ─────────────────────────────────────────────")
for s in random.sample([d for d in dataset if d["label"]==0], 2):
    print(f"  P: {s['premise']}")
    print(f"  H: {s['hypothesis']}")
    print()
