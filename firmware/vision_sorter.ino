
/*
 * Vision-based quality inspection and shape sorting - MCU firmware
 * Default target: Arduino Uno/Nano compatible board (5 V logic).
 * Vision computer sends one ASCII code per line over USB serial:
 * C = good circle, S = good square/rectangle, T = good triangle, D = defective/unknown
 *
 * IMPORTANT: Remove servo/mechanism loads during first bench test.
 * Use a suitable motor driver and separate regulated motor/servo supply;
 * share GND with MCU.
 */

#include <Servo.h>

const uint8_t MOTOR_EN = 5;       // PWM input on motor driver
const uint8_t MOTOR_IN1 = 7;
const uint8_t MOTOR_IN2 = 8;
const uint8_t IR_PIN = 2;         // Active LOW assumed; reserved for object trigger
const uint8_t REJECT_SERVO_PIN = 9;
const uint8_t SORT_SERVO_PIN = 10;
const uint8_t LED_GOOD = 11;
const uint8_t LED_DEFECT = 12;
const uint8_t BUZZER_PIN = 4;

const int MOTOR_SPEED = 150;      // 0..255; tune for your motor/conveyor
const unsigned long ACTUATION_MS = 650;
const int SERVO_HOME = 90;
const int REJECT_ANGLE = 35;
const int BIN_CIRCLE_ANGLE = 35;
const int BIN_SQUARE_ANGLE = 90;
const int BIN_TRIANGLE_ANGLE = 145;

Servo rejectServo;
Servo sortServo;

unsigned long goodCount = 0;
unsigned long defectCount = 0;
String rxLine;

void conveyorRun() {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
  analogWrite(MOTOR_EN, MOTOR_SPEED);
}

void conveyorStop() {
  analogWrite(MOTOR_EN, 0);
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
}

void pulseBuzzer(unsigned int durationMs) {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(durationMs);
  digitalWrite(BUZZER_PIN, LOW);
}

void returnServosHome() {
  rejectServo.write(SERVO_HOME);
  sortServo.write(SERVO_HOME);
  delay(250);
}

void processDecision(char code) {
  // Stop belt while the mechanism is moving.
  // The vision computer determines the classification code.
  conveyorStop();
  digitalWrite(LED_GOOD, LOW);
  digitalWrite(LED_DEFECT, LOW);
  returnServosHome();

  if (code == 'D') {
    defectCount++;
    digitalWrite(LED_DEFECT, HIGH);
    rejectServo.write(REJECT_ANGLE);
    pulseBuzzer(120);
    delay(ACTUATION_MS);
    rejectServo.write(SERVO_HOME);

    Serial.print("ACK,D,GOOD=");
    Serial.print(goodCount);
    Serial.print(",DEFECT=");
    Serial.println(defectCount);

  } else if (code == 'C' || code == 'S' || code == 'T') {
    goodCount++;
    digitalWrite(LED_GOOD, HIGH);

    int target = (code == 'C') ? BIN_CIRCLE_ANGLE :
                 (code == 'S') ? BIN_SQUARE_ANGLE :
                                  BIN_TRIANGLE_ANGLE;

    sortServo.write(target);
    delay(ACTUATION_MS);
    sortServo.write(SERVO_HOME);

    Serial.print("ACK,");
    Serial.print(code);
    Serial.print(",GOOD=");
    Serial.print(goodCount);
    Serial.print(",DEFECT=");
    Serial.println(defectCount);

  } else {
    Serial.println("ERR,UNKNOWN_CODE");
  }

  delay(200);
  digitalWrite(LED_GOOD, LOW);
  digitalWrite(LED_DEFECT, LOW);
  conveyorRun();
}

void setup() {
  pinMode(MOTOR_EN, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(IR_PIN, INPUT_PULLUP);
  pinMode(LED_GOOD, OUTPUT);
  pinMode(LED_DEFECT, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  rejectServo.attach(REJECT_SERVO_PIN);
  sortServo.attach(SORT_SERVO_PIN);

  returnServosHome();
  conveyorStop();

  Serial.begin(115200);
  Serial.println("READY,WAITING_FOR_VISION_CODE");

  conveyorRun();
}

void loop() {
  // The IR input is reserved for future trigger/handshake integration.
  // In this baseline, Python sends a result when a new object is detected.
  while (Serial.available() > 0) {
    char ch = (char)Serial.read();

    if (ch == '\n' || ch == '\r') {
      rxLine.trim();

      if (rxLine.length() > 0) {
        processDecision(rxLine.charAt(0));
        rxLine = "";
      }

    } else if (rxLine.length() < 16) {
      rxLine += ch;

    } else {
      rxLine = "";  // Discard malformed/overlong line
      Serial.println("ERR,LINE_TOO_LONG");
    }
  }
}
