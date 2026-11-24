# Results

Total placements: 3600; invalid JSON: 0

## RQ5: clarification rate (ideal: high for conflict/orthogonal, low for agree)

```
axis         agree  conflict  orthogonal
model                                   
gemma3:12b    0.12      0.12        0.10
gemma4:12b    0.00      0.00        0.00
llama3.1:8b   0.00      0.00        0.00
qwen2.5:7b    0.00      0.00        0.02
qwen3.5:9b    0.00      0.00        0.00
```

Questions asked: 21 of 900 ask-condition prompts; questions that mention the frame or perspective: 0.

## RQ1: ambiguous instructions where frames differ (share of placements)

```
label                   neither  object  viewer
model       axis                               
gemma3:12b  conflict       0.10    0.27    0.63
            orthogonal     0.22    0.28    0.50
gemma4:12b  conflict       0.00    0.40    0.60
            orthogonal     0.02    0.48    0.50
llama3.1:8b conflict       0.50    0.00    0.50
            orthogonal     0.13    0.37    0.50
qwen2.5:7b  conflict       0.00    0.50    0.50
            orthogonal     0.25    0.25    0.50
qwen3.5:9b  conflict       0.00    0.42    0.58
            orthogonal     0.10    0.38    0.52
```

## RQ2: accuracy when the frame is explicit, by whether the frames agree

```
axis                agree  conflict  orthogonal
model       frame                              
gemma3:12b  object   0.57      0.22        0.28
            viewer   0.52      0.60        0.50
gemma4:12b  object   0.92      0.65        0.50
            viewer   0.80      0.58        0.53
llama3.1:8b object   0.50      0.00        0.25
            viewer   0.50      0.50        0.50
qwen2.5:7b  object   0.75      0.40        0.27
            viewer   0.68      0.52        0.48
qwen3.5:9b  object   0.83      0.38        0.48
            viewer   0.80      0.58        0.50
```

## Paraphrase consistency

Share of items with the same label across all 3 paraphrases: gemma3:12b: 0.84, gemma4:12b: 0.89, llama3.1:8b: 0.96, qwen2.5:7b: 0.95, qwen3.5:9b: 0.88
