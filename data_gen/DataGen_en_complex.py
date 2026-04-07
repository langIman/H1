"""
English Complex UAV Dataset Generator
Multi-field longer sentences, implicit contradictions embedded in rich context.
Common prefix "Recon report:" + dual-style templates + Jaccard-aligned sampling.
"""

import json
import random
import re

import numpy as np

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

# ─── Config ──────────────────────────────────────────────────────────────────
TARGET_CONTRA     = 500
TARGET_NON_CONTRA = 500
MAX_TRIES         = 30000
POOL_MULTIPLIER   = 6
# ────────────────────────────────────────────────────────────────────────────


def _report(content):
    """Common prefix to eliminate UAV-A/B entity-name confusion."""
    return f"Recon report: {content}"


# ─── Dual-style phrase helpers ───────────────────────────────────────────────

def _loc(loc, style):
    return f"at {loc}" if style == "A" else f"in the vicinity of {loc}"


def _tgt(cnt, tgt, style):
    return f"{cnt} {tgt}(s) detected" if style == "A" else f"spotted {cnt} {tgt}(s)"


def _dir(d, style):
    return f"moving {d} at high speed" if style == "A" else f"heading {d} rapidly"


def _weather(w, vis, style):
    return f"weather {w}, {vis}" if style == "A" else f"weather conditions: {w}, {vis}"


def _alt(alt, style):
    return f"at altitude {alt}" if style == "A" else f"flight altitude {alt}"


def _status(s, style):
    return f"target is {s}" if style == "A" else f"target status: {s}"


# ─── Contradiction templates ─────────────────────────────────────────────────

def gen_contradictory():
    kind = random.randint(0, 6)
    sa, sb = "A", random.choice(["A", "B"])

    if kind == 0:
        loc1, loc2 = random.sample(locations, 2)
        tgt, cnt, t = random.choice(targets), random.choice(counts), random.choice(times)
        p = _report(f"at {t}, {_tgt(cnt, tgt, sa)} {_loc(loc1, sa)}, {_status(random.choice(statuses_active), sa)}, {random.choice(supplements)}.")
        h = _report(f"at {t}, {_tgt(cnt, tgt, sb)} {_loc(loc2, sb)}, {_status(random.choice(statuses_active), sb)}, {random.choice(supplements)}.")

    elif kind == 1:
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        w = random.choice(weather_good)
        p = _report(f"at {t}, the {tgt} {_loc(loc, sa)} has {random.choice(statuses_inactive)}, {_weather(w, random.choice(vis_good), sa)}, {random.choice(supplements)}.")
        h = _report(f"at {t}, the {tgt} {_loc(loc, sb)} is {random.choice(statuses_alive)}, {_weather(w, random.choice(vis_good), sb)}, {random.choice(supplements)}.")

    elif kind == 2:
        dir1, dir2 = random.sample(directions, 2)
        loc, tgt, cnt, t = random.choice(locations), random.choice(targets), random.choice(counts), random.choice(times)
        p = _report(f"at {t}, {_tgt(cnt, tgt, sa)} {_loc(loc, sa)} {_dir(dir1, sa)}, {random.choice(supplements)}.")
        h = _report(f"at {t}, {_tgt(cnt, tgt, sb)} {_loc(loc, sb)} {_dir(dir2, sb)}, {random.choice(supplements)}.")

    elif kind == 3:
        alt1, alt2 = random.sample(altitudes, 2)
        tgt = random.choice(["drone", "reconnaissance drone", "drone swarm"])
        loc, t = random.choice(locations), random.choice(times)
        p = _report(f"at {t}, {tgt} detected over {loc} {_alt(alt1, sa)}, {random.choice(signals)}, {random.choice(supplements)}.")
        h = _report(f"at {t}, {tgt} detected over {loc} {_alt(alt2, sb)}, {random.choice(signals)}, {random.choice(supplements)}.")

    elif kind == 4:
        t, loc, tgt = random.choice(times), random.choice(locations), random.choice(targets)
        w1, w2 = random.choice(weather_good), random.choice(weather_bad)
        p = _report(f"at {t}, {_weather(w1, random.choice(vis_good), sa)} {_loc(loc, sa)}, {tgt} {random.choice(statuses_active)}.")
        h = _report(f"at {t}, {_weather(w2, random.choice(vis_bad), sb)} {_loc(loc, sb)}, {tgt} {random.choice(statuses_active)}.")

    elif kind == 5:
        cnt1, cnt2 = random.sample(counts, 2)
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        p = _report(f"at {t}, {_tgt(cnt1, tgt, sa)} confirmed {_loc(loc, sa)}, {_status(random.choice(statuses_active), sa)}, {random.choice(supplements)}.")
        h = _report(f"at {t}, {_tgt(cnt2, tgt, sb)} confirmed {_loc(loc, sb)}, {_status(random.choice(statuses_active), sb)}, {random.choice(supplements)}.")

    else:
        t1, t2 = random.sample(times, 2)
        loc, tgt = random.choice(locations), random.choice(targets)
        p = _report(f"reconnaissance time {t1}, {tgt} confirmed present {_loc(loc, sa)}, {_status(random.choice(statuses_active), sa)}, {random.choice(supplements)}.")
        h = _report(f"reconnaissance time {t2}, {tgt} confirmed present {_loc(loc, sb)}, {_status(random.choice(statuses_active), sb)}, {random.choice(supplements)}.")

    return {"premise": p, "hypothesis": h, "label": 1}


