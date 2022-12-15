/* X axis control */
#define stepPin 2
#define directionPin 4

/* Y axis control */
#define stepPin1 3
#define directionPin1 5

char receivedCommand;
bool newData = false;
#define stePR 3000
#define n 3
#define s 100

void setup() {
  // put your setup code here, to run once:
  pinMode(directionPin, OUTPUT);
  pinMode(stepPin, OUTPUT);

  pinMode(directionPin1, OUTPUT);
  pinMode(stepPin1, OUTPUT);

  Serial.begin(9600);                    //define baud rate
  Serial.println("YOU CAN INPUT NOW!");  //print a messages
}

void loop(){

  if (Serial.available() > 0)  //if something comes from the computer
  {
    receivedCommand = Serial.read();  // pass the value to the receivedCommad variable
    newData = true;                   //indicate that there is a new data by setting this bool to true

    if (newData == true)  //we only enter this long switch-case statement if there is a new command from the computer
    {
      switch (receivedCommand)  //we check what is the command
      {
        case 'A': 
          mf();
          break;

        case 'D':  
          mb();
          break;

         case 'W': 
          mf1();
          break;

        case 'S':  
          mb1();
          break;
      }
    }
    newData = false;
  }
 
}


void mf() {
  for (int i = 0; i < stePR; i++) {
    digitalWrite(directionPin, HIGH);

    digitalWrite(stepPin, HIGH);
    delayMicroseconds(s);

    digitalWrite(stepPin, LOW);
    delayMicroseconds(s);
  }
}
void mb() {
  for (int i = 0; i < stePR; i++) {
    digitalWrite(directionPin, LOW);

    digitalWrite(stepPin, HIGH);
    delayMicroseconds(s);

    digitalWrite(stepPin, LOW);
    delayMicroseconds(s);
  }
}


void mf1() {
  for (int i = 0; i < stePR; i++) {
    digitalWrite(directionPin1, HIGH);

    digitalWrite(stepPin1, HIGH);
    delayMicroseconds(s);

    digitalWrite(stepPin1, LOW);
    delayMicroseconds(s);
  }
}
void mb1() {
  for (int i = 0; i < stePR; i++) {
    digitalWrite(directionPin1, LOW);

    digitalWrite(stepPin1, HIGH);
    delayMicroseconds(s);

    digitalWrite(stepPin1, LOW);
    delayMicroseconds(s);
  }
}
  // void loop() {
  //   // put your main code here, to run repeatedly:
  //   for (int i = 0; i < stePR * n; i++) {
  //     digitalWrite(directionPin, HIGH);
  //     digitalWrite(directionPin1, HIGH);


  //     digitalWrite(stepPin, HIGH);
  //     digitalWrite(stepPin1, HIGH);
  //     delayMicroseconds(s);

  //     digitalWrite(stepPin, LOW);
  //     digitalWrite(stepPin1, LOW);
  //     delayMicroseconds(s);
  //   }

  //   for (int i = 0; i < stePR * n; i++) {
  //     digitalWrite(directionPin, LOW);
  //     digitalWrite(directionPin1, LOW);

  //     digitalWrite(stepPin, HIGH);
  //     digitalWrite(stepPin1, HIGH);
  //     delayMicroseconds(s);
  //     digitalWrite(stepPin, LOW);
  //     digitalWrite(stepPin1, LOW);
  //     delayMicroseconds(s);
  //   }
  // }