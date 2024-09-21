#include <Arduino.h>

//rel, rel2, rel3, rel4 is connected to 4, 7, 8, 12 by hardware.
const int pump2 = 4; // this is rel1
const int pump1 = 7; // this is rel2
const int valve1 = 8; // this is rel3
const int valve2 = 12; // this is rel4
const int sensor1 = 5;
const int sensor2 = 6;

// main switch, this will be connected to a physical switch
const int CLEANER_SWITCH = 10;

unsigned long sensor1_last_changed_time = 0;
unsigned long sensor2_last_changed_time = 0;
unsigned long debounceDelay = 2000;

bool sensor1_status_last = HIGH; // HIGH means sensor in air
bool sensor2_status_last = HIGH;
bool sensor1_status;
bool sensor2_status;
bool pump1_status = LOW;
bool pump2_status = LOW;
bool valve1_status = HIGH;
bool valve2_status = HIGH;

void setup() 
{
  pinMode(CLEANER_SWITCH, INPUT);
  pinMode(sensor1, INPUT);
  pinMode(pump1, OUTPUT);
  pinMode(valve1, OUTPUT);
  pinMode(sensor2, INPUT);
  pinMode(pump2, OUTPUT);
  pinMode(valve2, OUTPUT);
  
  digitalWrite(pump1, pump1_status);
  digitalWrite(valve1, valve1_status);
  digitalWrite(pump2, pump2_status);
  digitalWrite(valve2, valve2_status);
  
  digitalWrite(CLEANER_SWITCH, HIGH); 
//  Serial.begin(9600);

}

void loop()
{
    int sensor1_reading = digitalRead(sensor1); // read sensor status
    int sensor2_reading = digitalRead(sensor2);

    pump1_status = digitalRead(pump1);
    valve1_status = digitalRead(valve1);

//    Serial.print("Sensor1_reading: ");
//    Serial.println(sensor1_reading);
//    Serial.print("Pump1_status: ");
//    Serial.println(pump1_status);
//    Serial.print("Valve1_status: ");
//    Serial.println(valve1_status);

    if (sensor1_reading !=  sensor1_status_last) //sensor state has changed.
        {
        sensor1_last_changed_time = millis();
        Serial.println("Sensor status changed!");
        }

    if (sensor2_reading !=  sensor2_status_last) //sensor state has changed.
        {
        sensor2_last_changed_time = millis();
        Serial.println("Sensor status changed!");
        }          
        
    if (millis() - sensor1_last_changed_time > debounceDelay) // A delay time has passed since last change
        {
          if (sensor1_reading != sensor1_status) // this means the change of sensor status persists.
            {
              sensor1_status = sensor1_reading;
              
              if (sensor1_status == HIGH) // seonsor low to high, need liquid, should turn on pump
              {
                pump1_status = HIGH;
               }
              else if (sensor1_status == LOW) // sensor high to low, liquid enough, should turn off pump
              {
                pump1_status = LOW;
               }
            }
        }

    if (millis() - sensor2_last_changed_time > debounceDelay) // A delay time has passed since last change
        {
          if (sensor2_reading != sensor2_status) // this means the change of sensor status persists.
            {
              sensor2_status = sensor2_reading;
              
              if (sensor2_status == HIGH) // seonsor low to high, need liquid, should turn on pump
              {
                pump2_status = HIGH;
               }
              else if (sensor2_status == LOW) // sensor high to low, liquid enough, should turn off pump
              {
                pump2_status = LOW;
               }
            }
        }

    digitalWrite(pump1, pump1_status);
    digitalWrite(valve1, pump1_status);
    digitalWrite(pump2, pump2_status);
    digitalWrite(valve2, pump2_status);


    sensor1_status_last = sensor1_reading;
    sensor2_status_last = sensor2_reading;

    delay(10); // Add a small delay to prevent a tight loop
}
