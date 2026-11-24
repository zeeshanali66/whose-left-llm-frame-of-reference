"""Whose left? Frame-of-reference choices when LLMs place objects in a 3D scene.

World (top-down): camera at (0, -10) looking toward +y. x grows to the camera's right, y grows away from the camera.
An anchor object (sofa, car, ...) sits at (0, 0) facing one of three directions:
  away   -> its front points to +y (away from the camera)
  toward -> its front points to -y (toward the camera)
  side   -> its front points to +x (to the camera's right)
The LLM places a target object "left of / right of / in front of / behind" the anchor, with the frame either
unspecified (ambiguous), the camera's view (viewer frame) or the anchor's own perspective (object frame).
A geometric checker labels each placement as consistent with the viewer frame, the object frame, both, or neither.

Usage:  python -I for_pipeline.py pilot     (12 prompts on one model)
        python -I for_pipeline.py run       (all prompts, all models; resumable)
        python -I for_pipeline.py results
"""
import itertools, json, math, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "placements.jsonl")
RES = os.path.join(HERE, "results")
OLLAMA = "http://localhost:11434/api/chat"
MODELS = ["llama3.1:8b", "qwen2.5:7b", "gemma3:12b", "qwen3.5:9b", "gemma4:12b"]

ANCHORS = ["sofa", "car", "armchair", "person", "desk"]
TARGETS = {"sofa": "lamp", "car": "traffic cone", "armchair": "plant", "person": "ball", "desk": "bin"}
RELATIONS = ["left", "right", "front", "behind"]
FACING = {"away": (0, 1), "toward": (0, -1), "side": (1, 0)}
FACING_TEXT = {"away": "faces away from the camera (its front points toward +y)",
               "toward": "faces the camera (its front points toward -y)",
               "side": "faces to the camera's right (its front points toward +x)"}
REL_TEXT = {"left": "to the left of", "right": "to the right of", "front": "in front of", "behind": "behind"}
FRAMES = ["ambiguous", "viewer", "object", "ask"]  # "ask": ambiguous, but the model may ask a clarifying question
PARAPHRASES = [
    "Place the {t} {rel} the {a}{frame}.",
    "Put a {t} {rel} the {a}{frame}.",
    "I want the {t} {rel} the {a}{frame}. Where should it go?",
]
FRAME_TEXT = {"ambiguous": "", "viewer": ", as seen from the camera", "object": ", from the {a}'s own point of view", "ask": ""}
ASK_TEXT = ('\nIf the instruction could reasonably mean more than one place, do not guess: '
            'return {"clarify": "<one short question>"} instead.')


def rot_left(v):  # rotate 90 degrees counter-clockwise: an entity facing v has its left at rot_left(v)
    return (-v[1], v[0])


def directions(facing):
    """Unit vectors for each relation in both frames."""
    f = FACING[facing]
    viewer = {"left": (-1, 0), "right": (1, 0), "front": (0, -1), "behind": (0, 1)}
    l = rot_left(f)
    obj = {"left": l, "right": (-l[0], -l[1]), "front": f, "behind": (-f[0], -f[1])}
    return viewer, obj


def satisfies(v, d):
    """True if vector v points within 45 degrees of direction d (and is not at the anchor)."""
    n = math.hypot(*v)
    if n < 0.3:
        return False
    return (v[0] * d[0] + v[1] * d[1]) / n > math.cos(math.radians(45))


def label(x, y, facing, rel):
    viewer, obj = directions(facing)
    vv, oo = satisfies((x, y), viewer[rel]), satisfies((x, y), obj[rel])
    return "both" if vv and oo else "viewer" if vv else "object" if oo else "neither"


def agreement(facing, rel):
    viewer, obj = directions(facing)
    a, b = viewer[rel], obj[rel]
    dot = a[0] * b[0] + a[1] * b[1]
    return "agree" if dot > 0.5 else "conflict" if dot < -0.5 else "orthogonal"


SYS = "You place objects in a simple 2D floor plan. You answer only with JSON."


def prompt(anchor, facing, rel, frame, para):
    t = TARGETS[anchor]
    instr = PARAPHRASES[para].format(t=t, rel=REL_TEXT[rel], a=anchor, frame=FRAME_TEXT[frame].format(a=anchor))
    return ("Floor plan (top-down, units in metres): a camera is at (0, -10) looking toward +y. "
            "x increases to the camera's right; y increases away from the camera.\n"
            f"A {anchor} is at (0, 0) and {FACING_TEXT[facing]}.\n"
            f"{instr}\nPlace it about 1.5 m from the {anchor}. "
            'Return JSON exactly like {"x": 0.0, "y": 0.0}.' + (ASK_TEXT if frame == "ask" else ""))


def items():
    for anchor, facing, rel, frame, para in itertools.product(ANCHORS, FACING, RELATIONS, FRAMES, range(len(PARAPHRASES))):
        yield {"anchor": anchor, "facing": facing, "rel": rel, "frame": frame, "para": para}


def chat(model, text):
    extra = {"think": False} if model.startswith(("qwen3", "gemma4")) else {}
    body = json.dumps({"model": model, "stream": False, "format": "json", **extra,
                       "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": text}],
                       "options": {"temperature": 0, "seed": 42, "num_predict": 80, "num_ctx": 2048}}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())["message"]["content"]
        except Exception as e:
            print("retry", attempt + 1, e, flush=True)
            time.sleep(15)
    raise RuntimeError("Ollama failed 3 times")


