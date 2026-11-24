"""Make the human-baseline survey: top-down scene images with candidate positions A-D.

Each image shows the camera (at the bottom), an anchor object with an arrow for the way it faces, and four
labelled spots around it. The respondent picks the spot that matches an instruction such as
"Put the lamp to the left of the sofa." Answers map back to viewer / object frames via for_pipeline.label().
"""
import os, sys, json, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import for_pipeline as fp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "survey")
os.makedirs(OUT, exist_ok=True)
SPOTS = {(-1.5, 0): None, (1.5, 0): None, (0, -1.5): None, (0, 1.5): None}
# Only cases where the two frames DISAGREE are informative for the survey.
CASES = [(a, f, r) for a in ["sofa", "car", "armchair", "person"] for f in ["toward", "side"] for r in ["left", "front"]]
random.seed(3)
key = []
for i, (anchor, facing, rel) in enumerate(CASES, 1):
    spots = list(SPOTS)
    random.shuffle(spots)
    letters = dict(zip("ABCD", spots))
    fig, ax = plt.subplots(figsize=(4.2, 5.2))
    ax.set_xlim(-3.2, 3.2); ax.set_ylim(-5.6, 3.2); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(plt.Rectangle((-0.6, -0.4), 1.2, 0.8, color="#8fb3d9"))
    dx, dy = fp.FACING[facing]
    ax.annotate("", xy=(dx * 1.0, dy * 1.0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=2.5, color="#1d4e89"))
    ax.text(0, 0, anchor, ha="center", va="center", fontsize=10, color="white", weight="bold")
    for L, (x, y) in letters.items():
        ax.add_patch(plt.Circle((x, y), 0.32, color="#f2a541"))
        ax.text(x, y, L, ha="center", va="center", fontsize=12, weight="bold")
    ax.plot(0, -5, marker="^", markersize=16, color="#444")
    ax.text(0, -5.45, "camera / you", ha="center", fontsize=9)
    ax.text(0, 2.9, f"The arrow shows the way the {anchor} is facing", ha="center", fontsize=8, color="#1d4e89")
    plt.savefig(os.path.join(OUT, f"q{i:02d}.png"), dpi=150, bbox_inches="tight"); plt.close()
    target = fp.TARGETS[anchor]
    key.append({"q": i, "question": f"Put the {target} {fp.REL_TEXT[rel]} the {anchor}. Which spot (A, B, C or D)?",
                "anchor": anchor, "facing": facing, "rel": rel,
                "spot_labels": {L: fp.label(x, y, facing, rel) for L, (x, y) in letters.items()}})
with open(os.path.join(OUT, "answer_key.json"), "w") as f:
    json.dump(key, f, indent=1)
with open(os.path.join(OUT, "FORM_TEXT.md"), "w", encoding="utf-8") as f:
    f.write("# Google Form text (copy into a new Form; one image question per item)\n\n"
            "**Title:** Where would you put it? (2-minute spatial language survey)\n\n"
            "**Intro:** This is part of a small research project on how people and AI systems understand words like "
            "'left' and 'in front of'. There are no right or wrong answers, so go with your first instinct. "
            "The survey is anonymous: no names or emails are collected.\n\n"
            "**Before the questions (optional):** First language? (Urdu / Punjabi / English / Other) · "
            "Do you play 3D video games? (Often / Sometimes / Never)\n\n")
    for k in key:
        f.write(f"{k['q']}. [image q{k['q']:02d}.png] {k['question']}\n")
print(len(key), "survey items written to", OUT)
