# Real-Time Vision-Based Industrial Quality Inspection and Shape Sorting System

**Review 2 software baseline** — Python/OpenCV vision application + serial-controlled MCU firmware.

## Architecture

`USB webcam → Python/OpenCV on laptop or Raspberry Pi → USB serial → Arduino-compatible MCU → motor driver / reject servo / sorting servo / indicators`

This repository implements a **feature-based prototype** for controlled lighting, a contrasting background, and one object in the inspection region at a time. It classifies circle, triangle, and square/rectangle silhouettes and applies configurable rules for size, contour solidity/irregularity, unexpected holes, and circularity. It does not claim reliable detection of every crack or surface defect; those require additional image features, reference images, or a trained model and validation data.

## Repository layout

- `vision/inspector.py` — camera acquisition, preprocessing, segmentation, contour features, rule-based inspection, annotation, optional serial output.
- `config.json` — ROI and inspection thresholds to calibrate for the camera and objects.
- `firmware/vision_sorter.ino` — Arduino-compatible serial parser and motor/servo/LED/buzzer control.
- `tests/test_inspector.py` — basic algorithm smoke tests.
- `docs/Review2_Code_Report.docx` — code development report.

## Requirements

- Python 3.10 or newer recommended.
- USB webcam or compatible Raspberry Pi camera exposed as a camera device.
- Arduino Uno/Nano compatible MCU for the included `.ino` sketch. The slides allow STM32 or another permitted MCU; an STM32 board requires a board-specific firmware port and pin/servo/PWM validation.
- Motor driver appropriate to the motor (e.g., TB6612FNG for a small motor; select based on motor stall current), two compatible servos, optional IR sensor, LEDs and buzzer.
- A regulated external supply for motors/servos. **Do not power servos or a conveyor motor directly from MCU GPIO or the USB port.** Connect grounds together.

## Setup: laptop / Raspberry Pi

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run live camera inspection without MCU:

```bash
python vision/inspector.py --config config.json --camera 0
```

Press `q` to exit. To inspect an image file:

```bash
python vision/inspector.py --config config.json --snapshot path/to/test_image.jpg
```

With the MCU connected by USB serial (replace port with the correct port):

```bash
python vision/inspector.py --config config.json --camera 0 --serial COM4
# Linux example: --serial /dev/ttyACM0
# macOS example: --serial /dev/cu.usbmodemXXXX
```

Close Arduino Serial Monitor before launching Python because only one application can usually own the serial port at a time.

## Firmware setup

1. Open `firmware/vision_sorter.ino` in Arduino IDE.
2. Select the correct board and USB port; compile and upload.
3. Check pin assignments and servo angles before connecting mechanical loads.
4. Use a suitable motor driver; the motor pins in this sketch are generic control signals and must match the selected driver.
5. Tune `MOTOR_SPEED`, servo angles, and actuation time for the actual prototype.

### Serial protocol

| Code | Meaning | MCU action |
|---|---|---|
| `C\n` | Good circle | Move sorting servo to circle bin |
| `S\n` | Good square/rectangle | Move sorting servo to square bin |
| `T\n` | Good triangle | Move sorting servo to triangle bin |
| `D\n` | Defective / unknown / rejected | Move reject servo |

MCU replies with `ACK,...` counters or `ERR,...`. The present Python script sends a result when the visible result signature changes. For a production conveyor, add an IR-trigger handshake and encoder/position tracking so each decision remains synchronized with its physical object; the current simple prototype does not guarantee object-to-actuator tracking on a fast moving belt.

## Calibration notes

- Use a matte, uniform background with strong contrast against the test objects.
- Keep the camera fixed and illumination stable; avoid shadows and reflective surfaces.
- Set the ROI to cover only the inspection zone. ROI coordinates are normalized `[x1,y1,x2,y2]` from 0 to 1.
- Tune `min_area_px` / `max_area_px` for the camera distance and object size. Pixel area changes when camera resolution or distance changes.
- `min_solidity` flags strongly concave or missing-portion silhouettes. It is not a universal defect detector.
- The current geometry rules detect silhouette/size anomalies and enclosed holes; cracks on a surface may not alter the silhouette and are **not reliably detected** by this baseline.
- Evaluate with labeled good/defective examples and report measured results only. Do not claim accuracy before testing.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Known limitations before final demonstration

1. The object must be isolated in the ROI; overlapping objects are not supported.
2. Shape detection is contour-based and depends on lighting/background calibration.
3. The serial interface is a simple result-code protocol, not a sensor-triggered request/reply handshake.
4. Servo positions and timing are illustrative defaults and must be mechanically calibrated.
5. The IR pin is reserved in firmware but not yet used to gate inspection. Add this handshake if required by the final hardware design.
6. LCD/OLED output is shown in the architecture but not implemented in this baseline; serial counters are available.
