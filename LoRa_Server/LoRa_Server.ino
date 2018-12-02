#include <Console.h>
#include <Process.h>
#include <SPI.h>
#include <RH_RF95.h>

#define   BAUDRATE      115200
#define   FREQUENCY     868.0


RH_RF95           rf95;
const char        rest_url[]    = "http://52.78.16.193:8080/api/image";
const char        rest_header[] = "'Content-Type: application/x-www-form-urlencoded'";

uint8_t buf[RH_RF95_MAX_MESSAGE_LEN+1];
uint8_t len = RH_RF95_MAX_MESSAGE_LEN;

uint8_t ack_buf[4] = " ACK";

void api_send_cell(int number, uint8_t* cell)
{
  String data = String(F("number=")) + String(number) + String(F("&cell="));
  
  for(int i=0; i< 100; i++)
    data += String(cell[i], HEX);

  Process p;
  p.begin("curl");
  p.addParameter("-X");
  p.addParameter("POST");
  p.addParameter(rest_url);
  p.addParameter("-H");
  p.addParameter(rest_header);
  p.addParameter("-d");
  p.addParameter(data);
  p.run();
}

void setup() 
{
  Bridge.begin(BAUDRATE);
//  Console.begin();
//  while (!Console);                // Wait for serial port to be available
  
  if (!rf95.init()){
//    Console.println("init failed");
    exit(0);
  }
//  Console.println("Start LoRa Client");

  rf95.setFrequency(FREQUENCY);     // Setup ISM frequency
  rf95.setTxPower(13);              // Setup Power,dBm
  rf95.setSpreadingFactor(7);       // Setup Spreading Factor (6 ~ 12)  
  rf95.setSignalBandwidth(125000);  // Setup BandWidth, option: 7800,10400,15600,20800,31200,41700,62500,125000,250000,500000
                                    // Lower BandWidth for longer distance.
  rf95.setCodingRate4(5);           // Setup Coding Rate:5(4/5),6(4/6),7(4/7),8(4/8) 
  
//  Console.print(F("Listening on frequency: "));
//  Console.println(FREQUENCY);
}

void loop()
{  
  if (rf95.available())
  {    
    if (rf95.recv(buf, &len))
    {            
//      Console.print(F("packet received "));
//      Console.println((int)len);

//      for(int i=0 ;i<len; i++){
//        Console.print((int)buf[i]);
//        Console.print(F(" "));
//      }
//      Console.println();

      ack_buf[0] = buf[0];
    
      rf95.send(ack_buf, sizeof(ack_buf));
      rf95.waitPacketSent();
      
      // rest call
      api_send_cell(buf[0], &buf[1]);
      
//      Console.println();
    }
  }
  
}
