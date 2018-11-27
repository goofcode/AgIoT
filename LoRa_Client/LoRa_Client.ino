#include <RH_RF95.h>

#define SERIAL_BAUDRATE                        115200
#define LORA_FREQ                               868.0

#define MAX_FRAME_SIZE        RH_RF95_MAX_MESSAGE_LEN
#define MAX_RETRANSMISSION                          7
#define ACK_WAIT_TIME                            3000

RH_RF95 rf95;
uint8_t buf[MAX_FRAME_SIZE];

bool send_with_ack(uint8_t *buf, uint8_t len) {

  int idx = buf[0];

  for(int i=0; i<MAX_RETRANSMISSION; i++){
    
    rf95.send(buf, len);
    rf95.waitPacketSent();
  
    if (rf95.waitAvailableTimeout(ACK_WAIT_TIME))
    {
      // Should be a reply message for us now
      if (rf95.recv(buf, &len))
        if (buf[0] == idx && strncmp(&buf[1], "ACK", 3) == 0)
          return true;
    }
  }

  return false;
}

bool send_without_ack(uint8_t *buf, uint8_t len) {

  rf95.send(buf, len);
  rf95.waitPacketSent();

  return true;
}

void setup() {

  Serial.begin(SERIAL_BAUDRATE);

  if (!rf95.init()) {
    Serial.println("init failed");
    exit(0);
  }
  Serial.println("lora client started");

  rf95.setFrequency(LORA_FREQ);     // Setup ISM frequency
  rf95.setTxPower(13);              // Setup Power,dBm
  rf95.setSpreadingFactor(7);       // Setup Spreading Factor (6 ~ 12)
  rf95.setSignalBandwidth(125000);  // Setup BandWidth, option: 7800,10400,15600,20800,31200,41700,62500,125000,250000,500000
  // Lower BandWidth for longer distance.
  rf95.setCodingRate4(5);           // Setup Coding Rate:5(4/5),6(4/6),7(4/7),8(4/8)
}

void loop() {

  // read length
  while(Serial.available() <= 0){ }
  uint8_t len = Serial.read();

  // read payload 
  uint8_t read_byte_cnt = 0;
  while (read_byte_cnt < len){
    if (Serial.available() > 0){
      buf[read_byte_cnt++] = Serial.read();
    }    
  }
  
  // send out packet through lora
  if(send_with_ack(buf, len)) 
    Serial.println(int(len));
  else
    Serial.println(0);
}
