# Validation iteration log

Predetermined candidates, training seed 20261029. Checkpoints and calibration use validation only. Test features are not extracted until this log and frozen.json have been written.

| Model | Change and reason | Validation F1 | AUC | Recall | Clean alarms / 1,000 | Epoch | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| linear_r0.001 | Learn weights over fixed pixel summaries | 0.8911 | 0.9509 | 0.9000 | 120.0 | 150 | KEPT: frozen final model |
| linear_r0.01 | Learn weights over fixed pixel summaries | 0.8809 | 0.9488 | 0.9000 | 143.3 | 150 | DROPPED: lower validation selection rank |
| neural32_r0.001 | Add nonlinear interactions | 0.8824 | 0.9519 | 0.9000 | 140.0 | 19 | DROPPED: lower validation selection rank |
| neural32_r0.01 | Add nonlinear interactions | 0.8696 | 0.9564 | 0.9000 | 170.0 | 148 | DROPPED: lower validation selection rank |
| ablate_spatial | Remove spatial layout to measure its contribution | 0.6986 | 0.7344 | 0.9000 | 676.7 | 159 | ABLATION: diagnostic only |
| ablate_normalization | Remove intensity normalization to measure its contribution | 0.8896 | 0.9524 | 0.9000 | 123.3 | 152 | ABLATION: diagnostic only |

All six fits are retained, including negative ablations. Per-epoch validation log loss and elapsed CPU fit time are in data/v2/iterations.json. This is a bounded grid, not six sequential discoveries. No post-test model revision is allowed.
