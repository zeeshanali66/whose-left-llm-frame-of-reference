# Results

Total placements: 284; invalid JSON: 0

## RQ1: ambiguous instructions where frames differ (share of placements)

```
label                   neither  object  viewer
model       axis                               
llama3.1:8b conflict       0.50    0.00     0.5
            orthogonal     0.08    0.42     0.5
```

## RQ2: accuracy when the frame is explicit, by whether the frames agree

```
axis                agree  conflict  orthogonal
model       frame                              
llama3.1:8b object   0.55       0.0        0.25
            viewer   0.51       0.5        0.50
```

## Paraphrase consistency

Share of items with the same label across all 3 paraphrases: llama3.1:8b: 0.98
