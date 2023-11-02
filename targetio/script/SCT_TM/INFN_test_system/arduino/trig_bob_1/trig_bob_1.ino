
int i = 0;

#define ARD_A0 2
#define ARD_A1 3
#define ARD_A2 4
#define ARD_A3 5
#define ARD_EN 6


void setup() {
  // put your setup code here, to run once:
   
   pinMode(ARD_A0, OUTPUT); //ARD_A0
   pinMode(ARD_A1, OUTPUT); //ARD_A1
   pinMode(ARD_A2, OUTPUT); //ARD_A2
   pinMode(ARD_A3, OUTPUT); //ARD_A3
   pinMode(ARD_EN, OUTPUT); //ARD_EN

   digitalWrite(ARD_A0, LOW); //ARD_A0
   digitalWrite(ARD_A1, LOW); //ARD_A1
   digitalWrite(ARD_A2, LOW); //ARD_A2
   digitalWrite(ARD_A3, LOW); //ARD_A3

   Serial.begin(115200);           // set up Serial library at 9600 bps  
}

void loop() {
  // put your main code here, to run repeatedly:

   digitalWrite(6,HIGH);

   String readString;

   while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    readString += c; //makes the String readString
    delay(2);  //slow looping to allow buffer to fill with next character
  }

  if (readString.length() >0) {

    readString.trim(); //removes newline

    if (readString == "ID") {
      Serial.println("TBOB");
      readString="";
      return;
    }
    
    //Serial.print("Read string: "); Serial.println(readString);  //so you can see the captured String
    int n = -1;
    if (!isDigit(readString[0])) n = -1; else //crude way to discard non-numbers
      n = readString.toInt();  //convert readString into a number
    //Serial.print("to integer: "); Serial.println(n); //so you can see the integer
    if (n >= 0 && n <= 15) {
      digitalWrite(ARD_EN, LOW);
      digitalWrite(ARD_A0, (n >> 0) & 1);
      digitalWrite(ARD_A1, (n >> 1) & 1);
      digitalWrite(ARD_A2, (n >> 2) & 1);
      digitalWrite(ARD_A3, (n >> 3) & 1);
      digitalWrite(ARD_EN, HIGH); //ARD_EN high
      Serial.print("ACK "); Serial.println(n);
      }
    else { Serial.print("NACK "); Serial.println(readString);} 
    readString="";
  
  } 
}
