"""Whose left? Part 2: can we make models follow the requested frame, and ask when they should?

Part 1 showed: (a) when told "from the sofa's own point of view", accuracy collapses when that conflicts with the
camera's view; (b) models almost never ask "whose left?". Part 2 tests simple fixes on the 3 strongest models,
using the first paraphrase only (part 1 showed paraphrase effects are small for these models):

  hint     the prompt spells out the requested direction in coordinates ("the sofa's own left is toward -x")
  reason   JSON must first state the direction (+x/-x/+y/-y) of the relation in the requested frame, then x, y
  ego      object frame only: the scene is described in the anchor's own coordinates (it faces +y, x to its right);
           the answer is rotated back to the world before checking
  ask_explained   ambiguous instruction, and the prompt explains that left/right/front/behind can be meant from the
           camera or from the object; the model should ask only when the two readings differ

  python -I for_fixes.py selftest | prompt | run | results
"""
import json, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # needed under python -I
import for_pipeline as p1

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "fixes.jsonl")
RES = os.path.join(HERE, "results")
MODELS = ["gemma4:12b", "qwen3.5:9b", "gemma3:12b"]
CONDS = [("viewer", "hint"), ("viewer", "reason"), ("object", "hint"), ("object", "reason"), ("object", "ego"),
         ("ambiguous", "ask_explained")]
DIRNAME = {(1, 0): "+x", (-1, 0): "-x", (0, 1): "+y", (0, -1): "-y"}


def target_dir(facing, rel, frame):
    viewer, obj = p1.directions(facing)
    return (viewer if frame == "viewer" else obj)[rel]


def scene_text():
    return ("Floor plan (top-down, units in metres): a camera is at (0, -10) looking toward +y. "
            "x increases to the camera's right; y increases away from the camera.\n")


def prompt(anchor, facing, rel, frame, fix):
    t, a = p1.TARGETS[anchor], anchor
    base_instr = p1.PARAPHRASES[0].format(t=t, rel=p1.REL_TEXT[rel], a=a,
                                          frame=p1.FRAME_TEXT[frame].format(a=a) if frame in p1.FRAME_TEXT else "")
    if fix == "ego":
        return (f"Coordinate system attached to the {a} (top-down, metres): the {a} is at (0, 0) and faces +y; "
                f"x increases to the {a}'s own right.\n{base_instr}\nPlace it about 1.5 m from the {a}. "
                'Return JSON exactly like {"x": 0.0, "y": 0.0}.')
    head = scene_text() + f"A {a} is at (0, 0) and {p1.FACING_TEXT[facing]}.\n"
    if fix == "hint":
        d = DIRNAME[tuple(int(round(c)) for c in target_dir(facing, rel, frame))]
        who = "the camera's view" if frame == "viewer" else f"the {a}'s own point of view"
        return (head + f"{base_instr}\nNote: '{p1.REL_TEXT[rel]}' from {who} is the {d} direction from the {a}.\n"
                f"Place it about 1.5 m from the {a}. " + 'Return JSON exactly like {"x": 0.0, "y": 0.0}.')
    if fix == "reason":
        return (head + f"{base_instr}\nPlace it about 1.5 m from the {a}. First work out which direction "
                "(+x, -x, +y or -y) that relation points in from the requested point of view, then give the position. "
                'Return JSON exactly like {"direction": "<one of +x, -x, +y, -y>", "x": 0.0, "y": 0.0}.')
    if fix == "ask_explained":
        return (head + f"{base_instr}\nPlace it about 1.5 m from the {a}.\n"
                f"Note: words like left, right, front and behind can be meant from the camera's view or from the {a}'s "
                "own point of view. If the instruction does not say which, and the two readings would give different "
                'places, do not guess: return {"clarify": "<one short question>"}. Otherwise return JSON exactly like '
                '{"x": 0.0, "y": 0.0}.')
    raise ValueError(fix)


def ego_to_world(x, y, facing):
    """Anchor frame (anchor faces +y', x' to its right) -> world. World facing f; right = -rot_left(f)."""
    f = p1.FACING[facing]
    l = p1.rot_left(f)
    r = (-l[0], -l[1])
    return (x * r[0] + y * f[0], x * r[1] + y * f[1])


def items():
    for anchor in p1.ANCHORS:
        for facing in p1.FACING:
            for rel in p1.RELATIONS:
                for frame, fix in CONDS:
                    yield anchor, facing, rel, frame, fix


def evaluate(anchor, facing, rel, frame, fix, raw):
    rec = {}
    if fix == "ask_explained":
        try:
            j = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except Exception:
            j = {}
        if "clarify" in j:
            return {"label": "asked", "question": str(j["clarify"])[:200]}
    xy = p1.parse(raw)
    if xy is None:
        return {"label": "invalid"}
    x, y = xy
    if fix == "ego":
        x, y = ego_to_world(x, y, facing)
    rec.update({"x": round(x, 3), "y": round(y, 3), "label": p1.label(x, y, facing, rel)})
    if fix == "reason":
        try:
            j = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            want = DIRNAME[tuple(int(round(c)) for c in target_dir(facing, rel, frame))]
            rec["stated_dir"] = str(j.get("direction", ""))
            rec["stated_dir_ok"] = rec["stated_dir"].strip() == want
        except Exception:
            pass
    return rec