def parse(s):
    try:
        j = json.loads(re.search(r"\{[^{}]*\}", s).group(0))
        return float(j["x"]), float(j["y"])
    except Exception:
        return None


def run(models=MODELS, limit=None):
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    done = set()
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            for l in f:
                r = json.loads(l)
                done.add((r["model"], r["anchor"], r["facing"], r["rel"], r["frame"], r["para"]))
    for m in models:
        n = 0
        for it in items():
            key = (m, it["anchor"], it["facing"], it["rel"], it["frame"], it["para"])
            if key in done:
                continue
            if limit and n >= limit:
                break
            raw = chat(m, prompt(**it))
            asked = '"clarify"' in raw
            xy = None if asked else parse(raw)
            row = dict(it, model=m, raw=raw, x=xy[0] if xy else None, y=xy[1] if xy else None,
                       label="asked" if asked else label(*xy, it["facing"], it["rel"]) if xy else "invalid",
                       axis=agreement(it["facing"], it["rel"]))
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            n += 1
        print(m, "done", flush=True)


def results():
    import pandas as pd
    os.makedirs(RES, exist_ok=True)
    R = pd.read_json(OUT, lines=True)
    lines = [f"# Results\n\nTotal placements: {len(R)}; invalid JSON: {(R['label'] == 'invalid').sum()}\n"]
    # RQ5: calibrated clarification -- do models ask when (and only when) the frames disagree?
    K = R[R["frame"] == "ask"]
    if len(K):
        t5 = K.assign(asked=K["label"] == "asked").pivot_table(index="model", columns="axis", values="asked", aggfunc="mean").round(2)
        lines += ["## RQ5: clarification rate (ideal: high for conflict/orthogonal, low for agree)\n", "```\n" + t5.to_string() + "\n```", ""]
        # does the question actually ask about the frame ("your left or the sofa's left?"), or about something else?
        fq = re.compile(r"perspective|point of view|viewpoint|whose|your left|camera|facing|own left|from where|view", re.I)
        Q = K[K["label"] == "asked"]
        nf = int(Q["raw"].str.contains(fq).sum())
        lines += [f"Questions asked: {len(Q)} of {len(K)} ask-condition prompts; questions that mention the frame or perspective: {nf}.\n"]
    R = R[R["frame"] != "ask"]  # RQ1-2 and consistency use the non-ask prompts
    # RQ1: which frame do models use when the instruction is ambiguous and the frames disagree?
    A = R[(R["frame"] == "ambiguous") & (R["axis"] != "agree")]
    t1 = pd.crosstab([A["model"], A["axis"]], A["label"], normalize="index").round(2)
    lines += ["## RQ1: ambiguous instructions where frames differ (share of placements)\n", "```\n" + t1.to_string() + "\n```", ""]
    # RQ2: compliance when the frame is stated explicitly
    E = R[R["frame"] != "ambiguous"].copy()
    E["correct"] = E.apply(lambda r: r["label"] in (r["frame"], "both"), axis=1)
    t2 = E.pivot_table(index=["model", "frame"], columns="axis", values="correct", aggfunc="mean").round(2)
    lines += ["## RQ2: accuracy when the frame is explicit, by whether the frames agree\n", "```\n" + t2.to_string() + "\n```", ""]
    # consistency across paraphrases (same item, different wording -> same label?)
    g = R.groupby(["model", "anchor", "facing", "rel", "frame"])["label"].nunique()
    lines += [f"## Paraphrase consistency\n\nShare of items with the same label across all 3 paraphrases: "
              + ", ".join(f"{m}: {(s == 1).mean():.2f}" for m, s in g.groupby(level=0)) + "\n"]
    # figure: explicit-frame accuracy when the frames agree vs conflict
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, fr in zip(axs, ["viewer", "object"]):
        t = t2.xs(fr, level="frame")[["agree", "conflict"]]
        t.plot.bar(ax=ax, color=["#5b8def", "#e07b39"], rot=20, legend=(fr == "viewer"))
        ax.set_title(f"'{fr}' frame stated explicitly"); ax.set_ylim(0, 1); ax.set_xlabel("")
    axs[0].set_ylabel("share placed correctly")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "fig_rq2_accuracy.png"), dpi=150); plt.close(fig)
    # data for the three.js / WebXR viewer
    V = pd.read_json(OUT, lines=True).drop(columns=["raw"])
    with open(os.path.join(HERE, "viewer", "viewer_data.js"), "w", encoding="utf-8") as f:
        f.write("window.VIEWER_DATA=" + V.to_json(orient="records") + ";\n")
    with open(os.path.join(RES, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))


def selftest():
    # facing toward the camera: the anchor's own left is the camera's right (+x)
    assert label(1.5, 0, "toward", "left") == "object"
    assert label(-1.5, 0, "toward", "left") == "viewer"
    assert label(-1.5, 0, "away", "left") == "both"
    assert label(0, -1.5, "away", "front") == "viewer"   # between camera and anchor
    assert label(0, 1.5, "away", "front") == "object"    # the side the anchor faces
    assert label(0, 1.5, "side", "left") == "object"     # facing +x, own left is +y
    assert agreement("toward", "left") == "conflict" and agreement("away", "left") == "agree"
    assert agreement("side", "front") == "orthogonal"
    print("selftest ok;", sum(1 for _ in items()), "prompts per model")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "selftest":
        selftest()
    elif cmd == "pilot":
        run(models=[MODELS[0]], limit=12)
    elif cmd == "run":
        run()
    elif cmd == "results":
        results()
