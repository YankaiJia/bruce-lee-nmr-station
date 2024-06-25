int CLEANER_SWITCH = 10;
int LIQUID_SENSOR = 8;
int PUMP_SWITCH = 12;

int liquid_sensor_status_current = 0;
int liquid_sensor_status_previous = 0;

unsigned long liquid_sensor_trigger_ON = 0;
unsigned long liquid_sensor_trigger_OFF = 0;

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
    while (digitalRead(CLEANER_SWITCH) == HIGH) // check if cleaner switch is ON

    {
        liquid_sensor_status_current = digitalRead(LIQUID_SENSOR);
        Serial.println(liquid_sensor_status_current);
        if (liquid_sensor_status_previous == LOW && liquid_sensor_status_current == HIGH) // sensor trigger ON, needs liquid
        {
            liquid_sensor_trigger_ON = millis();
        }
        if (liquid_sensor_status_previous == HIGH && liquid_sensor_status_current == LOW) // sensor trigger OFF, stop liquid
        {
            liquid_sensor_trigger_OFF = millis();
        }
        if (liquid_sensor_trigger_ON != 0 && millis() - liquid_sensor_trigger_ON > 500) // start pump
        {
            digitalWrite(PUMP_SWITCH, HIGH);
            liquid_sensor_trigger_ON = 0;
        }
        if (liquid_sensor_trigger_OFF != 0 && millis() - liquid_sensor_trigger_OFF > 500) // stop pump
        {
            digitalWrite(PUMP_SWITCH, LOW);
            liquid_sensor_trigger_OFF = 0;
        }
        liquid_sensor_status_previous = liquid_sensor_status_current;
        delay(10); // Add a small delay to prevent a tight loop
    }
    // Ensure the pump is turned off when the cleaner switch is turned off
    digitalWrite(PUMP_SWITCH, LOW);
    // Reset sensor states and times when the cleaner switch is turned off
    liquid_sensor_status_current = 0;
    liquid_sensor_status_previous = 0;
    liquid_sensor_trigger_ON = 0;
    liquid_sensor_trigger_OFF = 0;
    // Add a small delay to prevent a tight loop
    delay(10);
}
