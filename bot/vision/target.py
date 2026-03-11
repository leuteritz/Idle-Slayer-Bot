import numpy as np
from bot.vision.matcher import TemplateMatcher


class Target(TemplateMatcher):
    def __init__(self, filename: str, priority: int, confidence: float):
        self.image      = self._load_template(filename)
        self.name       = filename
        self.priority   = priority
        self.confidence = confidence

    def find(self, gray_frame: np.ndarray):
        """Gibt (x, y, confidence) zurück wenn gefunden, sonst None."""
        match = self._find_one(gray_frame, self.image, self.confidence)
        if match:
            cx, cy, conf, tw, th = match
            return cx, cy, conf
        return None
