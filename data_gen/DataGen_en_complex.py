"""
English Complex UAV Dataset Generator
Multi-field longer sentences, implicit contradictions embedded in rich context.
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
directions   = ["north", "south", "east", "west", "northeast", "southwest", "northwest", "southeast"]
counts       = ["1", "2", "3", "4", "5", "multiple", "several", "a large number of"]
altitudes    = ["100m", "200m", "300m", "500m", "800m", "1000m", "1200m", "1500m", "2000m"]
times        = ["06:00", "08:20", "10:30", "12:00", "13:45", "14:15",
                "16:40", "18:00", "19:30", "20:10", "22:00", "23:50"]
weather_good = ["clear", "partly cloudy", "light breeze"]
weather_bad  = ["heavy fog", "dense fog", "heavy rain", "sandstorm", "thunderstorm"]
vis_good     = ["good visibility", "open field of view", "target clearly visible"]
vis_bad      = ["very poor visibility", "obstructed field of view", "target barely visible"]
statuses_active   = ["continuously maneuvering", "rapidly mobilizing", "deploying", "frequently starting and stopping"]
statuses_inactive = ["destroyed", "silenced", "lost heat signature", "no signs of life"]
statuses_alive    = ["still active", "clear heat signature", "continuously transmitting signals", "resuming maneuver"]
signals      = ["strong electromagnetic radiation", "intermittent communication signal",
                "frequency-hopping communication", "radar scan beam", "radio silence"]
supplements  = [
    "civilian activity nearby", "camouflage net detected", "low-frequency vibration detected",
    "fresh excavation marks found", "abnormal heat source nearby", "tire tracks observed",
    "suspected sentry position detected", "livestock activity in area",
    "weak signal strength", "GPS accuracy degraded", "infrared flare residue detected",
    "bird swarm interference detected",
]
obstacles    = [
    "numerous obstacles", "temporary roadblocks", "bridge damaged", "minefield markers",
    "fallen trees", "vehicle wreckage", "trenches", "barbed wire fence",
    "concrete barriers", "waterlogged road",
]
# ────────────────────────────────────────────────────────────────────────────


def report(uav_id, content):
    return f"UAV-{uav_id} reports: {content}"


def gen_contradictory():
    kind = random.randint(0, 6)

    if kind == 0:
        # Location contradiction
        loc1, loc2 = random.sample(locations, 2)
        tgt, cnt, t = random.choice(targets), random.choice(counts), random.choice(times)
        p = report("A", f"at {t}, {cnt} {tgt}(s) detected at {loc1}, {random.choice(statuses_active)}, {random.choice(supplements)}.")
        h = report("B", f"at {t}, {cnt} {tgt}(s) detected at {loc2}, {random.choice(statuses_active)}, {random.choice(supplements)}.")

    elif kind == 1:
        # Alive/dead status contradiction
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        w = random.choice(weather_good)
        p = report("A", f"at {t}, the {tgt} at {loc} has {random.choice(statuses_inactive)}, weather {w}, {random.choice(vis_good)}, {random.choice(supplements)}.")
        h = report("B", f"at {t}, the {tgt} at {loc} is {random.choice(statuses_alive)}, weather {w}, {random.choice(vis_good)}, {random.choice(supplements)}.")

    elif kind == 2:
        # Direction contradiction
        dir1, dir2 = random.sample(directions, 2)
        loc, tgt, cnt, t = random.choice(locations), random.choice(targets), random.choice(counts), random.choice(times)
        p = report("A", f"at {t}, {cnt} {tgt}(s) at {loc} moving {dir1} at high speed, {random.choice(supplements)}.")
        h = report("B", f"at {t}, {cnt} {tgt}(s) at {loc} moving {dir2} at high speed, {random.choice(supplements)}.")

    elif kind == 3:
        # Altitude contradiction
        alt1, alt2 = random.sample(altitudes, 2)
        tgt = random.choice(["drone", "reconnaissance drone", "drone swarm"])
        loc, t = random.choice(locations), random.choice(times)
        p = report("A", f"at {t}, {tgt} detected over {loc} at altitude {alt1}, {random.choice(signals)}, {random.choice(supplements)}.")
        h = report("B", f"at {t}, {tgt} detected over {loc} at altitude {alt2}, {random.choice(signals)}, {random.choice(supplements)}.")

    elif kind == 4:
        # Weather/visibility contradiction
        t, loc, tgt = random.choice(times), random.choice(locations), random.choice(targets)
        w1, w2 = random.choice(weather_good), random.choice(weather_bad)
        p = report("A", f"at {t}, weather at {loc} is {w1}, {random.choice(vis_good)}, {tgt} {random.choice(statuses_active)}.")
        h = report("B", f"at {t}, weather at {loc} is {w2}, {random.choice(vis_bad)}, {tgt} {random.choice(statuses_active)}.")

    elif kind == 5:
        # Count contradiction
        cnt1, cnt2 = random.sample(counts, 2)
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        p = report("A", f"at {t}, {cnt1} {tgt}(s) confirmed at {loc}, {random.choice(statuses_active)}, {random.choice(supplements)}.")
        h = report("B", f"at {t}, {cnt2} {tgt}(s) confirmed at {loc}, {random.choice(statuses_active)}, {random.choice(supplements)}.")

    else:
        # Time contradiction
        t1, t2 = random.sample(times, 2)
        loc, tgt = random.choice(locations), random.choice(targets)
        p = report("A", f"reconnaissance time {t1}, {tgt} confirmed present at {loc}, {random.choice(statuses_active)}, {random.choice(supplements)}.")
        h = report("B", f"reconnaissance time {t2}, {tgt} confirmed present at {loc}, {random.choice(statuses_active)}, {random.choice(supplements)}.")

    return {"premise": p, "hypothesis": h, "label": 1}


def gen_non_contradictory():
    kind = random.randint(0, 3)

    if kind == 0:
        loc1, loc2 = random.sample(locations, 2)
        tgt1, tgt2 = random.sample(targets, 2)
        t = random.choice(times)
        p = report("A", f"at {t}, {random.choice(counts)} {tgt1}(s) detected at {loc1}, {random.choice(statuses_active)}, {random.choice(supplements)}.")
        h = report("B", f"at {t}, {random.choice(counts)} {tgt2}(s) detected at {loc2}, {random.choice(statuses_active)}, {random.choice(supplements)}.")

    elif kind == 1:
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        p = report("A", f"at {t}, {random.choice(counts)} {tgt}(s) detected at {loc}, {random.choice(statuses_active)}, {random.choice(signals)}.")
        h = report("B", f"{loc} vicinity: {random.choice(obstacles)}, {random.choice(supplements)}, recommend avoidance.")

    elif kind == 2:
        t1, t2 = random.sample(times, 2)
        loc = random.choice(locations)
        tgt1, tgt2 = random.sample(targets, 2)
        p = report("A", f"at {t1}, {tgt1} at {loc} is {random.choice(statuses_active)}, {random.choice(supplements)}.")
        h = report("B", f"at {t2}, {tgt2} at {loc} is {random.choice(statuses_active)}, {random.choice(supplements)}.")

    else:
        loc, t = random.choice(locations), random.choice(times)
        w = random.choice(weather_good + weather_bad)
        tgt = random.choice(targets)
        p = report("A", f"at {t}, weather at {loc} is {w}, {random.choice(vis_good + vis_bad)}, {random.choice(signals)}.")
        h = report("B", f"at {t}, {random.choice(counts)} {tgt}(s) detected at {loc}, {random.choice(statuses_active)}, {random.choice(supplements)}.")

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

with open("data/uav_nli_dataset_en_complex.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"Contradiction    (label=1): {n_contra}")
print(f"Non-contradiction (label=0): {n_non_contra}")
print(f"Total: {len(dataset)}, saved to data/uav_nli_dataset_en_complex.json")

print("\n─── Contradiction samples ───────────────────────────────────")
for s in random.sample([d for d in dataset if d["label"]==1], 2):
    print(f"  P: {s['premise']}")
    print(f"  H: {s['hypothesis']}\n")
print("─── Non-contradiction samples ───────────────────────────────")
for s in random.sample([d for d in dataset if d["label"]==0], 2):
    print(f"  P: {s['premise']}")
    print(f"  H: {s['hypothesis']}\n")
