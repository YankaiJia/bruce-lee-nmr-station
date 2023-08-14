#include <Servo.h>
Servo servo;
int angle = 0;
int user_input;
void setup() {
  servo.attach(9);
  servo.write(angle);
  Serial.begin(9600);
}
void close();
void open();

void loop()
{

if(Serial.available())
{
int user_input = Serial.read();

if(user_input == '1'){
  Serial.println('1');
  open();
}
else if(user_input == '0'){
  Serial.println('0');
  close();
}
  
}
}
void close()
{
for(angle = 90; angle > 3; angle-=2)    
{                                
  servo.write(angle);           
  delay(20); 
}
}

void open()
{
servo.write(90);
delay(500);
}
