# Whose left? Part 2: fixes

New outputs: 1080 (3 models, first paraphrase). Invalid JSON: 0.

## Accuracy when the frame is stated, by fix (part-1 baseline = same prompts, no fix)

```
axis                  agree  conflict  orthogonal
frame  fix                                       
object ego             0.88      0.88        0.88
       hint            1.00      1.00        0.92
       none (part 1)   0.77      0.42        0.42
       reason          0.70      0.52        0.35
viewer hint            1.00      1.00        1.00
       none (part 1)   0.70      0.57        0.52
       reason          0.68      0.57        0.55
```

## Same, per model (conflict items only: where part 1 failed)

```
fix                 ego  hint  none (part 1)  reason
model      frame                                    
gemma3:12b object  0.70   1.0           0.20    0.25
           viewer   NaN   1.0           0.55    0.55
gemma4:12b object  1.00   1.0           0.65    0.80
           viewer   NaN   1.0           0.60    0.60
qwen3.5:9b object  0.95   1.0           0.40    0.50
           viewer   NaN   1.0           0.55    0.55
```

## Reason-first: is the stated direction right, and does the placement follow it?

```
                   stated_dir_ok  correct
model      frame                         
gemma3:12b object           0.33     0.33
           viewer           0.55     0.48
gemma4:12b object           0.75     0.75
           viewer           0.68     0.68
qwen3.5:9b object           0.52     0.48
           viewer           0.62     0.63
```

## Calibrated clarification (ideal: ask on conflict/orthogonal, not on agree)

```
axis                      agree  conflict  orthogonal
model      fix                                       
gemma3:12b ask (part 1)     0.0       0.0        0.00
           ask_explained    0.0       0.0        0.00
gemma4:12b ask (part 1)     0.0       0.0        0.00
           ask_explained    0.1       0.5        0.35
qwen3.5:9b ask (part 1)     0.0       0.0        0.00
           ask_explained    0.0       0.0        0.00
```
