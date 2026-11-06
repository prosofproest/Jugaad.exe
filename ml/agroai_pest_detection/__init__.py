"""AgroAI pest detection package (YOLO11s, IP102, 102 pest classes).

Wraps the IP102 Pest Detector model hosted on Hugging Face at
``Yashwanth1508/AgroAI-pest-detection``.

Authoritative model page:
https://huggingface.co/Yashwanth1508/AgroAI-pest-detection
IP102 benchmark (CVPR 2019):
https://ip102.github.io/
"""

from __future__ import annotations

from .model import PestDetector, load_detector

__all__ = ["PestDetector", "load_detector"]

__version__ = "1.0.0"
