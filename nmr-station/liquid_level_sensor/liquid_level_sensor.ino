int CLEANER_SWITCH = 10;
int LIQUID_SENSOR = 8;
int PUMP_SWITCH = 12;
int LIQUID_VALVE = 7;

int liquid_sensor_status_current = 0;
int liquid_sensor_status_previous = 0;

unsigned long liquid_sensor_trigger_ON = 0;
unsigned long liquid_sensor_trigger_OFF = 0;

void setup()
{
    pinMode(CLEANER_SWITCH, INP
    pinMode(LIQUID_SENSOR, INPUT);
    pinMode(PUMP_SWITCH, OUTPUT);
    pintMode(LIQUID_VALVE, OUTPUT);
    
    digitalWrite(CLEANER_SWITCH, HIGH); 
    digitalWrite(LIQUID_VALVE, LOW); 
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
        if (liquid_sensor_trigger_ON != 0 &&// name pin 4, 7, 8, 12 as sol_pump_rel1, sol_switch_rel2, air_switch_rel3 and to_be_used_rel4
int sol_pump_rel1 = 4;
int sol_switch_rel2 = 7;
int air_switch_rel3 = 8;
int to_be_used_rel4 = 12;
int sol_level_sensor = 6;


int CLEANER_SWITCH = 10; // this will be connected to a physical switch
int LIQUID_SENSOR = 6;
int& LIQUID_VALVE = sol_switch_rel2;


int liquid_sensor_status_current = 0;
int liquid_sensor_status_previous = 0;


unsigned long liquid_sensor_trigger_ON_timestamp = 0;
unsigned long liquid_sensor_trigger_OFF_timestamp = 0;


void setup()
{
    pinMode(CLEANER_SWITCH, INPUT); // this will be connected to a physical switch
    digitalWrite(CLEANER_SWITCH, LOW); // this will be connected to a physical switch


    pinMode(LIQUID_SENSOR, INPUT);


    Serial.begin(9600);


     // set sol_pump_rel1, sol_switch_rel2, air_switch_rel3 and to_be_used_rel4 as output
    pinMode(sol_pump_rel1, OUTPUT);
    pinMode(sol_switch_rel2, OUTPUT);
    pinMode(air_switch_rel3, OUTPUT);
    pinMode(to_be_used_rel4, OUTPUT);


    // set pin sol_pump_rel1, sol_switch_rel2, air_switch_rel3 and to_be_used_rel4 to LOW
    digitalWrite(sol_pump_rel1, LOW);
    digitalWrite(sol_switch_rel2, LOW);
    digitalWrite(air_switch_rel3, LOW);
    digitalWrite(to_be_used_rel4, LOW);


    // NOTE: liquid_sensor is HIGH when there is no liquid and LOW when there is liquid
}


void loop()
{   delay(10);
    if (digitalRead(CLEANER_SWITCH) == LOW) //check if cleaner switch is ON
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
        if (liquid_sensor_trigger_ON_timestamp != 0 && millis() - liquid_sensor_trigger_ON_timestamp > 500) // start pump
            {
            digitalWrite(LIQUID_VALVE, HIGH);
            digitalWrite(sol_pump_rel1, HIGH); // turn on pump
            liquid_sensor_trigger_ON_timestamp = 0;
            }
        if (liquid_sensor_trigger_OFF_timestamp != 0 && millis() - liquid_sensor_trigger_OFF_timestamp > 500) // stop pump
            {
            digitalWrite(LIQUID_VALVE, LOW);
            digitalWrite(sol_pump_rel1, LOW); // turn off pump
            liquid_sensor_trigger_OFF_timestamp = 0;
            }
        liquid_sensor_status_previous = liquid_sensor_status_current;
        delay(10); // Add a small delay to prevent a tight loop
       
        return;
    }
    // cleaner switch off, ensure liquid valve open
    else {
        digitalWrite(LIQUID_VALVE, HIGH);
        digitalWrite(sol_pump_rel1, LOW);
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
 millis() - liquid_sensor_trigger_ON > 500) // start pump
        {
            digitalWrite(LIQUID_VALVE, HIGH);
            digitalWrite(PUMP_SWITCH, HIGH);
            liquid_sensor_trigger_ON = 0;
        }
        if (liquid_sensor_trigger_OFF != 0 && millis() - liquid_sensor_trigger_OFF > 500) // stop pump
        {
            digitalWrite(LIQUID_VALVE, LOW);
            digitalWrite(PUMP_SWITCH, LOW);
            liquid_sensor_trigger_OFF = 0;
        }
        liquid_sensor_status_previous = liquid_sensor_status_current;
        delay(10); // Add a small delay to prevent a tight loop
    }
    // Ensure the pump is turned off when the cleaner switch is turned off
    digitalWrite(LIQUID_VALVE, LOW);
    digitalWrite(PUMP_SWITCH, LOW);
    // Reset sensor states and times when the cleaner switch is turned off
    liquid_sensor_status_current = 0;
    liquid_sensor_status_previous = 0;
    liquid_sensor_trigger_ON = 0;
    liquid_sensor_trigger_OFF = 0;
    // Add a small delay to prevent a tight loop
    delay(10);
}
