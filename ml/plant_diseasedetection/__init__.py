"""Plant disease detection package (YOLOv11x, 116 classes).

Wraps the Multi-Domain Plant Disease Detection benchmark model hosted on
Hugging Face at ``Ananthakrishnanmzen/PlantDiseaseDetection``.

Authoritative source:
https://github.com/SIV-TK/A-YOLOv11x-Benchmark-on-116-Classes-Using-Combined-Laboratory-and-Field-Images
"""

from __future__ import annotations

from .model import PlantDiseaseDetector, load_detector

__all__ = ["PlantDiseaseDetector", "load_detector"]

__version__ = "1.0.0"
