import cv2
import numpy as np


def grab_gray(sct, monitor_idx: int) -> np.ndarray:
    monitor    = sct.monitors[monitor_idx]
    screenshot = sct.grab(monitor)
    frame      = np.array(screenshot)
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
