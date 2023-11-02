#define ID "BOB1"

//digital pin numbers
#define PIN_SMART_SPI_CLK 2 //arduino input
#define PIN_SS_MUSIC3 3 //arduino input
#define PIN_SS_MUSIC2 4 //arduino input
#define PIN_SS_MUSIC1 5 //arduino input
#define PIN_SS_MUSIC0 6 //arduino input
#define PIN_SMART_SPI_RES 7 //arduino input
#define PIN_RESET_MUSIC 8 //arduino input
#define PIN_SCLK_MUSIC 9 //arduino input
#define PIN_MISO_MUSIC 10 //arduino input here, but in the future (actual MUSIC/SMART connection) will be OUTPUT. Testing as input
#define PIN_MOSI_MUSIC 11 //arduino input

//analog pins
#define PIN_HV1 A0
#define PIN_HV2 A1
#define PIN_3V3A A6
#define PIN_3V3B A7
#define PIN_5V0A A4
#define PIN_5V0B A5

//the clock sampler waits for a low to high level transition, so -->
//note: the first transition is always the "high level" duration
//the second transition is always the "low level" duration
//and so on...
//so for example: duty cycle = transition[0]/(transition[0]+transition[1])

void setup() {
   Serial.begin(115200); // set up Serial library at 115200 bps  
}


#define MAXSTAT 100
unsigned long stats[MAXSTAT];
unsigned int statcount = 0;
unsigned long min_halfperiod;
unsigned long max_halfperiod;
unsigned long sum;
float stddev;
String tested_clock_pin_name = "UNDEFINED"; 
float avg;


unsigned long pulsestats(volatile uint8_t *port, uint8_t bit, uint8_t stateMask, unsigned long maxloops)
{

     statcount = 0;
     unsigned long width = 0;
     // wait for any previous pulse to end
     while ((*port & bit) == stateMask)
        if (--maxloops == 0)
             return 1;

     // wait for the pulse to start
     while ((*port & bit) != stateMask)
         if (--maxloops == 0)
             return 2;

     while (true) {
        width = 0;
        while((*port & bit) == stateMask) {
          width++;
          if (--maxloops == 0) return 0;
          }
        stats[statcount++] = width;
        if (!(statcount < MAXSTAT)) return 0;
     
        width = 0;
        while((*port & bit) != stateMask) {
          width++;
          if (--maxloops == 0) return 0;
          }
        stats[statcount++] = width;
        if (!(statcount < MAXSTAT)) return 0;
        width = 0;
     }


    return 0;
 }

void test_clock(int INPIN) {

 
  unsigned long res;

  uint8_t state = HIGH;

  uint8_t bit = digitalPinToBitMask(INPIN);
  uint8_t port = digitalPinToPort(INPIN);
  uint8_t stateMask = (state ? bit : 0);

  noInterrupts();
  res = pulsestats(portInputRegister(port), bit, stateMask, 30000UL);
  interrupts();

  
  min_halfperiod = 0xFFFFFFFF;
  max_halfperiod = 0;
  sum = 0;
  stddev = 0;
  
  for (int i = 0; i< statcount; i++) { 
    if (stats[i] < min_halfperiod) min_halfperiod = stats[i];
    if (stats[i] > max_halfperiod) max_halfperiod = stats[i];
    sum += stats[i];
  }

  avg = float(sum)/float(statcount);

  for (int i = 0; i < statcount; i++) {
    stddev += sq(float(stats[i])-avg);
  }

  stddev /= float(statcount-1);
  stddev = sqrt(stddev);
}


void printresults() {
  Serial.println("---------------------------------");
  Serial.print(" Results for: ");
  Serial.println(tested_clock_pin_name);
  Serial.println("---------------------------------");
  
  Serial.print("Transition count: "); Serial.println(statcount);
  for (int i = 0; i< statcount; i++) {
     Serial.print("Transition "); Serial.print(i); Serial.print(": "); Serial.print(stats[i]); Serial.println(" cycles.");
  }

  Serial.print("Min: "); Serial.print(min_halfperiod); Serial.println(" cycles.");
  Serial.print("Max: "); Serial.print(max_halfperiod); Serial.println(" cycles.");
  Serial.print("Avg: "); Serial.print(avg); Serial.println(" cycles.");
  Serial.print("Stddev: "); Serial.print(stddev); Serial.println(" cycles.");
  Serial.flush();
}

void printresults_short() {
  Serial.print(tested_clock_pin_name); Serial.print(" ");
  Serial.print(statcount); Serial.print(" ");
  Serial.print(min_halfperiod); Serial.print(" ");
  Serial.print(max_halfperiod); Serial.print(" ");
  Serial.print(avg); Serial.print(" ");
  Serial.println(stddev);
}
  

