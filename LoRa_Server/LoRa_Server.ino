#include <Console.h>
#include <SPI.h>
#include <RH_RF95.h>

#define BAUDRATE            115200

RH_RF95     rf95;
float       frequency = 868.0;
int         led = A2;

void hexPrint(uint8_t *p, uint8_t len){

  char hexMap[] = {
    '0','1','2','3','4','5','6','7',
    '8','9','A','B','C','D','E','F'
    };
  
  Console.print(len);
  Console.print("B: ");
  for(int i=0; i < len; i++){
    Console.print("0x");
    Console.print(hexMap[p[i] >> 4]);
    Console.print(hexMap[p[i] & 0x0F]);
    Console.print(" ");
  }
  Console.println();
}

void setup() 
{
  pinMode(led, OUTPUT);     
  Bridge.begin(BAUDRATE);
  Console.begin();
  while (!Console) ; // Wait for serial port to be available
  
  if (!rf95.init()){
    Console.println("init failed");
    exit(0);
  }
  Console.println("Start LoRa Client");

  rf95.setFrequency(frequency);     // Setup ISM frequency
  rf95.setTxPower(13);              // Setup Power,dBm
  rf95.setSpreadingFactor(7);       // Setup Spreading Factor (6 ~ 12)  
  rf95.setSignalBandwidth(125000);  // Setup BandWidth, option: 7800,10400,15600,20800,31200,41700,62500,125000,250000,500000
                                    // Lower BandWidth for longer distance.
  rf95.setCodingRate4(5);           // Setup Coding Rate:5(4/5),6(4/6),7(4/7),8(4/8) 
  
  Console.print("Listening on frequency: ");
  Console.println(frequency);
}

void loop()
{
  if (rf95.available())
  {
    // Should be a message for us now   
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t i, len = RH_RF95_MAX_MESSAGE_LEN;
    
    if (rf95.recv(buf, &len))
    {
      hexPrint(buf, len);
      
      Console.print("RSSI: ");
      Console.println(rf95.lastRssi(), DEC);
      
      // Send a reply
      rf95.send("ACK", sizeof("ACK"));
      rf95.waitPacketSent();
      Console.println("Sent a reply");
      digitalWrite(led, LOW);
    }
    else
    {
      Console.println("recv failed");
    }
  }
}
