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

static const uint8_t CRC_8_TABLE[256] = 
{
    0, 94,188,226, 97, 63,221,131,194,156,126, 32,163,253, 31, 65,
  157,195, 33,127,252,162, 64, 30, 95,  1,227,189, 62, 96,130,220,
   35,125,159,193, 66, 28,254,160,225,191, 93,  3,128,222, 60, 98,
  190,224,  2, 92,223,129, 99, 61,124, 34,192,158, 29, 67,161,255,
   70, 24,250,164, 39,121,155,197,132,218, 56,102,229,187, 89,  7,
  219,133,103, 57,186,228,  6, 88, 25, 71,165,251,120, 38,196,154,
  101, 59,217,135,  4, 90,184,230,167,249, 27, 69,198,152,122, 36,
  248,166, 68, 26,153,199, 37,123, 58,100,134,216, 91,  5,231,185,
  140,210, 48,110,237,179, 81, 15, 78, 16,242,172, 47,113,147,205,
   17, 79,173,243,112, 46,204,146,211,141,111, 49,178,236, 14, 80,
  175,241, 19, 77,206,144,114, 44,109, 51,209,143, 12, 82,176,238,
   50,108,142,208, 83, 13,239,177,240,174, 76, 18,145,207, 45,115,
  202,148,118, 40,171,245, 23, 73,  8, 86,180,234,105, 55,213,139,
   87,  9,235,181, 54,104,138,212,149,203, 41,119,244,170, 72, 22,
  233,183, 85, 11,136,214, 52,106, 43,117,151,201, 74, 20,246,168,
  116, 42,200,150, 21, 75,169,247,182,232, 10, 84,215,137,107, 53
};

uint8_t get_crc8(uint8_t *buf, uint8_t len)
{
  uint8_t CRC = 0;
 
  for (int i=0; i<len; i++)
    CRC = CRC_8_TABLE[CRC ^ buf[i]];
 
  return CRC;
}

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

  if(Console){
    while (p.available() > 0) {
      char c = p.read();
      Console.print(c);
    }
    Console.println(F("API call finished"));
  }
}

void setup() 
{
  Bridge.begin(BAUDRATE);

  Console.begin();

  if (!rf95.init()){
    if(Console){
      Console.println("init failed");
    }
    exit(0);
  }

  rf95.setFrequency(FREQUENCY);     // Setup ISM frequency
  rf95.setTxPower(13);              // Setup Power,dBm
  rf95.setSpreadingFactor(7);       // Setup Spreading Factor (6 ~ 12)  
  rf95.setSignalBandwidth(125000);  // Setup BandWidth, option: 7800,10400,15600,20800,31200,41700,62500,125000,250000,500000
                                    // Lower BandWidth for longer distance.
  rf95.setCodingRate4(5);           // Setup Coding Rate:5(4/5),6(4/6),7(4/7),8(4/8) 

  if(Console){
    Console.print(F("Listening on frequency: "));
    Console.println(FREQUENCY);
  }
}

void loop()
{  
  if (rf95.available())
  {    
    if (rf95.recv(buf, &len))
    {            
      if(Console){
        Console.print(F("packet received "));
        Console.println((int)len);
  
        for(int i=0 ;i<len; i++){
          Console.print((int)buf[i]);
          Console.print(F(" "));
        }
        Console.println();
      }

      if(buf[len-1] == get_crc8(buf, len-1)){
        if(Console){
          Console.println(F("CRC check passed"));
        }

        ack_buf[0] = buf[0];
      
        rf95.send(ack_buf, sizeof(ack_buf));
        rf95.waitPacketSent();
        
        // rest call
        api_send_cell(buf[0], &buf[1]);
        
      }
    }
  }
  
}
