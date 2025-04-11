//#include <Arduino.h>

const int valve1 = 8; // this is rel3
const int valve2 = 9; // this is rel4
const int sensor1 = 6;
const int sensor2 = 7;

// main switch, this will be connected to a physical switch
const int CLEANER_SWITCH = 10;

unsigned long sensor1_last_changed_time = 0;
unsigned long sensor2_last_changed_time = 0;
unsigned long debounceDelay = 2000;

bool sensor1_status_last = LOW; // HIGH means sensor in air
bool sensor2_status_last = LOW;
bool sensor1_status;
bool sensor2_status;

bool CONNECTED = LOW; // Low signal trigger relay
bool DISCONNECTED = HIGH; // Low signal trigger relay

bool valve1_status = DISCONNECTED;
bool valve2_status = DISCONNECTED;

void setup() 
{
  pinMode(CLEANER_SWITCH, INPUT);
  pinMode(sensor1, INPUT);
  pinMode(valve1, OUTPUT);
  pinMode(sensor2, INPUT);
  pinMode(valve2, OUTPUT);
  
  digitalWrite(valve1, DISCONNECTED);
  digitalWrite(valve2, DISCONNECTED);
  
  digitalWrite(CLEANER_SWITCH, HIGH); 
  Serial.begin(9600);

}

void loop()
{
    int sensor1_reading = digitalRead(sensor1); // read sensor status
    int sensor2_reading = digitalRead(sensor2);

    valve1_status = digitalRead(valve1);
    valve2_status = digitalRead(valve2);

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
              
              if (sensor1_status == HIGH) // seonsor low to high, need liquid, should turn on valve1
              {
                valve1_status = CONNECTED;
               }
              else if (sensor1_status == LOW) // sensor high to low, liquid enough, should turn off valve1
              {
                valve1_status = DISCONNECTED;
               }
            }
        }

    if (millis() - sensor2_last_changed_time > debounceDelay) // A delay time has passed since last change
        {
          if (sensor2_reading != sensor2_status) // this means the change of sensor status persists.
            {
              sensor2_status = sensor2_reading;
              
              if (sensor2_status == HIGH) // seonsor low to high, need liquid, should turn on valve2
              {
                valve2_status = CONNECTED;
               }
              else if (sensor2_status == LOW) // sensor high to low, liquid enough, should turn off valve2
              {
                valve2_status = DISCONNECTED;
               }
            }
        }

    digitalWrite(valve1, valve1_status);
    digitalWrite(valve2, valve2_status);


    sensor1_status_last = sensor1_reading;
    sensor2_status_last = sensor2_reading;

    delay(100); // Add a small delay to prevent a tight loop
}
