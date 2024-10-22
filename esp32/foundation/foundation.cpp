// Includes
#include "foundation.h"

// Global Variables
QueueHandle_t dataQueue = xQueueCreate(FUNDATION_AQUISITION_QUEUE_SIZE, sizeof(AcquiredData));

#ifdef ENABLE_WIFI
  WiFiMulti wifiMulti;
#endif

#ifdef ENABLE_API
  HTTPClient http;
#endif

// Function Implementations

#ifdef ENABLE_WIFI
  void setupWifi() {
    wifiMulti.addAP(FUNDATION_SSID, FUNDATION_PASSWORD);
    #ifdef DEBUG_M5_LCD
      M5.Lcd.print("Connecting Wifi...   ");
    #endif
    while (wifiMulti.run() != WL_CONNECTED) {
      delay(100);
    }    
    #ifdef DEBUG_M5_LCD
      M5.Lcd.println("WiFi connected");
    #endif
  }

void setupRTC() {
  int retries = 10;
  for (int i = 0; i < retries; ++i) {
    #ifdef DEBUG_M5_LCD
      M5.Lcd.println("Setting RTC...");
    #endif
    
    configTime(NTP_TIMEZONE, 0, NTP_SERVER);
    
    struct tm timeInfo;
    if (getLocalTime(&timeInfo, 5000)) {  // Espera hasta 5000 ms
      #ifdef DEBUG_M5_LCD
        M5.Lcd.println("RTC set successfully.");
      #endif
      return;  // Salir del bucle y de la función si el tiempo se establece correctamente
    }

    #ifdef DEBUG_M5_LCD
      M5.Lcd.println("Failed to set RTC, retrying...");
    #endif
    
    delay(2000);  // Esperar 2 segundos antes de reintentar
  }

  #ifdef DEBUG_M5_LCD
    M5.Lcd.println("Failed to set RTC after multiple attempts.");
  #endif
}

#endif


void transmissionTask(void* parameter) {
  AcquiredData data;
  
  while(true) {    
    if(uxQueueMessagesWaiting(dataQueue) > 0) {
      if(xQueueReceive(dataQueue, &data, 0)) {
  
        #ifdef DEBUG_M5_LCD
          M5.Lcd.println("TX: " + String(uxQueueMessagesWaiting(dataQueue)));
        #endif

        DynamicJsonDocument doc(JSON_SIZE);
        doc["source"] = SOURCE;
        doc["measure"] = MEASURE;
    
        JsonObject values = doc.createNestedObject("values");
        JsonArray timestampsArray = doc.createNestedArray("timestamps");
    
        for (unsigned long long value : data.timestamps) {
          timestampsArray.add(value);
        }
    
        for (const auto& channelName : channelNames) {
          if (data.channels.find(channelName) != data.channels.end()) {
            JsonArray channelData = values.createNestedArray(channelName);
            for (int value : data.channels[channelName]) {
              channelData.add(value);
            }
          }
        }

        String postMessage;
        serializeJson(doc, postMessage);
    
        #ifdef DEBUG_M5_LCD
          M5.Lcd.print("(timestamps:" + String(doc["timestamps"].size()));
          for (const auto& channelName : channelNames) {
            if (data.channels.find(channelName) != data.channels.end()) {
              M5.Lcd.print(", " + String(channelName) + ":" + String(doc["values"][channelName].size()));
            }
          }
          M5.Lcd.println(")");
        #endif
    
        #ifdef ENABLE_API
          bool success = false;
          M5.Lcd.print("TX ");
          while (!success) {
            M5.Lcd.print(".");
            http.begin(FUNDATION_POST);
            http.addHeader("Content-Type", "application/json");
            http.addHeader("Authorization", FUNDATION_TOKEN);
            int response_timeserie = http.POST(postMessage);  
        
            if (response_timeserie == HTTP_CODE_OK || response_timeserie == HTTP_CODE_CREATED) {
              success = true;            
              #ifdef DEBUG_M5_LCD
                M5.Lcd.println("\nPOST size: " + String(postMessage.length()));
                M5.Lcd.println("POST [" + String(response_timeserie) + "]");
              #endif
            } 
            else {      
              #ifdef DEBUG_M5_LCD
                M5.Lcd.println("POST [" + String(response_timeserie) + "]");
              #endif
              vTaskDelay(10 / portTICK_PERIOD_MS);
            }
          }
        #endif

      }
    }
    else {
      vTaskDelay(10 / portTICK_PERIOD_MS);
    }
  }
    
}


void foundation(){

  #ifdef DEBUG_M5_LCD
    M5.begin();
  #endif

  #ifdef ENABLE_WIFI
    setupWifi();
    setupRTC();
  #endif

  xTaskCreatePinnedToCore(
      acquisitionTask,
      "Acquisition",
      5000,
      NULL,
      1,
      &acquisitionHandle,
      0
  );

  xTaskCreatePinnedToCore(
      transmissionTask,
      "Transmission",
      100000,
      NULL,
      1,
      &transmissionHandle,
      1
  );
  
 }
