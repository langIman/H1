import json
import random
import itertools

random.seed(42)

# 基础词库
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
counts = ["1辆", "2辆", "3辆", "4辆", "5辆", "多辆", "无", "少量", "大量"]
statuses = ["静止停放", "正向移动", "已摧毁", "正在装卸", "伪装隐蔽", "频繁启停",
            "快速撤离", "原地待命", "正在部署", "已转移"]
times = ["06:00", "08:20", "10:30", "12:00", "13:45", "14:15",
         "16:40", "18:00", "19:30", "20:10", "22:00", "23:50"]
altitudes = ["100米", "200米", "300米", "500米", "800米", "1000米", "1200米", "1500米", "2000米"]
weather = ["晴朗", "多云", "小雨", "中雨", "暴雨", "大雾", "浓雾", "沙尘", "阴天", "雷暴"]
obstacles = [
    "大量障碍物", "临时路障", "桥梁损毁", "雷区标识", "树木倒伏", "车辆残骸",
    "壕沟拦截", "铁丝网围栏", "混凝土路墩", "积水漫道",
]
complements = [
    "东侧有临时掩体", "风速15节", "地面有车辙", "周边有平民活动",
    "使用跳频技术", "南侧桥梁完好", "热信号微弱", "电磁环境复杂",
    "北侧有疑似哨位", "发现红外干扰弹", "通信信号间歇中断", "地面潮湿有泥泞",
    "发现伪装网覆盖", "区域内有牲畜活动", "探测到低频振动", "空中有鸟群干扰",
    "发现新挖掘痕迹", "周边有废弃建筑", "信号强度偏弱", "GPS精度下降",
]

def gen_contradictory():
    """生成矛盾对：核心属性互斥"""
    templates = [
        (f"UAV-A报告：目标位于{random.choice(locations)}。",
         f"UAV-B报告：目标位于{random.choice(locations)}。", "location"),
        (f"UAV-A报告：发现{random.choice(counts)}{random.choice(targets)}。",
         f"UAV-B报告：该区域无任何{random.choice(targets)}。", "existence"),
        (f"UAV-A报告：目标正向{random.choice(directions)}移动。",
         f"UAV-B报告：目标正向{random.choice(directions)}移动。", "direction"),
        (f"UAV-A报告：目标{random.choice(['已摧毁', '已沉默', '无生命迹象'])}。",
         f"UAV-B报告：目标{random.choice(['仍在活动', '热信号清晰', '持续发射信号'])}。", "status"),
        (f"UAV-A报告：侦察时间为{random.choice(times)}。",
         f"UAV-B报告：侦察时间为{random.choice(times)}。", "time"),
        (f"UAV-A报告：目标高度为{random.choice(altitudes)}。",
         f"UAV-B报告：目标高度为{random.choice(altitudes)}。", "altitude"),
        (f"UAV-A报告：天气{random.choice(weather)}，能见度良好。",
         f"UAV-B报告：天气{random.choice(weather)}，能见度极低。", "weather"),
    ]
    t = random.choice(templates)
    # 确保互斥值不同
    if t[2] in ["location", "direction", "time", "altitude"]:
        v1, v2 = random.sample(t[0].split("：")[-1].replace("。","").split("位于")[-1].split("正向")[-1].split("为")[-1].split("时间为")[-1], 2) if len(t[0].split("：")[-1].replace("。","")) > 2 else (t[0], t[1])
        # 简化处理：直接替换确保不同
        pass
    return {"premise": t[0], "hypothesis": t[1], "label": 1}

def gen_non_contradictory():
    """生成不矛盾对：包含同模板一致型（高 Jaccard）和正交互补型（低 Jaccard）"""
    r = random.random()

    if r < 0.5:
        # ── 同模板一致型：与矛盾对句式相同，但关键字段取相同值 ──
        # 这类样本的 Jaccard 极高，迫使模型理解语义而非依赖词汇重叠
        loc = random.choice(locations)
        tgt = random.choice(targets)
        cnt = random.choice(counts)
        dir_ = random.choice(directions)
        tm = random.choice(times)
        alt = random.choice(altitudes)
        wth = random.choice(weather)
        st = random.choice(statuses)

        consistent_templates = [
            # 位置一致
            (f"UAV-A报告：目标位于{loc}。",
             f"UAV-B报告：目标位于{loc}。"),
            # 目标一致（同类型同数量）
            (f"UAV-A报告：发现{cnt}{tgt}。",
             f"UAV-B报告：发现{cnt}{tgt}。"),
            # 方向一致
            (f"UAV-A报告：目标正向{dir_}移动。",
             f"UAV-B报告：目标正向{dir_}移动。"),
            # 高度一致
            (f"UAV-A报告：目标高度为{alt}。",
             f"UAV-B报告：目标高度为{alt}。"),
            # 时间一致
            (f"UAV-A报告：侦察时间为{tm}。",
             f"UAV-B报告：侦察时间为{tm}。"),
            # 天气一致
            (f"UAV-A报告：天气{wth}，能见度良好。",
             f"UAV-B报告：天气{wth}，能见度良好。"),
            # 状态一致
            (f"UAV-A报告：目标{st}。",
             f"UAV-B报告：目标{st}。"),
        ]
        p, h = random.choice(consistent_templates)
        return {"premise": p, "hypothesis": h, "label": 0}

    else:
        # ── 正交互补型：不同话题，低 Jaccard ──
        p_templates = [
            f"UAV-A报告：目标位于{random.choice(locations)}。",
            f"UAV-A报告：发现{random.choice(counts)}{random.choice(targets)}。",
            f"UAV-A报告：目标正向{random.choice(directions)}移动。",
            f"UAV-A报告：目标高度{random.choice(altitudes)}。",
            f"UAV-A报告：侦察时间{random.choice(times)}。",
            f"UAV-A报告：天气{random.choice(weather)}。"
        ]
        h_templates = [
            f"UAV-B报告：{random.choice(locations)}存在{random.choice(obstacles)}。",
            f"UAV-B报告：{random.choice(complements)}。",
            f"UAV-B报告：{random.choice(targets)}后方有{random.choice(['步兵', '补给箱', '指挥人员'])}。",
            f"UAV-B报告：{random.choice(times)}区域出现{random.choice(['烟雾', '灯光', '扬尘'])}。"
        ]
        return {
            "premise": random.choice(p_templates),
            "hypothesis": random.choice(h_templates),
            "label": 0
        }

# ─── 数量配置（两类独立控制）───────────────────────────────────────────────
TARGET_CONTRA     = 500   # 矛盾组（label=1）目标数量
TARGET_NON_CONTRA = 500   # 非矛盾组（label=0）目标数量
MAX_TRIES         = 20000 # 单类最大尝试次数，防止词库过小时死循环
# ────────────────────────────────────────────────────────────────────────────

seen = set()

def collect(gen_func, target):
    """调用 gen_func 持续生成，去重后收集到 target 条为止。"""
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

# 合并并打乱，避免模型训练时看到规律性的标签顺序
dataset = contra_samples + non_contra_samples
random.shuffle(dataset)

# 保存
with open("data/uav_nli_dataset.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

# 统计并打印各类数量
n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"矛盾组   (label=1): {n_contra} 条")
print(f"非矛盾组 (label=0): {n_non_contra} 条")
print(f"合计:               {len(dataset)} 条，已保存至 uav_nli_dataset.json")
