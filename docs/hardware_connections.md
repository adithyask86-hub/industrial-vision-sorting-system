# Hardware Connections

## 1. Project Overview

The Industrial Vision Sorting System combines a USB camera, a computer running Python and OpenCV, an Arduino-compatible microcontroller, a motor driver, servo motors, indicator LEDs, and a buzzer.

The computer performs image processing and classification. The microcontroller receives the classification result through USB serial communication and controls the sorting mechanism.

## 2. Main Hardware Components

| Component | Purpose |
|---|---|
| USB camera | Captures images of objects |
| Laptop or computer | Runs Python and OpenCV |
| Arduino Uno/Nano | Controls the conveyor and sorting mechanism |
| DC motor | Drives the conveyor belt |
| Motor driver | Controls the DC motor |
| Reject servo | Moves the rejection mechanism |
| Sorting servo | Positions the shape-sorting mechanism |
| Green LED | Indicates a good object |
| Red LED | Indicates a defective or unknown object |
| Buzzer | Provides an audible defect alert |
| IR sensor | Reserved for object detection and triggering |

## 3. Arduino Pin Connections

| Arduino Pin | Component Connection |
|---|---|
| D2 | IR sensor output |
| D4 | Buzzer control |
| D5 | Motor driver PWM/enable |
| D7 | Motor driver IN1 |
| D8 | Motor driver IN2 |
| D9 | Reject servo signal |
| D10 | Sorting servo signal |
| D11 | Green LED through a current-limiting resistor |
| D12 | Red LED through a current-limiting resistor |
| GND | Common signal ground |

The USB connection between the computer and Arduino provides serial communication.

## 4. Motor Driver Connections

Connect the motor driver's enable/PWM input to Arduino D5, IN1 to D7, and IN2 to D8.

Connect the DC motor to the motor driver's output terminals. Power the motor driver using a suitable external supply compatible with the motor and driver specifications.

Do not power a conveyor motor directly from an Arduino output pin.

## 5. Servo Connections

Connect the reject servo's signal wire to D9 and the sorting servo's signal wire to D10.

Provide servo power using a suitable regulated supply that meets the servo current and voltage requirements. Connect the external supply ground to Arduino GND.

The firmware uses 90 degrees as the home position. The rejection position is 35 degrees. The shape-sorting positions are 35 degrees for circles, 90 degrees for squares or rectangles, and 145 degrees for triangles.

These angles must be calibrated for the actual mechanical arrangement before operation.

## 6. Indicator and Buzzer Connections

Connect the green LED to D11 and the red LED to D12, using suitable current-limiting resistors.

Connect the buzzer control input to D4 if the buzzer module is compatible with the Arduino output. Use a suitable driver circuit for a buzzer that requires more current than a GPIO pin can safely supply.

## 7. Serial Communication Protocol

The computer sends one classification code followed by a newline character at 115200 baud.

| Code | Meaning |
|---|---|
| C | Good circle |
| S | Good square or rectangle |
| T | Good triangle |
| D | Defective or unknown object |

The Arduino responds with an acknowledgement containing the received code and good/defect counters. Invalid codes produce an error message.

## 8. Safety Precautions

1. Disconnect power before changing wiring.
2. Test the Arduino without the conveyor motor and servo mechanisms connected.
3. Verify motor-driver and servo power ratings before connecting loads.
4. Use a suitable external power supply for motors and servos.
5. Ensure all required signal grounds are connected together.
6. Keep hands and loose objects away from moving mechanisms.
7. Test servo angles and motor direction at low speed before operating the conveyor.

## 9. Implementation Note

The pin assignments and control signals documented here correspond to the current `firmware/vision_sorter.ino` baseline. Confirm the actual hardware modules and their electrical specifications before assembling the system.
