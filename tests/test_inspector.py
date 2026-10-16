import unittest
import cv2
import numpy as np
from vision.inspector import inspect_frame

CONFIG = {
    "roi": [0.0, 0.0, 1.0, 1.0], "min_area_px": 300,
    "max_area_px": 1000000, "morph_kernel": 3, "min_solidity": 0.80,
    "allowed_holes": 0, "min_circle_circularity": 0.70
}

class InspectorSmokeTests(unittest.TestCase):
    def make_frame(self, kind):
        frame = np.full((240, 320, 3), 245, dtype=np.uint8)
        if kind == "circle":
            cv2.circle(frame, (160, 120), 45, (20, 20, 20), -1)
        elif kind == "square":
            cv2.rectangle(frame, (115, 75), (205, 165), (20, 20, 20), -1)
        elif kind == "triangle":
            points = np.array([[160, 65], [105, 165], [215, 165]], np.int32)
            cv2.fillPoly(frame, [points], (20, 20, 20))
        return frame

    def test_circle_shape(self):
        result, _ = inspect_frame(self.make_frame("circle"), CONFIG)
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, "CIRCLE")

    def test_square_shape(self):
        result, _ = inspect_frame(self.make_frame("square"), CONFIG)
        self.assertIsNotNone(result)
        self.assertIn(result.shape, ("SQUARE", "RECTANGLE"))

    def test_triangle_shape(self):
        result, _ = inspect_frame(self.make_frame("triangle"), CONFIG)
        self.assertIsNotNone(result)
        self.assertEqual(result.shape, "TRIANGLE")

    def test_empty_frame_returns_no_object(self):
        frame = np.full((240, 320, 3), 245, dtype=np.uint8)
        result, _ = inspect_frame(frame, CONFIG)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
