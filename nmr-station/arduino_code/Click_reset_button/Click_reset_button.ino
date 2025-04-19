#include <Servo.h>

Servo myServo;  // Create a Servo object
const int servoPin = 9;  // Pin where the servo is connected
const int delayTime = 1000;  // 5 minutes in milliseconds

void setup() {
  myServo.attach(servoPin);  // Attach the servo to the pin
  myServo.write(0);  // Start at 0 degrees
  delay(1000);  // Short delay to stabilize
}

void loop() {
  myServo.write(0);  // Move to 30 degrees
//  delay(6000);  // Wait for the servo to reach position
//
//  delay(60000);  // Wait for the servo to reach position
//  delay(60000);  // Wait for the servo to reach position
//  delay(60000);  // Wait for the servo to reach position
//  delay(60000);  // Wait for the servo to reach position
//  delay(60000);  // Wait for the servo to reach position
//  delay(60000);  // Wait for the servo to reach position
  delay(300000);  // Wait for the servo to reach position

  myServo.write(8);  // Move back to 0 degrees
  delay(1000);  // Wait for the servo to reach position

}