# ─── Non-contradiction templates ─────────────────────────────────────────────

def gen_non_contradictory():
    kind = random.randint(0, 3)
    sa, sb = "A", random.choice(["A", "B"])

    if kind == 0:
        loc1, loc2 = random.sample(locations, 2)
        tgt1, tgt2 = random.sample(targets, 2)
        t = random.choice(times)
        p = _report(f"at {t}, {_tgt(random.choice(counts), tgt1, sa)} {_loc(loc1, sa)}, {_status(random.choice(statuses_active), sa)}, {random.choice(supplements)}.")
        h = _report(f"at {t}, {_tgt(random.choice(counts), tgt2, sb)} {_loc(loc2, sb)}, {_status(random.choice(statuses_active), sb)}, {random.choice(supplements)}.")

    elif kind == 1:
        loc, tgt, t = random.choice(locations), random.choice(targets), random.choice(times)
        p = _report(f"at {t}, {_tgt(random.choice(counts), tgt, sa)} {_loc(loc, sa)}, {_status(random.choice(statuses_active), sa)}, {random.choice(signals)}.")
        h = _report(f"{loc} vicinity: {random.choice(obstacles)}, {random.choice(supplements)}, recommend avoidance.")

    elif kind == 2:
        t1, t2 = random.sample(times, 2)
        loc = random.choice(locations)
        tgt1, tgt2 = random.sample(targets, 2)
        p = _report(f"at {t1}, {tgt1} {_loc(loc, sa)} is {random.choice(statuses_active)}, {random.choice(supplements)}.")
        h = _report(f"at {t2}, {tgt2} {_loc(loc, sb)} is {random.choice(statuses_active)}, {random.choice(supplements)}.")

    else:
        loc, t = random.choice(locations), random.choice(times)
        w = random.choice(weather_good + weather_bad)
        tgt = random.choice(targets)
        p = _report(f"at {t}, {_weather(w, random.choice(vis_good + vis_bad), sa)} {_loc(loc, sa)}, {random.choice(signals)}.")
        h = _report(f"at {t}, {_tgt(random.choice(counts), tgt, sb)} {_loc(loc, sb)}, {_status(random.choice(statuses_active), sb)}, {random.choice(supplements)}.")

    return {"premise": p, "hypothesis": h, "label": 0}


# ─── Jaccard tools ───────────────────────────────────────────────────────────

def _tokenize(text):
    if re.search(r"[\u4e00-\u9fff]", text):
        return set(text.replace(" ", ""))
    return set(text.lower().split())


def _jaccard(text_a, text_b):
    sa, sb = _tokenize(text_a), _tokenize(text_b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ─── Generate with Jaccard-matched sampling ──────────────────────────────────

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

with open("data/uav_nli_dataset_en_complex.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"Contradiction    (label=1): {n_contra}")
print(f"Non-contradiction (label=0): {n_non_contra}")
print(f"Total: {len(dataset)}, saved to data/uav_nli_dataset_en_complex.json")
