// name pin 4, 7, 8, 12 as sol_pump_rel1, sol_switch_rel2, air_switch_rel3 and to_be_used_rel4
int sol_pump_rel1 = 4;
int sol_switch_rel2 = 7;
int air_switch_rel3 = 8;
int to_be_used_rel4 = 12;
int sol_level_sensor = 6;

void setup() {
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
}

void loop() {
    // turn on sol_pump_rel1
    digitalWrite(sol_pump_rel1, HIGH);
    delay(5000);
    // turn off sol_pump_rel1
    digitalWrite(sol_pump_rel1, LOW);
    delay(2000);
}
