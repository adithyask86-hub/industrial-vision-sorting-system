# System Architecture

## 1. Project Overview

The Industrial Vision Sorting System is designed to inspect objects using a camera and classify them according to their shape and visible features.

The system combines Python, OpenCV, serial communication, and a microcontroller to demonstrate automated visual inspection and sorting.

## 2. System Workflow

1. **Image Acquisition:** A USB camera captures images of objects.
2. **Image Processing:** Python and OpenCV process the captured images.
3. **Feature Extraction:** The software analyzes contours and geometric properties to estimate the object's shape and identify possible defects.
4. **Classification:** The software assigns a decision code.
5. **Serial Communication:** The decision is transmitted to the microcontroller through USB serial communication.
6. **Actuation:** The microcontroller controls the motor and servo mechanisms according to the received code.

## 3. Decision Codes

| Code | Meaning |
|---|---|
| C | Good circle |
| S | Good square or rectangle |
| T | Good triangle |
| D | Defective or unknown object |

## 4. Software Components

- Python: Main application logic.
- OpenCV: Image processing and contour analysis.
- NumPy: Numerical operations.
- Serial communication: Transfers inspection decisions to the microcontroller.

## 5. Microcontroller Components

The firmware is designed for an Arduino Uno/Nano-compatible board. It receives decision codes and controls the conveyor motor, sorting servos, status LEDs, and buzzer.

## 6. Prototype Limitations

The baseline uses feature-based, rule-based inspection. It is not a trained machine-learning defect detector. Classification accuracy depends on lighting, camera positioning, object contrast, and the inspection thresholds.

## 7. Safety

Test the software and serial communication before connecting mechanical loads. Use a suitable motor driver, separate regulated power for motors and servos, and a common ground where required.
