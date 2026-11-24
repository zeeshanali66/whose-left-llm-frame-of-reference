# Whose left? Frame-of-reference choices when LLMs place objects in a 3D scene

"Put the lamp to the left of the sofa." Left from the **viewer's** point of view, or the **sofa's own** left?
The two readings disagree whenever the sofa faces the viewer. This small study measures which reading
local open LLMs choose when they *generate* a 3D layout, whether they follow an explicitly stated frame,
and whether they ask for clarification when (and only when) the instruction is genuinely ambiguous.

Prior frame-of-reference work (e.g., What'sUp, COMFORT) studies *perception* of existing images; text-to-3D
layout systems (LayoutGPT, Holodeck) check constraints under one fixed reading. This project looks at the
*generation* side.

## Research questions
1. **Default frame:** with no frame stated, which frame do models use?
2. **Instruction following:** with "from the camera's view" / "from the sofa's own perspective", do they comply, and does accuracy drop when the frames conflict?
3. **Human comparison:** do model defaults match what people expect? (survey materials in `survey/`)
4. **Calibrated clarification:** when allowed to ask, do models ask "your left or the sofa's left?" only when the frames actually disagree?

## Design
- Top-down world: camera at (0, -10) looking toward +y; anchor at the origin facing **away**, **toward**, or **sideways**.
- 5 anchors × 4 relations (left/right/front/behind) × 3 facings × frame conditions (ambiguous / viewer / object / ask) × 3 paraphrases.
- A geometric checker labels every placement as viewer-consistent, object-consistent, both, or neither.
- Models (local, via Ollama): Llama 3.1 8B, Qwen 2.5 7B, Gemma 3 12B, Qwen 3.5 9B, Gemma 4 12B.
- `viewer/index.html`: a three.js / WebXR viewer that renders the generated scenes (VR headset optional).

## Run
```
python -I for_pipeline.py selftest   # checker unit tests, no model needed
python -I for_pipeline.py pilot      # 12 prompts on one model
python -I for_pipeline.py run        # all prompts, all models (resumable)
python -I for_pipeline.py results    # tables -> results/RESULTS.md
python -I make_survey.py             # survey images + answer key
```
`watchdog.py` stops a run if the GPU gets too hot (used for unattended overnight runs).

## Status
Data collection in progress; results will be added to `results/RESULTS.md`.

## Disclosure
Code and documentation were written with the help of an AI assistant; the research design, checking and
decisions are the author's.

## License
MIT
