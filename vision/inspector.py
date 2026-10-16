"""Feature-based visual inspection for the Review 2 conveyor sorting prototype.

Designed for a fixed USB camera, controlled lighting, and a contrasting matte
background. This is a rule-based prototype, not a trained ML defect detector.
"""
from __future__ import annotations
import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

@dataclass
class InspectionResult:
    status: str                 # GOOD or DEFECT
    shape: str                  # CIRCLE, SQUARE, TRIANGLE, RECTANGLE, UNKNOWN
    reason: str
    area_px: float
    circularity: float
    solidity: float
    aspect_ratio: float
    vertices: int
    hole_count: int
    processing_ms: float = 0.0

    def protocol_code(self) -> str:
        """One-line protocol consumed by the MCU firmware."""
        if self.status != "GOOD":
            return "D"
        return {"CIRCLE": "C", "SQUARE": "S", "RECTANGLE": "S", "TRIANGLE": "T"}.get(self.shape, "D")


def classify_shape(contour: np.ndarray, perimeter: float, circularity: float,
                   aspect_ratio: float) -> tuple[str, int]:
    approx = cv2.approxPolyDP(contour, 0.035 * perimeter, True)
    vertices = len(approx)
    if vertices == 3:
        return "TRIANGLE", vertices
    if vertices == 4:
        shape = "SQUARE" if 0.85 <= aspect_ratio <= 1.15 else "RECTANGLE"
        return shape, vertices
    if vertices >= 7 and circularity >= 0.72:
        return "CIRCLE", vertices
    return "UNKNOWN", vertices


