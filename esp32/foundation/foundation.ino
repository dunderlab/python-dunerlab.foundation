#include "foundation.h"


unsigned long long getEpochTimeInMilliseconds() {
  time_t now;
  time(&now);
  return (unsigned long long)now * 1000ULL;
}


void acquisitionTask(void* parameter) {
  AcquiredData data;
  
  while(true) {

    data.channels.clear();
    data.timestamps.clear();

    unsigned long long currentMillis = getEpochTimeInMilliseconds();

    M5.Lcd.println("TIMESTAMP: " + String(currentMillis));
    for(int i = 1; i <= PKG_SIZE; ++i) {
      data.timestamps.push_back(currentMillis + i);
    }
    
    for (const auto& channelName : channelNames) {
      for(int j = 0; j < PKG_SIZE; ++j) {
        data.channels[channelName].push_back(random(-8388608, 8388607));
      }
    }
    
    xQueueSend(dataQueue, &data, portMAX_DELAY);
    
    #ifdef DEBUG_M5_LCD
      M5.Lcd.println("ACK: " + String(uxQueueMessagesWaiting(dataQueue)));
    #endif

    vTaskDelay(3000 / portTICK_PERIOD_MS);    
    #ifdef DEBUG_M5_LCD
      M5.Lcd.clear();
      M5.Lcd.setCursor(0, 0);
    #endif
  }
}


void setup() {
  foundation();
}

void loop() {

}
