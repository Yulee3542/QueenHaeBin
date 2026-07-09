const int LEFT_PWM = 3;
const int LEFT_IN1 = 24;
const int LEFT_IN2 = 25;

const int RIGHT_PWM = 4;
const int RIGHT_IN1 = 26;
const int RIGHT_IN2 = 27;

const int STEER_PWM = 2;
const int STEER_IN1 = 22;
const int STEER_IN2 = 23;

const int DRIVE_SPEED = 100;
const int STEER_SPEED = 160;
const unsigned long STEER_PULSE_MS = 120;

bool goMode = false;
int driveState = 0;
unsigned long steerStartTime = 0;

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

  stopCar();
  Serial.println(0);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'G' || cmd == '1') {
      goMode = true;
      forward();
      printState(1);
    }
    else if (cmd == '2') {
      goMode = false;
      backward();
      printState(2);
    }
    else if (cmd == 'S' || cmd == '3') {
      goMode = false;
      stopCar();
      printState(0);
    }
    else if (cmd == 'F') {
      steerStop();
    }
    else if (cmd == 'L') {
      steerLeft();
    }
    else if (cmd == 'R') {
      steerRight();
    }
  }

  if (goMode && driveState != 1) {
    forward();
    printState(1);
  }

  if (steerStartTime > 0 && millis() - steerStartTime >= STEER_PULSE_MS) {
    steerStop();
  }
}

void forward() {
  digitalWrite(LEFT_IN1, HIGH);
  digitalWrite(LEFT_IN2, LOW);
  analogWrite(LEFT_PWM, DRIVE_SPEED);

  digitalWrite(RIGHT_IN1, HIGH);
  digitalWrite(RIGHT_IN2, LOW);
  analogWrite(RIGHT_PWM, DRIVE_SPEED);

  driveState = 1;
}

void backward() {
  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, HIGH);
  analogWrite(LEFT_PWM, DRIVE_SPEED);

  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, HIGH);
  analogWrite(RIGHT_PWM, DRIVE_SPEED);

  driveState = 2;
}

void stopCar() {
  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, LOW);
  analogWrite(LEFT_PWM, 0);

  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, LOW);
  analogWrite(RIGHT_PWM, 0);

  steerStop();

  driveState = 0;
}

void steerLeft() {
  digitalWrite(STEER_IN1, LOW);
  digitalWrite(STEER_IN2, HIGH);
  analogWrite(STEER_PWM, STEER_SPEED);
  steerStartTime = millis();
}

void steerRight() {
  digitalWrite(STEER_IN1, HIGH);
  digitalWrite(STEER_IN2, LOW);
  analogWrite(STEER_PWM, STEER_SPEED);
  steerStartTime = millis();
}

void steerStop() {
  digitalWrite(STEER_IN1, LOW);
  digitalWrite(STEER_IN2, LOW);
  analogWrite(STEER_PWM, 0);
  steerStartTime = 0;
}

void printState(int state) {
  Serial.println(state);
}
