#include <Car_Library.h>

const int RIGHT_PWM = 7;
const int RIGHT_IN1 = 36;
const int RIGHT_IN2 = 46;

const int STEER_PWM = 6;
const int STEER_IN1 = 34;
const int STEER_IN2 = 44;

const int LEFT_PWM = 5;
const int LEFT_IN1 = 32;
const int LEFT_IN2 = 42;

const int LEFT_ULTRA_TRIG = 12;
const int LEFT_ULTRA_ECHO = 13;

const int RIGHT_ULTRA_TRIG = 30;
const int RIGHT_ULTRA_ECHO = 31;

const int analogPin = A0;

const int STEER_DIFF = 60;
const int OBSTACLE_DISTANCE_MM = 1000;
const unsigned long ULTRA_TIMEOUT_US = 12000;
const unsigned long STATUS_PRINT_MS = 100;

bool canGo = false;
bool cameraObstacle = false;
bool lidarObstacle = false;

char steer = 'F';

int lastState = -1;
unsigned long lastStatusPrintTime = 0;

void setup() {
  Serial.begin(9600);

  pinMode(LEFT_PWM, OUTPUT);
  pinMode(LEFT_IN1, OUTPUT);
  pinMode(LEFT_IN2, OUTPUT);

  pinMode(RIGHT_PWM, OUTPUT);
  pinMode(RIGHT_IN1, OUTPUT);
  pinMode(RIGHT_IN2, OUTPUT);

  pinMode(STEER_PWM, OUTPUT);
  pinMode(STEER_IN1, OUTPUT);
  pinMode(STEER_IN2, OUTPUT);

  pinMode(LEFT_ULTRA_TRIG, OUTPUT);
  pinMode(LEFT_ULTRA_ECHO, INPUT);

  pinMode(RIGHT_ULTRA_TRIG, OUTPUT);
  pinMode(RIGHT_ULTRA_ECHO, INPUT);

  carStop();
  printState(0);
}

void loop() {
  readSerialCommand();

  float leftDistance = readUltrasonicMM(LEFT_ULTRA_TRIG, LEFT_ULTRA_ECHO);
  float rightDistance = readUltrasonicMM(RIGHT_ULTRA_TRIG, RIGHT_ULTRA_ECHO);

  bool ultrasonicObstacle = isObstacle(leftDistance) || isObstacle(rightDistance);
  bool obstacleDetected = ultrasonicObstacle || cameraObstacle || lidarObstacle;

  if (!canGo || obstacleDetected) {
    carStop();
    printState(0);
    delay(20);
    return;
  }

  int val = potentiometer_Read(analogPin);
  int level = (int)round((val / 255.0) * 10.0 - 5.0);
  level = constrain(level, -5, 5);

  if (level == 0) {
    carStop();
    printState(0);
    delay(20);
    return;
  }

  int baseSpeed = level * 51;

  int leftSpeed = baseSpeed;
  int rightSpeed = baseSpeed;

  if (steer == 'L') {
    leftSpeed = baseSpeed - STEER_DIFF;
    rightSpeed = baseSpeed + STEER_DIFF;
  }
  else if (steer == 'R') {
    leftSpeed = baseSpeed + STEER_DIFF;
    rightSpeed = baseSpeed - STEER_DIFF;
  }

  driveCar(leftSpeed, rightSpeed);

  if (baseSpeed > 0) {
    printState(1);
  }
  else {
    printState(2);
  }

  delay(20);
}

void readSerialCommand() {
  while (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'G') {
      canGo = true;
    }
    else if (command == 'S') {
      canGo = false;
    }
    else if (command == 'F' || command == 'L' || command == 'R') {
      steer = command;
    }
    else if (command == 'C') {
      cameraObstacle = true;
    }
    else if (command == 'c') {
      cameraObstacle = false;
    }
    else if (command == 'D') {
      lidarObstacle = true;
    }
    else if (command == 'd') {
      lidarObstacle = false;
    }
  }
}

float readUltrasonicMM(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, ULTRA_TIMEOUT_US);

  if (duration == 0) {
    return -1.0;
  }

  return duration * 0.17;
}

bool isObstacle(float distanceMM) {
  if (distanceMM <= 0) {
    return false;
  }

  if (distanceMM <= OBSTACLE_DISTANCE_MM) {
    return true;
  }

  return false;
}

void printState(int state) {
  unsigned long now = millis();

  if (state != lastState || now - lastStatusPrintTime >= STATUS_PRINT_MS) {
    Serial.println(state);
    lastState = state;
    lastStatusPrintTime = now;
  }
}

void driveLeftMotor(int speedValue) {
  speedValue = constrain(speedValue, -255, 255);

  if (speedValue > 0) {
    digitalWrite(LEFT_IN1, HIGH);
    digitalWrite(LEFT_IN2, LOW);
    analogWrite(LEFT_PWM, speedValue);
  }
  else if (speedValue < 0) {
    digitalWrite(LEFT_IN1, LOW);
    digitalWrite(LEFT_IN2, HIGH);
    analogWrite(LEFT_PWM, -speedValue);
  }
  else {
    analogWrite(LEFT_PWM, 0);
    digitalWrite(LEFT_IN1, LOW);
    digitalWrite(LEFT_IN2, LOW);
  }
}

void driveRightMotor(int speedValue) {
  speedValue = constrain(speedValue, -255, 255);

  if (speedValue > 0) {
    digitalWrite(RIGHT_IN1, HIGH);
    digitalWrite(RIGHT_IN2, LOW);
    analogWrite(RIGHT_PWM, speedValue);
  }
  else if (speedValue < 0) {
    digitalWrite(RIGHT_IN1, LOW);
    digitalWrite(RIGHT_IN2, HIGH);
    analogWrite(RIGHT_PWM, -speedValue);
  }
  else {
    analogWrite(RIGHT_PWM, 0);
    digitalWrite(RIGHT_IN1, LOW);
    digitalWrite(RIGHT_IN2, LOW);
  }
}

void driveCar(int leftSpeed, int rightSpeed) {
  driveLeftMotor(leftSpeed);
  driveRightMotor(rightSpeed);
}

void carForward(int speedValue) {
  driveCar(speedValue, speedValue);
}

void carBackward(int speedValue) {
  driveCar(-speedValue, -speedValue);
}

void carStop() {
  driveCar(0, 0);
}
