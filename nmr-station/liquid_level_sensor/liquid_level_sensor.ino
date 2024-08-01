// name pin 4, 7, 8, 12 as sol_pump_rel1, sol_switch_rel2, air_switch_rel3 and to_be_used_rel4
int sol_pump_rel1 = 4;
int sol_switch_rel2 = 7;
int air_switch_rel3 = 8;
int to_be_used_rel4 = 12;
int sol_level_sensor = 6;

int CLEANER_SWITCH = 10; // this will be connected to a physical switch

int liquid_sensor_status_current = 0;
int liquid_sensor_status_previous = 0;

unsigned long liquid_sensor_trigger_ON_timestamp = 0;
unsigned long liquid_sensor_trigger_OFF_timestamp = 0;

void setup() 
{
  pinMode(CLEANER_SWITCH, INPUT);
  pinMode(LIQUID_SENSOR, INPUT);
  pinMode(PUMP_SWITCH, OUTPUT);
  digitalWrite(CLEANER_SWITCH, HIGH); 

  Serial.begin(9600);

  
}

void loop()
{
    while(digitalRead(CLEANER_SWITCH) == HIGH) //check if cleaner switch is ON
    {
        liquid_sensor_status_current = digitalRead(LIQUID_SENSOR); // read sensor status
        Serial.println(liquid_sensor_status_current); 
        if (liquid_sensor_status_previous == LOW && liquid_sensor_status_current == HIGH) // sensor trigger ON, needs liquid
            {
            liquid_sensor_trigger_ON_timestamp = millis();
            }
        if (liquid_sensor_status_previous == HIGH && liquid_sensor_status_current == LOW) // sensor trigger OFF, stop liquid
            {
            liquid_sensor_trigger_OFF_timestamp = millis();
            }
        if (liquid_sensor_trigger_ON != 0 && millis() - liquid_sensor_trigger_ON > 500) // start pump
            {
            digitalWrite(sol_pump_rel1, HIGH); // turn on pump
            liquid_sensor_trigger_ON = 0;
            }
        if (liquid_sensor_trigger_OFF != 0 && millis() - liquid_sensor_trigger_OFF > 500) // stop pump
            {
            digitalWrite(sol_pump_rel1, LOW); // turn off pump
            liquid_sensor_trigger_OFF_timestamp = 0;
            }
        liquid_sensor_status_previous = liquid_sensor_status_current;
        delay(10); // Add a small delay to prevent a tight loop

    }
    // Ensure the pump is turned off when the cleaner switch is turned off
    digitalWrite(sol_pump_rel1, LOW);

    // Reset sensor states and times when the cleaner switch is turned off
    liquid_sensor_status_current = 0;
    liquid_sensor_status_previous = 0;
    liquid_sensor_trigger_ON_timestamp = 0;
    liquid_sensor_trigger_OFF_timestamp = 0;
    // Add a small delay to prevent a tight loop
    delay(10);
}