def count_holes(binary: np.ndarray, outer_contour: np.ndarray) -> int:
    """Count nested contour holes inside the selected foreground object."""
    hierarchy_data = cv2.findContours(binary.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours, hierarchy = hierarchy_data[-2], hierarchy_data[-1]
    if hierarchy is None:
        return 0
    outer_area = cv2.contourArea(outer_contour)
    selected_index = max(range(len(contours)), key=lambda i: cv2.contourArea(contours[i]))
    # Count child contours of the largest outer contour. Ignore tiny noise.
    count = 0
    child = hierarchy[0][selected_index][2]
    while child != -1:
        if cv2.contourArea(contours[child]) > max(20.0, outer_area * 0.005):
            count += 1
        child = hierarchy[0][child][0]
    return count


def inspect_frame(frame: np.ndarray, config: dict) -> tuple[Optional[InspectionResult], np.ndarray]:
    """Return the largest object's inspection result and an annotated frame."""
    started = time.perf_counter()
    annotated = frame.copy()
    height, width = frame.shape[:2]
    roi = config.get("roi", [0.05, 0.05, 0.95, 0.95])
    x1, y1 = int(roi[0] * width), int(roi[1] * height)
    x2, y2 = int(roi[2] * width), int(roi[3] * height)
    if x2 <= x1 or y2 <= y1:
        raise ValueError("ROI must have x2>x1 and y2>y1, using normalized 0..1 coordinates")
    crop = frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Otsu segmentation; choose polarity by the larger foreground contour.
    _, binary_a = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary_b = cv2.bitwise_not(binary_a)
    kernel_size = int(config.get("morph_kernel", 5))
    kernel_size = max(3, kernel_size | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    candidates = []
    for binary in (binary_a, binary_b):
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
        found = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = found[-2]
        # Ignore contours that touch the ROI border: these are commonly the
        # segmented background rather than a physical object.
        valid = []
        for contour in contours:
            bx, by, bw, bh = cv2.boundingRect(contour)
            if bx <= 1 or by <= 1 or bx + bw >= cleaned.shape[1] - 1 or by + bh >= cleaned.shape[0] - 1:
                continue
            area = cv2.contourArea(contour)
            if area >= float(config.get("min_area_px", 500)):
                valid.append((area, contour, cleaned))
        candidates.extend(valid)
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 180, 0), 2)
    if not candidates:
        return None, annotated

    area, contour, cleaned = max(candidates, key=lambda item: item[0])
    perimeter = cv2.arcLength(contour, True)
    if perimeter <= 0:
        return None, annotated
    moments = cv2.moments(contour)
    x, y, w, h = cv2.boundingRect(contour)
    aspect = w / float(h) if h else 0.0
    circularity = (4.0 * np.pi * area) / (perimeter * perimeter)
    hull_area = cv2.contourArea(cv2.convexHull(contour))
    solidity = area / hull_area if hull_area else 0.0
    shape, vertices = classify_shape(contour, perimeter, circularity, aspect)

    # Convert local ROI contour to full-frame coordinates for display.
    full_contour = contour + np.array([[[x1, y1]]], dtype=contour.dtype)
    cv2.drawContours(annotated, [full_contour], -1, (0, 220, 0), 2)
    holes = count_holes(cleaned, contour)

    defects = []
    min_area = float(config.get("min_area_px", 500))
    max_area = float(config.get("max_area_px", 1000000))
    if not (min_area <= area <= max_area):
        defects.append("SIZE_OUT_OF_RANGE")
    if shape == "UNKNOWN":
        defects.append("UNKNOWN_OR_DEFORMED_SHAPE")
    if solidity < float(config.get("min_solidity", 0.88)):
        defects.append("IRREGULAR_OR_MISSING_PORTION")
    if holes > int(config.get("allowed_holes", 0)):
        defects.append("UNEXPECTED_HOLE")
    if shape == "CIRCLE" and circularity < float(config.get("min_circle_circularity", 0.78)):
        defects.append("CIRCLE_DEFORMATION")

    status = "DEFECT" if defects else "GOOD"
    reason = ",".join(defects) if defects else "PASS"
    result = InspectionResult(status, shape, reason, float(area), float(circularity),
                              float(solidity), float(aspect), vertices, holes,
                              (time.perf_counter() - started) * 1000.0)
    label = f"{status} | {shape} | {reason}"
    color = (0, 0, 255) if status == "DEFECT" else (0, 180, 0)
    cv2.putText(annotated, label[:70], (max(5, x1), max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)
    return result, annotated


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenCV industrial visual inspection")
    parser.add_argument("--config", default="config.json", help="Path to JSON configuration")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index")
    parser.add_argument("--serial", default="", help="Serial port, e.g. COM4 or /dev/ttyACM0; blank disables MCU")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--snapshot", default="", help="Inspect one image file instead of live camera")
    args = parser.parse_args()
    config = load_config(args.config)
    serial_port = None
    if args.serial:
        try:
            import serial
            serial_port = serial.Serial(args.serial, args.baud, timeout=0.1, write_timeout=1)
            time.sleep(2.0)  # Arduino-class boards often reset on serial open.
            print(f"Serial connected: {args.serial} @ {args.baud}")
        except Exception as exc:
            raise SystemExit(f"Could not open serial port {args.serial}: {exc}")

    if args.snapshot:
        frame = cv2.imread(args.snapshot)
        if frame is None:
            raise SystemExit(f"Could not read image: {args.snapshot}")
        result, view = inspect_frame(frame, config)
        print(json.dumps(asdict(result) if result else {"status": "NO_OBJECT"}, indent=2))
        cv2.imshow("Inspection result", view)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    camera = cv2.VideoCapture(args.camera)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, int(config.get("camera_width", 640)))
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, int(config.get("camera_height", 480)))
    if not camera.isOpened():
        raise SystemExit("Camera could not be opened. Check --camera index and camera permissions.")
    print("Live inspection started. Press q to quit. Place one object in the ROI at a time.")
    last_send = 0.0
    last_signature = None
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Camera frame read failed")
                break
            result, view = inspect_frame(frame, config)
            if result:
                cv2.putText(view, f"Area:{result.area_px:.0f}  Solidity:{result.solidity:.2f}",
                            (12, view.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (255, 255, 255), 2, cv2.LINE_AA)
                signature = (result.status, result.shape, result.reason)
                # Avoid flooding the MCU while the same stationary object remains in view.
                now = time.monotonic()
                if serial_port and signature != last_signature and now - last_send > 1.0:
                    serial_port.write((result.protocol_code() + "\n").encode("ascii"))
                    last_send, last_signature = now, signature
                    print(f"TX {result.protocol_code()} | {result.status} {result.shape}: {result.reason}")
                elif signature != last_signature:
                    print(f"{result.status} {result.shape}: {result.reason}")
                    last_signature = signature
            else:
                last_signature = None
                cv2.putText(view, "NO OBJECT DETECTED", (12, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.imshow("Industrial Visual Inspection - Review 2", view)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        if serial_port:
            serial_port.close()

if __name__ == "__main__":
    main()