void loop() {
  String readString;

   while (Serial.available()) {
    char c = Serial.read();  //gets one byte from serial buffer
    readString += c; //makes the String readString
    delay(2);  //slow looping to allow buffer to fill with next character
  }

  if (readString.length() >0) {
    readString.trim(); //removes newline

    
    if (readString == "ID") {
      Serial.println(ID);
      readString="";
      return;
    }

   //TEST HV

   //for 31.4 V
   //ARDUINO ADC: Vref 5V: measured 4.83 V 
   //the ADC is 10 bit (0-1023)
   //expected ADC value : 2.05/4.83*1024=434 ADC units
   //V measured @arduino pin A0: 2.05 V
   //V measured @arduino pin A1: 2.05 V
   //expected @ arduino (voltage divider) 31.4/(91+6.6)*6.6 = 2.12 V (probably 0.1V voltage drop in cables)
   //tot current,HV enabled 180 mA @ 31.4 V
   //expected: 31.4/(3k/4)*2 ~ 170 mA
   
   //HV1 0 //HV off
   //HV2 0  //HV off
   //HV1 432
   //HV2 424
   //HV2 424
   //HV1 432
   //HV2 424



   if (readString == "HV1") { 
      int val = analogRead(PIN_HV1);
      Serial.println("HV1 " + String(val) );
      readString="";
      return;
    }

   if (readString == "HV2") {
      int val = analogRead(PIN_HV2);
      Serial.println("HV2 " + String(val) );
      readString="";
      return;
    }

   if (readString == "3V3A") {
      int val = analogRead(PIN_3V3A);
      Serial.println("3V3A " + String(val) );
      readString="";
      return;
    }

   if (readString == "3V3B") {
      int val = analogRead(PIN_3V3B);
      Serial.println("3V3B " + String(val) );
      readString="";
      return;
    }

   if (readString == "5V0A") {
      int val = analogRead(PIN_5V0A);
      Serial.println("5V0A " + String(val) );
      readString="";
      return;
    }

   if (readString == "5V0B") {
      int val = analogRead(PIN_5V0B);
      Serial.println("5V0B " + String(val) );
      readString="";
      return;
    }

    
   if (readString == "SMART_SPI_CLK") {
      int val = digitalRead(PIN_SMART_SPI_CLK);
      Serial.println("SMART_SPI_CLK " + String(val) );
      readString="";
      return;
    }

   if (readString == "SS_MUSIC3") {
      int val = digitalRead(PIN_SS_MUSIC3);
      Serial.println("SS_MUSIC3 " + String(val) );
      readString="";
      return;
    }

   if (readString == "SS_MUSIC2") {
      int val = digitalRead(PIN_SS_MUSIC2);
      Serial.println("SS_MUSIC2 " + String(val) );
      readString="";
      return;
    }

   if (readString == "SS_MUSIC1") {
      int val = digitalRead(PIN_SS_MUSIC1);
      Serial.println("SS_MUSIC1 " + String(val) );
      readString="";
      return;
    }

    
   if (readString == "SS_MUSIC0") {
      int val = digitalRead(PIN_SS_MUSIC0);
      Serial.println("SS_MUSIC0 " + String(val) );
      readString="";
      return;
    }

   if (readString == "SMART_SPI_RES") {
      int val = digitalRead(PIN_SMART_SPI_RES);
      Serial.println("SMART_SPI_RES " + String(val) );
      readString="";
      return;
    }

   if (readString == "RESET_MUSIC") {
      int val = digitalRead(PIN_RESET_MUSIC);
      Serial.println("RESET_MUSIC " + String(val) );
      readString="";
      return;
    }

   if (readString == "SCLK_MUSIC") {
      int val = digitalRead(PIN_SCLK_MUSIC);
      Serial.println("SCLK_MUSIC " + String(val) );
      readString="";
      return;
    }

   if (readString == "MISO_MUSIC") {
      int val = digitalRead(PIN_MISO_MUSIC);
      Serial.println("MISO_MUSIC " + String(val) );
      readString="";
      return;
    }

   if (readString == "MOSI_MUSIC") {
      int val = digitalRead(PIN_MOSI_MUSIC);
      Serial.println("MOSI_MUSIC " + String(val) );
      readString="";
      return;
    }

   char buf[readString.length()+1];
   readString.toCharArray(buf, sizeof(buf));
   //Serial.print("converted to char array: ");
   //Serial.println(buf);
   char * tok, *p;
   tok = strtok_r(buf, " ", &p);
   


   //this section parses clock analysis commands
   if (strcmp(tok,"CLOCK") == 0) {
      tok = strtok_r(NULL, " ", &p);
      if (tok == NULL)
         {

                Serial.print("NACK "); Serial.println(readString);     
                readString="";
                return;
         }

         //Serial.print("Second token: "); Serial.println(tok);

         {
         if (strcmp(tok, "SMART_SPI_CLK") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                test_clock(PIN_SMART_SPI_CLK);
                return;
         }
         else if (strcmp(tok, "SS_MUSIC3") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_SS_MUSIC3);
                return;
         }
         else if (strcmp(tok, "SS_MUSIC2") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_SS_MUSIC2);
                return;
         }
         else if (strcmp(tok, "SS_MUSIC1") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_SS_MUSIC1);
                return;
         }
         else if (strcmp(tok, "SS_MUSIC0") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_SS_MUSIC0);
                return;
         }
         else if (strcmp(tok, "SMART_SPI_RES") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_SMART_SPI_RES);
                return;
         }
         else if (strcmp(tok, "RESET_MUSIC") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_RESET_MUSIC);
                return;
         }
         else if (strcmp(tok, "SCLK_MUSIC") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_SCLK_MUSIC);
                return;
         }
         else if (strcmp(tok, "MISO_MUSIC") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_MISO_MUSIC);
                return;
         }
         else if (strcmp(tok, "MOSI_MUSIC") == 0) {
                Serial.println("ACK"); Serial.flush();
                tested_clock_pin_name = tok;
                readString="";
                test_clock(PIN_MOSI_MUSIC);
                return;
         }        
         else 
         {

                Serial.print("NACK "); Serial.println(readString);
                readString="";
                return;
         }


          
         }
      readString="";
      return;
      }


   if (readString == "CLOCK_RESULTS") {
      printresults();
      readString="";
      return;
    }

   if (readString == "CLOCK_RESULTS_SHORT") {
      printresults_short();
      readString="";
      return;
    }
  

    
  Serial.print("NACK "); Serial.println(readString);} 
  readString="";
  return;

}
