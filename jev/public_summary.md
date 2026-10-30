# Jev 1.14 image model: numbers safe to publish

Model jev-1.14.0 (experimental image and Box features, per TypeSafe). 150 synthetic parcel images and 150 real bin photos; one fixed prompt each, no tuning.

- Parcel damage yes/no: AUC 0.76 [0.68, 0.83]; recall 0.17; clean false alarms 0 per 1,000. Our trained local model on the same images: AUC 0.96.
- Damage box: median overlap (IoU) with truth 0.54 [0.49, 0.60]; 59% of boxes overlap >= 0.5. The box step returns a box even on clean images (75 of 75), so a presence check must come first.
- Bin fill level (4 classes): accuracy 0.58 [0.50, 0.66]; macro-F1 0.54 [0.46, 0.61]; empty vs not-empty accuracy 0.93 [0.89, 0.97]. Our fine-tuned local model: accuracy 0.78, macro-F1 0.75.
- Speed: median 0.15 s per call, p95 0.26 s; about 698 to 962 input tokens per image.
- Parcels are synthetic; bin photos are not redistributed. Real parcel photos were not tested.
