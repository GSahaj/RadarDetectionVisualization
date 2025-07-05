#include <Arduino.h>
#include <Stepper.h>

// =================================================================
//                      HARDWARE CONFIGURATION
// =================================================================
// Stepper Motor Settings
const int STEPS_PER_REV = 2048;       // Steps per revolution (28BYJ-48 typically 2048)
const int MOTOR_PIN1 = 8;             // IN1 on ULN2003 driver
const int MOTOR_PIN2 = 10;            // IN2
const int MOTOR_PIN3 = 9;             // IN3
const int MOTOR_PIN4 = 11;            // IN4
Stepper stepper(STEPS_PER_REV, MOTOR_PIN1, MOTOR_PIN3, MOTOR_PIN2, MOTOR_PIN4);

// Ultrasonic Sensor Pins
const int TRIG_PIN = 6;
const int ECHO_PIN = 7;

// =================================================================
//                      OPERATION PARAMETERS
// =================================================================
const int MAX_STEPS = 1024;           // 3/4 rotation limit
const int STEP_SIZE = 10;             // Steps per movement
const int MOTOR_RPM = 15;             // Motor speed (start with 10-20)

// =================================================================
//                      GLOBAL VARIABLES
// =================================================================
int currentSteps = 0;                 // Tracks absolute position
bool isClockwise = true;              // Movement direction flag

// =================================================================
//                      INITIALIZATION
// =================================================================
void setup() {
  Serial.begin(9600);
  
  // Ultrasonic sensor setup
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Stepper motor setup
  stepper.setSpeed(MOTOR_RPM);
  
  Serial.println("System Initialized");
  Serial.println("==================");
}

// =================================================================
//                      SENSOR FUNCTIONS
// =================================================================
float getDistanceCM() {
  // Send ultrasonic pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Measure echo duration
  long duration = pulseIn(ECHO_PIN, HIGH);
  
  // Convert to centimeters
  return duration * 0.034 / 2;
}


// =================================================================
//                      MOTOR FUNCTIONS
// =================================================================
void moveStepper(int steps) {
  stepper.step(steps);
  currentSteps += steps;
  
  // Debug output
  Serial.print("Moved ");
  Serial.print(steps > 0 ? "CW " : "CCW ");
  Serial.print(abs(steps));
  Serial.print(" steps (Total: ");
  Serial.print(currentSteps);
  Serial.print(", Angle: ");
  Serial.print(currentSteps * 360.0 / STEPS_PER_REV);
  Serial.println("°)");
}

void updateDirection() {
  if (currentSteps >= MAX_STEPS) {
    isClockwise = false;
    Serial.println("Direction changed to CCW");
  } 
  else if (currentSteps <= 0) {
    isClockwise = true;
    Serial.println("Direction changed to CW");
  }
}

// =================================================================
//                      MAIN LOOP
// =================================================================
void loop() {
  // 1. Get sensor reading
  float distance = getDistanceCM();
  
  // 2. Send data to GUI (format: "angle,distance")
  float currentAngle = currentSteps * 0.0 / STEPS_PER_REV;
  Serial.print(currentAngle);
  Serial.print(",");
  Serial.println(distance);

 // 3. Check distance before moving
  if (distance < 17.0) {
    Serial.println("Object detected < 17cm. Paused.");
    delay(200);  // Brief pause before checking again
    return;      // Skip the rest of the loop and don't move
  }

  // 4. Move motor
  if (isClockwise) {
    moveStepper(STEP_SIZE);
  } else {
    moveStepper(-STEP_SIZE);
  }
  
  // 5. Check direction change
  updateDirection();
  
  // 6. Control scan speed
  delay(50);
}