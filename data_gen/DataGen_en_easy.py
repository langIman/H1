"""
English Easy UAV Dataset Generator — Scene-driven + Paraphrase System
All pairs originate from the same scene. Contradictory pairs flip one field;
non-contradictory pairs keep consistent info.
Dual-style templates (original / paraphrase) decouple Jaccard from labels.
Common prefix "Recon report:" eliminates entity-name confusion for NLI.
"""

import json
import random
import re

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
counts = ["1", "2", "3", "4", "5", "several", "a large number of"]
statuses_active = ["moving", "being deployed", "on standby", "loading cargo", "frequently stopping"]
statuses_dead   = ["destroyed", "silenced", "no signs of life"]
statuses_alive  = ["still active", "clear heat signature", "continuously transmitting signals"]
statuses_all    = statuses_active + statuses_dead + statuses_alive
altitudes = ["100m", "200m", "300m", "500m", "800m", "1000m", "1500m", "2000m"]
weather_good = ["clear", "partly cloudy", "overcast"]
weather_bad  = ["heavy rain", "heavy fog", "dense fog", "sandstorm", "thunderstorm"]
complements = [
    "temporary cover on the east side", "wind speed 15 knots", "tire tracks on the ground",
    "civilian activity nearby", "frequency-hopping communication in use",
    "southern bridge intact", "weak heat signature", "complex electromagnetic environment",
    "suspected sentry position to the north", "infrared flare residue detected",
    "intermittent communication signal", "muddy ground", "camouflage net detected",
    "low-frequency vibration detected", "fresh excavation marks", "abandoned buildings nearby",
]

_VOCABS = {
    "location":  locations,
    "target":    targets,
    "count":     counts,
    "direction": directions,
    "status":    statuses_all,
    "altitude":  altitudes,
}

# ─── Config ──────────────────────────────────────────────────────────────────
TARGET_CONTRA     = 500
TARGET_NON_CONTRA = 500
MAX_TRIES         = 30000
POOL_MULTIPLIER   = 6
# ─────────────────────────────────────────────────────────────────────────────


def gen_scene():
    wth = random.choice(weather_good + weather_bad)
    return {
        "location":   random.choice(locations),
        "target":     random.choice(targets),
        "count":      random.choice(counts),
        "direction":  random.choice(directions),
        "status":     random.choice(statuses_all),
        "altitude":   random.choice(altitudes),
        "weather":    wth,
        "visibility": "good visibility" if wth in weather_good else "very poor visibility",
    }


# ─── Dual-style report templates ────────────────────────────────────────────

def _render_field_a(scene, f):
    """Style A (original)"""
    if f == "location":
        return f"target located at {scene['location']}"
    elif f == "count_target":
        return f"{scene['count']} {scene['target']}(s) spotted"
    elif f == "direction":
        return f"moving {scene['direction']}"
    elif f == "status":
        return f"target is {scene['status']}"
    elif f == "altitude":
        return f"altitude {scene['altitude']}"
    elif f == "weather":
        return f"weather is {scene['weather']}, {scene['visibility']}"


def _render_field_b(scene, f):
    """Style B (paraphrase)"""
    if f == "location":
        return f"activity observed at {scene['location']}"
    elif f == "count_target":
        return f"detected {scene['count']} {scene['target']}(s)"
    elif f == "direction":
        return f"heading {scene['direction']}"
    elif f == "status":
        return f"target status: {scene['status']}"
    elif f == "altitude":
        return f"flight altitude {scene['altitude']}"
    elif f == "weather":
        return f"weather conditions: {scene['weather']}, {scene['visibility']}"


def scene_to_report(scene, fields, style="A"):
    render = _render_field_a if style == "A" else _render_field_b
    parts = [render(scene, f) for f in fields]
    return f"Recon report: {', '.join(parts)}."


_CORE_FIELDS = ["location", "count_target", "direction", "status", "altitude", "weather"]

_FIELD_TO_KEY = {
    "location":     "location",
    "count_target": "count",
    "direction":    "direction",
    "status":       "status",
    "altitude":     "altitude",
    "weather":      "weather",
}


def flip_field(scene, field):
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
            scene_b["visibility"] = "very poor visibility"
        else:
            scene_b[key] = random.choice(weather_good)
            scene_b["visibility"] = "good visibility"
    else:
        vocab = _VOCABS[key]
        scene_b[key] = random.choice([v for v in vocab if v != scene[key]])

    return scene_b


# ─── Pair generation ─────────────────────────────────────────────────────────

def _gen_pair(label):
    """Unified generation. label=1 flips a field; label=0 keeps consistent.
    Style and complement mixing creates rich Jaccard distribution;
    post-hoc rejection sampling aligns distributions across labels."""
    scene = gen_scene()
    n_fields = random.randint(3, min(5, len(_CORE_FIELDS)))
    fields = random.sample(_CORE_FIELDS, n_fields)

    use_cross_style = random.random() < 0.5
    style_p = "A"
    style_h = "B" if use_cross_style else "A"

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
        premise    = premise.rstrip(".") + f", {comp_pair[0]}."
        hypothesis = hypothesis.rstrip(".") + f", {comp_pair[1]}."

    return {"premise": premise, "hypothesis": hypothesis, "label": label}


def gen_contradictory():
    return _gen_pair(1)


def gen_non_contradictory():
    return _gen_pair(0)


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

import numpy as np

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

with open("data/uav_nli_dataset_en_easy.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

n_contra     = sum(1 for d in dataset if d["label"] == 1)
n_non_contra = sum(1 for d in dataset if d["label"] == 0)
print(f"Contradiction    (label=1): {n_contra}")
print(f"Non-contradiction (label=0): {n_non_contra}")
print(f"Total: {len(dataset)}, saved to data/uav_nli_dataset_en_easy.json")
