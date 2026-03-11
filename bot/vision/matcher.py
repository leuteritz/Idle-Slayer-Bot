import cv2
import numpy as np
import os

from bot.vision.capture import grab_gray as _grab_gray

_PROJECT_ROOT  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENEMIES_DIR    = os.path.join(_PROJECT_ROOT, "assets", "enemies")
MINIGAMES_DIR  = os.path.join(_PROJECT_ROOT, "assets", "minigames")


class TemplateMatcher:

    def _load_template(self, filename: str, assets_dir: str = None) -> np.ndarray:
        """Lädt ein Template. Nutzt assets_dir falls angegeben, sonst assets/enemies/."""
        directory = assets_dir if assets_dir else ENEMIES_DIR
        path      = os.path.join(directory, filename)
        image     = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"Template '{path}' nicht gefunden!")
        return image

    @staticmethod
    def grab_gray(sct, monitor_idx: int) -> np.ndarray:
        return _grab_gray(sct, monitor_idx)

    def _find_one(self, gray_frame: np.ndarray, template: np.ndarray, confidence: float):
        result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            th, tw = template.shape
            return max_loc[0] + tw // 2, max_loc[1] + th // 2, max_val, tw, th
        return None

    def _find_all(self, gray_frame: np.ndarray, template: np.ndarray, confidence: float):
        result    = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)
        th, tw    = template.shape
        boxes     = [
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
