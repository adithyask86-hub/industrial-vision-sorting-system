# Testing Guide

## 1. Purpose

This document describes the software and hardware tests for the Industrial Vision Sorting System.

## 2. Software Testing

The Python inspection module uses OpenCV and NumPy to process images and estimate object shapes and visible defects.

Run the existing test file from the project root:

```bash
python -m pytest tests/test_inspector.py -v
```

If pytest is not installed, install the project dependencies first:

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

## 3. Camera Testing

1. Connect a USB camera to the computer.
2. Check that the operating system recognizes the camera.
3. Run the vision application using the project's configured camera settings.
4. Confirm that images are captured and displayed correctly.
5. Test with circles, squares, rectangles, triangles, and visibly defective or unfamiliar objects.

## 4. Serial Communication Testing

1. Connect the Arduino to the computer using USB.
2. Confirm that the selected serial port is correct.
3. Set the communication speed to 115200 baud.
4. Send C, S, T, and D, each followed by a newline.
5. Check that the Arduino returns an acknowledgement and updates its counters.

Close any other application using the serial port before running the Python application.

## 5. Hardware Testing

1. Test the Arduino without motor or servo loads initially.
2. Verify the LED and buzzer outputs.
3. Test servo movement using a suitable external power supply.
4. Verify the motor driver connections and motor direction.
5. Test the complete mechanism at low speed with the sorting area clear.

## 6. Expected Results

| Test | Expected Result |
|---|---|
| Camera capture | An image is received |
| Shape inspection | A supported shape is classified |
| Serial transmission | A decision code is transmitted |
| Arduino reception | A valid code is acknowledged |
| Defect decision | Red LED and buzzer activate |
| Good-object decision | Green LED activates |
| Sorting mechanism | The corresponding servo position is commanded |

These are expected outcomes, not confirmed test results. Record actual results after executing each test.

## 7. Limitations

The current system is a rule-based visual inspection prototype. Its results depend on lighting, camera position, background contrast, object size, and configured thresholds. It is not a trained machine-learning defect detector.

The IR sensor input is reserved for future triggering integration in the current firmware baseline.
