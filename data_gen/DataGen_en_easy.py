"""
English Easy UAV Dataset Generator
Single-field short sentences, explicit contradictions.
"""

import json
import random

random.seed(42)

# ─── Vocabulary ──────────────────────────────────────────────────────────────
locations = [
    "Zone X", "Zone Y", "Highland Z", "north side of the valley", "abandoned factory",
    "intersection of Road 3", "end of airport runway", "Position A", "Highland B",
    "Ford C", "Village D", "eastern ridge", "western lowland", "southern forest",
    "northern plain", "west end of railway bridge", "south side of reservoir dam",
    "near oil depot", "dock area", "hilltop observation post",
    "tunnel entrance", "canyon exit", "industrial park", "north of substation",
]
targets = [
    "light truck", "armored personnel carrier", "drone", "radar station",
    "communication relay vehicle", "command post", "supply convoy",
    "self-propelled artillery", "anti-tank missile position", "field medical team",
    "drone swarm", "electronic warfare vehicle", "air defense missile system",
    "engineering support vehicle", "fuel supply truck", "infantry fighting vehicle",
    "reconnaissance drone", "rocket artillery position", "communication base station",
    "armored command vehicle",
]
directions = ["north", "south", "east", "west", "northeast", "southwest", "northwest", "southeast"]
counts = ["1", "2", "3", "4", "5", "multiple", "no", "several", "a large number of"]
altitudes = ["100m", "200m", "300m", "500m", "800m", "1000m", "1200m", "1500m", "2000m"]
weather_good = ["clear", "partly cloudy", "light breeze"]
weather_bad  = ["heavy fog", "dense fog", "heavy rain", "sandstorm", "thunderstorm"]
times = ["06:00", "08:20", "10:30", "12:00", "13:45", "14:15",
         "16:40", "18:00", "19:30", "20:10", "22:00", "23:50"]
complements = [
    "temporary cover on the east side", "wind speed 15 knots", "tire tracks on the ground",
    "civilian activity nearby", "frequency-hopping communication in use",
    "southern bridge intact", "weak heat signature", "complex electromagnetic environment",
    "suspected sentry position to the north", "infrared flare residue detected",
    "intermittent communication signal", "muddy ground", "camouflage net detected",
    "livestock activity in the area", "low-frequency vibration detected",
    "fresh excavation marks", "abandoned buildings nearby", "weak signal strength",
    "GPS accuracy degraded", "bird swarm interference detected",
]
# ────────────────────────────────────────────────────────────────────────────


def gen_contradictory():
    kind = random.randint(0, 5)

    if kind == 0:
        loc1, loc2 = random.sample(locations, 2)
        p = f"UAV-A reports: target is located at {loc1}."
        h = f"UAV-B reports: target is located at {loc2}."

    elif kind == 1:
        tgt = random.choice(targets)
        status_dead  = random.choice(["destroyed", "silenced", "no signs of life"])
        status_alive = random.choice(["still active", "clear heat signature", "continuously transmitting signals"])
        p = f"UAV-A reports: the {tgt} has been {status_dead}."
        h = f"UAV-B reports: the {tgt} is {status_alive}."

    elif kind == 2:
        dir1, dir2 = random.sample(directions, 2)
        tgt = random.choice(targets)
        p = f"UAV-A reports: the {tgt} is moving {dir1}."
        h = f"UAV-B reports: the {tgt} is moving {dir2}."

    elif kind == 3:
        alt1, alt2 = random.sample(altitudes, 2)
        tgt = random.choice(["drone", "reconnaissance drone", "drone swarm"])
        p = f"UAV-A reports: target altitude is {alt1}."
        h = f"UAV-B reports: target altitude is {alt2}."

    elif kind == 4:
        w1 = random.choice(weather_good)
        w2 = random.choice(weather_bad)
        p = f"UAV-A reports: weather is {w1}, good visibility."
        h = f"UAV-B reports: weather is {w2}, very poor visibility."

    else:
        t1, t2 = random.sample(times, 2)
        p = f"UAV-A reports: reconnaissance time is {t1}."
        h = f"UAV-B reports: reconnaissance time is {t2}."

    return {"premise": p, "hypothesis": h, "label": 1}


def gen_non_contradictory():
    kind = random.randint(0, 3)

    if kind == 0:
        loc = random.choice(locations)
        tgt = random.choice(targets)
        p = f"UAV-A reports: target is located at {loc}."
        h = f"UAV-B reports: {random.choice(complements)}."

    elif kind == 1:
        tgt1, tgt2 = random.sample(targets, 2)
        p = f"UAV-A reports: {random.choice(counts)} {tgt1} spotted."
        h = f"UAV-B reports: {random.choice(targets)} detected behind the {tgt2}."

    elif kind == 2:
        t = random.choice(times)
        p = f"UAV-A reports: reconnaissance time is {t}."
        h = f"UAV-B reports: {random.choice(complements)}."

    else:
        w = random.choice(weather_good + weather_bad)
        p = f"UAV-A reports: weather is {w}."
        h = f"UAV-B reports: {random.choice(complements)}."

    return {"premise": p, "hypothesis": h, "label": 0}


# ─── Generate & deduplicate ───────────────────────────────────────────────────
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

with open("data/uav_nli_dataset_en_easy.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"Contradiction    (label=1): {n_contra}")
print(f"Non-contradiction (label=0): {n_non_contra}")
print(f"Total: {len(dataset)}, saved to data/uav_nli_dataset_en_easy.json")

print("\n─── Contradiction samples ───────────────────────────────────")
for s in random.sample([d for d in dataset if d["label"]==1], 2):
    print(f"  P: {s['premise']}")
    print(f"  H: {s['hypothesis']}\n")
print("─── Non-contradiction samples ───────────────────────────────")
for s in random.sample([d for d in dataset if d["label"]==0], 2):
    print(f"  P: {s['premise']}")
    print(f"  H: {s['hypothesis']}\n")
