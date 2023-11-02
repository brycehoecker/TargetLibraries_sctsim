const byte INPIN = 3; //DIGITAL 3 (D3 on Arduino Nano) 

void setup() {
   Serial.begin(9600);
   pinMode(INPIN, INPUT);
}


#define MAXSTAT 100
unsigned long stats[MAXSTAT];
unsigned int statcount = 0;


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

void loop() {

 
  unsigned long res;

  uint8_t state = HIGH;

  uint8_t bit = digitalPinToBitMask(INPIN);
  uint8_t port = digitalPinToPort(INPIN);
  uint8_t stateMask = (state ? bit : 0);

  noInterrupts();
  res = pulsestats(portInputRegister(port), bit, stateMask, 3000000UL);
  interrupts();


  Serial.println("---------------------------------");
  Serial.print("Transition count: "); Serial.println(statcount);
  for (int i = 0; i< statcount; i++) {
     Serial.print("Transition "); Serial.print(i); Serial.print(": "); Serial.print(stats[i]); Serial.println(" cycles.");
  }

  unsigned long min = 0xFFFFFFFF;
  unsigned  max = 0;
  unsigned long sum = 0;
  
  for (int i = 0; i< statcount; i++) { 
    if (stats[i] < min) min = stats[i];
    if (stats[i] > max) max = stats[i];
    sum += stats[i];
  }


  float avg = float(sum)/float(statcount);

  float stddev = 0;

  for (int i = 0; i < statcount; i++) {
    stddev += sq(float(stats[i])-avg);
  }



  stddev /= float(statcount-1);
  stddev = sqrt(stddev);
  Serial.print("Min: "); Serial.print(min); Serial.println(" cycles.");
  Serial.print("Max: "); Serial.print(max); Serial.println(" cycles.");
  Serial.print("Avg: "); Serial.print(avg); Serial.println(" cycles.");
  Serial.print("Stddev: "); Serial.print(stddev); Serial.println(" cycles.");
  
  
  Serial.flush();
}
