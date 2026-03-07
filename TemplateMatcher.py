import cv2
import numpy as np
import os

BASE_DIR    = os.path.dirname(__file__)
ENEMIES_DIR = os.path.join(BASE_DIR, "enemies")


class TemplateMatcher:

    def _load_template(self, filename: str) -> np.ndarray:
        path  = os.path.join(ENEMIES_DIR, filename)
        image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Template '{path}' nicht gefunden!")
        return image

    def _find_one(self, gray_frame: np.ndarray, template: np.ndarray, confidence: float):
        """Gibt (cx, cy, conf, tw, th) zurück oder None."""
        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            th, tw = template.shape
            cx = max_loc[0] + tw // 2
            cy = max_loc[1] + th // 2
            return cx, cy, max_val, tw, th
        return None

    def _find_all(self, gray_frame: np.ndarray, template: np.ndarray, confidence: float):
        result    = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)
        th, tw    = template.shape
        boxes = [
            (pt[0] + tw // 2, pt[1] + th // 2)
            for pt in zip(*locations[::-1])
        ]
        return self._deduplicate(boxes)

    def _deduplicate(self, boxes, min_dist: int = 20):
        unique = []
        for b in boxes:
            if not any(
                abs(b[0] - u[0]) < min_dist and abs(b[1] - u[1]) < min_dist
                for u in unique
            ):
                unique.append(b)
        return unique