def run(models=MODELS):
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT, encoding="utf-8"):
            r = json.loads(l)
            done.add((r["model"], r["anchor"], r["facing"], r["rel"], r["frame"], r["fix"]))
    for m in models:
        for anchor, facing, rel, frame, fix in items():
            if (m, anchor, facing, rel, frame, fix) in done:
                continue
            raw = p1.chat(m, prompt(anchor, facing, rel, frame, fix))
            rec = {"model": m, "anchor": anchor, "facing": facing, "rel": rel, "frame": frame, "fix": fix,
                   "axis": p1.agreement(facing, rel), "raw": raw, **evaluate(anchor, facing, rel, frame, fix, raw)}
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(m, anchor, facing, rel, frame, fix, rec["label"], flush=True)
        print("model done", m, flush=True)
    print("done", flush=True)


def results():
    import pandas as pd
    R = pd.read_json(OUT, lines=True)
    B = pd.read_json(p1.OUT, lines=True)
    B = B[(B.para == 0) & B.model.isin(MODELS) & B.frame.isin(["viewer", "object", "ask"])].copy()
    B["fix"] = B.frame.map(lambda f: "ask (part 1)" if f == "ask" else "none (part 1)")
    B["frame"] = B.frame.replace({"ask": "ambiguous"})
    allr = pd.concat([B[["model", "frame", "fix", "axis", "label"]], R[["model", "frame", "fix", "axis", "label"]]])
    E = allr[allr.frame != "ambiguous"].copy()
    E["correct"] = E.apply(lambda r: r["label"] in (r["frame"], "both"), axis=1)
    L = ["# Whose left? Part 2: fixes", "",
         f"New outputs: {len(R)} (3 models, first paraphrase). Invalid JSON: {(R.label == 'invalid').sum()}.", "",
         "## Accuracy when the frame is stated, by fix (part-1 baseline = same prompts, no fix)", "", "```",
         E.pivot_table(index=["frame", "fix"], columns=["axis"], values="correct", aggfunc="mean").round(2).to_string(),
         "```", "", "## Same, per model (conflict items only: where part 1 failed)", "", "```",
         E[E.axis == "conflict"].pivot_table(index=["model", "frame"], columns="fix", values="correct", aggfunc="mean").round(2).to_string(),
         "```", ""]
    Rs = R[R.fix == "reason"]
    if "stated_dir_ok" in Rs:
        L += ["## Reason-first: is the stated direction right, and does the placement follow it?", "", "```",
              Rs.assign(correct=Rs.apply(lambda r: r["label"] in (r["frame"], "both"), axis=1))
                .groupby(["model", "frame"])[["stated_dir_ok", "correct"]].mean().round(2).to_string(), "```", ""]
    A = allr[allr.frame == "ambiguous"].assign(asked=lambda d: d.label == "asked")
    L += ["## Calibrated clarification (ideal: ask on conflict/orthogonal, not on agree)", "", "```",
          A.pivot_table(index=["model", "fix"], columns="axis", values="asked", aggfunc="mean").round(2).to_string(), "```", ""]
    open(os.path.join(RES, "RESULTS_fixes.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))


def selftest():
    # ego: sofa facing the camera (-y): its own right is -x... check: facing (0,-1), rot_left = (1,0) = its left -> right = (-1,0)
    assert ego_to_world(1, 0, "toward") == (-1, 0)
    assert ego_to_world(0, 1, "toward") == (0, -1)
    # object-frame 'left' of a sofa facing the camera is +x (camera's right)
    assert target_dir("toward", "left", "object") == (1, 0)
    # ego answer "left" (x' = -1.5) for a sofa facing the camera must land at world +x and be labelled object-correct
    x, y = ego_to_world(-1.5, 0, "toward")
    assert p1.label(x, y, "toward", "left") == "object", (x, y)
    assert "+x direction" in prompt("sofa", "toward", "left", "object", "hint")
    assert len(list(items())) == 5 * 3 * 4 * 6
    r = evaluate("sofa", "toward", "left", "ambiguous", "ask_explained", '{"clarify": "Whose left?"}')
    assert r["label"] == "asked"
    r = evaluate("sofa", "toward", "left", "object", "reason", '{"direction": "+x", "x": 1.5, "y": 0}')
    assert r["stated_dir_ok"] and r["label"] == "object", r
    print("selftest ok:", len(list(items())), "prompts per model")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    if cmd == "selftest":
        selftest()
    elif cmd == "prompt":
        for fx in ("hint", "reason", "ego"):
            print(prompt("sofa", "toward", "left", "object", fx), "\n----")
        print(prompt("sofa", "toward", "left", "ambiguous", "ask_explained"))
    elif cmd == "run":
        run()
    elif cmd == "results":
        results()
