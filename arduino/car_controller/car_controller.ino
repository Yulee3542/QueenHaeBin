// autodrive_for_skku 차량 펌웨어 (test5.ino 후속, Car_Library 의존성 제거)
//
// 시리얼 프로토콜 (9600bps) — README '시리얼 프로토콜' 절과 동일하게 유지할 것
//   PC -> Arduino:
//     G / S        주행 허용 / 정지
//     F / L / R    조향 (직진/좌/우, 좌우는 차동 구동)
//     V<int>\n     부호 있는 속도 -255..255 (음수 = 후진). 최초 수신 시
//                  포텐셔미터 대신 시리얼 속도 제어로 전환
//     C / c        카메라 장애물 플래그 on/off
//     D / d        라이다 장애물 플래그 on/off
//   Arduino -> PC:
//     0 / 1 / 2            상태 (정지/전진/후진)
//     U,<left>,<right>     좌우 초음파 거리(mm), 측정 실패 시 -1

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
const unsigned long ULTRA_PRINT_MS = 100;
const unsigned long WATCHDOG_MS = 500;       // 시리얼 두절 시 정지
const bool USE_POT_LIMIT = false;            // true면 포텐셔미터가 최대 속도 리미터

bool canGo = false;
bool cameraObstacle = false;
bool lidarObstacle = false;

char steer = 'F';
int driveSpeed = 0;           // V 명령으로 설정되는 부호 있는 속도
bool useSerialSpeed = false;  // 첫 V 수신 후 true

int lastState = -1;
unsigned long lastStatusPrintTime = 0;
unsigned long lastUltraPrintTime = 0;
unsigned long lastSerialTime = 0;

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(20);  // parseInt가 오래 블록되지 않게

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
  printUltrasonic(leftDistance, rightDistance);

  bool ultrasonicObstacle = isObstacle(leftDistance) || isObstacle(rightDistance);
  bool obstacleDetected = ultrasonicObstacle || cameraObstacle || lidarObstacle;

  int speed = currentSpeed();

  // 장애물 정지는 전진에만 적용 — 후진 주차 시 측면 센서가 막지 않도록
  bool blockForward = obstacleDetected && speed > 0;

  bool watchdogTripped = useSerialSpeed && (millis() - lastSerialTime > WATCHDOG_MS);

  if (!canGo || speed == 0 || blockForward || watchdogTripped) {
    carStop();
    printState(0);
    delay(20);
    return;
  }

  int leftSpeed = speed;
  int rightSpeed = speed;

  if (steer == 'L') {
    leftSpeed = speed - STEER_DIFF;
    rightSpeed = speed + STEER_DIFF;
  }
  else if (steer == 'R') {
    leftSpeed = speed + STEER_DIFF;
    rightSpeed = speed - STEER_DIFF;
  }

  driveCar(leftSpeed, rightSpeed);
  printState(speed > 0 ? 1 : 2);

  delay(20);
}

int currentSpeed() {
  if (useSerialSpeed) {
    int speed = driveSpeed;
    if (USE_POT_LIMIT) {
      int maxSpeed = analogRead(analogPin) / 4;  // 0..255
      speed = constrain(speed, -maxSpeed, maxSpeed);
    }
    return speed;
  }

  // V 명령을 한 번도 못 받았으면 기존 포텐셔미터 제어 유지
  int val = analogRead(analogPin) / 4;
  int level = (int)round((val / 255.0) * 10.0 - 5.0);
  level = constrain(level, -5, 5);
  return level * 51;
}

void readSerialCommand() {
  while (Serial.available() > 0) {
    char command = Serial.read();
    lastSerialTime = millis();

    if (command == 'G') {
      canGo = true;
    }
    else if (command == 'S') {
      canGo = false;
    }
    else if (command == 'F' || command == 'L' || command == 'R') {
      steer = command;
    }
    else if (command == 'V') {
      long v = Serial.parseInt();
      driveSpeed = constrain(v, -255, 255);
      useSerialSpeed = true;
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
  return distanceMM <= OBSTACLE_DISTANCE_MM;
}

void printState(int state) {
  unsigned long now = millis();

  if (state != lastState || now - lastStatusPrintTime >= STATUS_PRINT_MS) {
    Serial.println(state);
    lastState = state;
    lastStatusPrintTime = now;
  }
}

void printUltrasonic(float leftMM, float rightMM) {
  unsigned long now = millis();

  if (now - lastUltraPrintTime >= ULTRA_PRINT_MS) {
    Serial.print("U,");
    Serial.print((int)leftMM);
    Serial.print(",");
    Serial.println((int)rightMM);
    lastUltraPrintTime = now;
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

void carStop() {
  driveCar(0, 0);
}
