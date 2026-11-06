# AgroAI Pest Detection — YOLO11s (IP102, 102 pest classes)

This package wraps the
[IP102 Pest Detector — YOLO11 Small](https://huggingface.co/Yashwanth1508/AgroAI-pest-detection)
model trained on the IP102 benchmark dataset for real-time agricultural pest detection.

## Model card

| Item | Value |
|------|-------|
| Architecture | YOLO11 Small (YOLO11s) |
| Dataset | IP102 (balanced, 34K+ images) |
| Image sizes | 640 × 640 and 896 × 896 |
| Total classes | 102 pest species |
| Precision (val) | 0.744 |
| Recall (val) | 0.789 |
| mAP@0.5 (val) | 0.815 |
| mAP@0.5:0.95 (val) | 0.605 |
| License | MIT |

## Quick start

```bash
# from the repo root
pip install -r ml/agroai_pest_detection/requirements.txt
```

```python
from ml.agroai_pest_detection import PestDetector

detector = PestDetector()  # downloads weights on first use
results = detector.predict("field_image.jpg", conf=0.25, imgsz=640)
for r in results:
    for box in r.boxes:
        print(detector.class_name(int(box.cls[0])), f"{float(box.conf[0]):.2%}")
```

## Weight files

Pre-trained weights (`best.pt`) are fetched automatically from Hugging Face on first
load via `ultralytics` / `huggingface_hub`. To bundle weights locally, place `best.pt`
in `ml/agroai_pest_detection/weights/`.

```
ml/agroai_pest_detection/
├── __init__.py
├── model.py
├── inference.py
├── requirements.txt
├── pests.yaml
├── README.md
└── weights/
    └── .gitkeep
```

## Citation

If you use this model or the IP102 dataset in research, please cite:

```
@inproceedings{wu2019ip102,
  title={IP102: A Large-Scale Benchmark Dataset for Insect Pest Recognition},
  author={Wu, Shiyu and Zhan, Chuming and Lai, Zhi-Ming and others},
  booktitle={CVPR},
  year={2019}
}

@software{agroai_2026_pest_detection,
  author = {Yashwanth},
  title  = {AgroAI-pest-detection: IP102 Pest Detector YOLO11s},
  year   = {2026},
  url    = {https://huggingface.co/Yashwanth1508/AgroAI-pest-detection},
}
```
