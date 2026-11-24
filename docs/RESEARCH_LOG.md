# Research log: problems we hit and how we handled them

### 1. Defining "left" so that a program can check it
"Left of the sofa" has two readings. We used a top-down world with the camera at (0, -10) looking toward +y, so the viewer's left is always -x. An anchor that faces direction v has its own left at v rotated 90° counter-clockwise. A placement is labelled **viewer**, **object**, **both** (when the readings agree) or **neither**. The checker has unit tests (`python -I for_pipeline.py selftest`) that run before any model call, so a sign error cannot silently flip the results.

### 2. Making sure the readings actually disagree
If the anchor faces away from the viewer, both readings give the same answer and the item tells us nothing about the default frame. Every item is therefore tagged by **axis**: *agree* (facing away), *conflict* (facing the viewer: left and right swap) or *orthogonal* (facing sideways: "left" in one frame is "front" or "behind" in the other). RQ1 uses only the conflict and orthogonal items.

### 3. Wording effects
One phrasing could favour one frame by accident. Every item has three paraphrases, and we report how often a model gives the same label across them.

### 4. The newest models "think" first
Qwen 3.5 and Gemma 4 produce a reasoning trace by default, which was slow and sometimes put text before the JSON. We turned thinking off (`think: false`) so all five models answer the same kind of prompt in one step. With JSON mode and one retry, 0 of 3,600 outputs were invalid.

### 5. "It asked a question" is not the same as "it asked the right question"
The first count of clarification requests made Gemma 3 look somewhat cautious (10 to 12%). Reading the questions showed they were about distance ("How far left of the sofa should the lamp be?"), not about whose left, and they came just as often when the frames agreed. We added an automatic check for whether a question mentions the frame or perspective. Result: 0 of 21 questions did.

### 6. High consistency can hide a broken model
Llama 3.1 8B looked the most consistent across paraphrases (0.96). Looking at the raw coordinates showed it often returns the same point (for example (-1.5, 0)) regardless of the relation asked for. We report this next to the consistency score so the number is not misread as robustness.

### 7. Running unattended overnight on one home GPU (8 GB)
A watchdog script stops the run if the GPU passes 84 °C and logs temperatures every 30 s (no alerts in this run; peak 66 °C). The run is resumable: finished prompts are skipped on restart.

### 8. Part 2: testing fixes
After finding the failure, we tested four fixes on the 3 strongest models (first paraphrase only, since part 1 showed
small paraphrase effects for them). Design choices: the reason-first example JSON originally showed "+x" as the
direction, which could bias answers, so it was replaced by a neutral placeholder; answers given in the object's own
coordinates are rotated back to the world before checking, with unit tests for the rotation.
Result: hints and object-centred coordinates fix most errors; asking the model to reason first does not.

## Next steps
- Run the human survey (RQ3) to see which reading people expect.
- Test whether giving the model the user's position or gaze direction in the prompt removes the ambiguity.
- Extend to real 3D scenes in the WebXR viewer, and to a robot that must explain its own route (see the follow-up project "Says vs. Does").
