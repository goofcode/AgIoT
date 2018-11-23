#include <Console.h>
#include <Process.h>
#include <SPI.h>
#include <RH_RF95.h>

#define   BAUDRATE      115200
#define   FREQUENCY     868.0


RH_RF95     rf95;
String      rest_url = "http://52.78.16.193:8080/api/image";

uint8_t buf[RH_RF95_MAX_MESSAGE_LEN+1];
uint8_t len = RH_RF95_MAX_MESSAGE_LEN;

void api_send_cell(int number, uint8_t* cell)
{
  Process p;    
  p.begin("curl");
  p.addParameter("-X Post");
  p.addParameter("-H content-type: multipart/form-data");
  p.addParameter("-k " + upload_url);
  p.addParameter("-F number="  );
  p.addParameter(buf);
  p.run();
}

void setup() 
{
  Bridge.begin(BAUDRATE);
  Console.begin();
  while (!Console) ;                // Wait for serial port to be available
  
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
    if (rf95.recv(buf, &len))
    {      
      buf[len] = '\0';
      
      Console.print("packet received (rssi: ");
      Console.println(rf95.lastRssi(), DEC);
      Console.print(")");
      
      // Send a ACK
      rf95.send("ACK", sizeof("ACK"));
      rf95.waitPacketSent();

      // rest call
//      api_send_cell(buf);
       
      Console.println();
    }
  }
}
