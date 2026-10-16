REVIEW 2 — CODE DEVELOPMENT REPORT
Real-Time Vision-Based Industrial Quality Inspection and Shape Sorting System
Course: Microprocessor, Microcontroller and Interfacing Techniques | Course Code: 21ECC301P Team: Adithya Sajeev Kumar (RA2411004010326), Abhinandh M (RA2411004010336), Dharun Prakash (RA2411004010342)
1. Project objective
The project develops a low-cost prototype that inspects a single object in a controlled camera region, classifies its silhouette as a circle, triangle, square/rectangle, or unknown, applies configurable geometric defect rules, and sends a compact decision code to a microcontroller for sorting or rejection. The implementation follows the Review 1 architecture: the laptop/Raspberry Pi performs image processing while the MCU handles motor and actuator interfacing.
2. Software architecture
Module
Implementation
Responsibility
Vision application
Python 3, OpenCV, NumPy
Camera acquisition, ROI, filtering, thresholding, morphology, contours, feature extraction, shape classification, rule-based inspection, annotated preview.
Communication
USB serial / pySerial
Sends C, S, T, or D as a newline-terminated ASCII command at 115200 baud.
MCU firmware
Arduino-compatible C++ / Servo library
Controls motor-driver signals, reject/sort servos, LEDs, buzzer, and good/defect counters.
Configuration and tests
JSON + unittest
Allows threshold calibration and checks core shape-detection behavior on synthetic images.
3. Image-processing algorithm
Image acquisition: OpenCV reads frames from a USB webcam or compatible camera device.
Region of interest (ROI): A normalized rectangle restricts processing to the inspection zone.
Noise reduction: A 5×5 Gaussian blur reduces high-frequency noise.
Segmentation: Otsu thresholding creates two candidate polarities; the application ignores contours touching the ROI boundary to avoid treating the background as the object.
Morphology: Opening suppresses small specks and closing fills small gaps in the segmented foreground.
Contour and features: The largest valid contour is measured for area, perimeter, circularity, convex-hull solidity, bounding-box aspect ratio, polygon vertices, and nested holes.
Decision rules: The object is flagged for configured size violations, unknown/deformed outline, low solidity, unexpected holes, or circle circularity below threshold.
Output: The result is drawn on the preview and mapped to a serial code for the MCU.
4. Defect rules and important interpretation
The baseline detects geometric/silhouette anomalies under controlled lighting. It is not a universal industrial defect detector. A crack that does not change the outer silhouette may not be detected. Surface scratches, subtle material defects, overlapping objects, and changing illumination require additional methods and validation. CNN/ML is intentionally not included because Review 1 identifies it as a future enhancement.
Feature / rule
Purpose
Calibration note
Area min/max
Reject objects outside expected pixel-size range.
Depends on camera resolution, distance, and object dimensions.
Solidity
Flags strongly concave or missing-portion silhouettes.
Tune against examples of acceptable and defective parts.
Hole count
Flags enclosed holes when not allowed.
Small holes/noise are filtered by a relative area threshold.
Polygon vertices + circularity
Classifies common silhouettes and flags unknown/deformed outlines.
Works best with matte objects and a contrasting background.
5. Serial protocol
Code
Vision meaning
MCU action
C
Good circle
Move sorting servo to circle-bin angle
S
Good square/rectangle
Move sorting servo to square-bin angle
T
Good triangle
Move sorting servo to triangle-bin angle
D
Defective or unknown
Move rejection servo
The MCU returns ACK messages with good/defect counters or ERR messages. The current baseline uses a simple serial result protocol. Although the IR input pin is declared in firmware, it is not yet used as a trigger/handshake. The Python application sends when the visible result signature changes; for a moving conveyor, production-grade object tracking requires a sensor-triggered request/reply sequence and position timing/encoder support.
6. Files delivered
vision/inspector.py — OpenCV processing, live preview, still-image mode, and optional serial transmission.
config.json — camera size, ROI, area limits, morphology, solidity, hole, and circularity thresholds.
firmware/vision_sorter.ino — MCU motor/servo/indicator control and serial parser.
requirements.txt — Python dependencies.
tests/test_inspector.py — four synthetic-image smoke tests.
README.md — setup, wiring cautions, commands, calibration, and limitations.
7. Verification performed
The Python smoke-test suite was executed in the development environment. All four tests passed: circle classification, square/rectangle classification, triangle classification, and empty-frame handling. These are algorithm-level synthetic tests only; they do not establish real-camera accuracy, physical sorting accuracy, processing-time guarantees, or successful hardware actuation. Those must be measured on the actual prototype.
8. Setup and execution
Create and activate a Python virtual environment, then run: pip install -r requirements.txt
Live camera only: python vision/inspector.py --config config.json --camera 0
With MCU: python vision/inspector.py --config config.json --camera 0 --serial COM4 (replace COM4 with the correct port)
Still image: python vision/inspector.py --config config.json --snapshot path/to/image.jpg
Tests: python -m unittest discover -s tests -v
Open firmware/vision_sorter.ino in Arduino IDE, select the correct board/port, and upload.
9. Safety and hardware notes
Do not connect motors or servo power directly to MCU pins or rely on the USB port for motor loads. Use a motor driver rated for the motor stall current and a suitable external regulated supply for servos/motors. Tie the external supply ground to MCU ground. Verify pin mappings, servo angles, belt direction, emergency stop, and mechanical clearances before running the conveyor. Start with the belt disconnected and test actuators individually.
10. Remaining work before final review
Calibrate ROI and thresholds using the actual camera, lighting, and sample objects.
Collect labeled good/defective samples and calculate defect precision/recall, shape accuracy, sorting accuracy, and per-object processing time.
Integrate IR-triggered inspection and object-to-actuator timing; verify one decision per physical object.
Adapt the firmware to the exact selected MCU if STM32 rather than Arduino-compatible hardware is used.
Add LCD/OLED support if required by the final prototype; the current baseline reports counters over serial.
Capture demo evidence: live annotated frames, serial logs, actuator video, test table, and measured results.
Status statement for Review 2: The code baseline covers the main vision pipeline, shape classification, configurable geometric inspection rules, serial decision output, and MCU actuation logic. Hardware integration, calibration, real-object validation, and performance measurement remain to be demonstrated. Do not describe the system as 75% complete unless the team can substantiate that percentage against its own task checklist.
