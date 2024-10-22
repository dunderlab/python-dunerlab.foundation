#ifndef DATA_H
#define DATA_H

#include "config.h"
#include <ArduinoJson.h>
#include <map>
#include <vector>
#include <queue>
#include <cstdint>

#ifdef DEBUG_M5_LCD
  #include <M5Core2.h>
#endif

#ifdef ENABLE_WIFI
  #include <WiFiMulti.h>
  #include <time.h>
#endif

#ifdef ENABLE_API
  #include <HTTPClient.h>
#endif

// Functions
void foundation();
void setupWifi();
void acquisitionTask(void* parameter);
void transmissionTask(void* parameter);

// Data structures
struct AcquiredData {
    std::map<std::string, std::vector<int32_t>> channels;
    std::vector<unsigned long long> timestamps; 
};


// Global variables
extern QueueHandle_t dataQueue;

// Inline variables
inline const char* channelNames[] = {CHANNEL_NAMES};
inline TaskHandle_t acquisitionHandle;
inline TaskHandle_t transmissionHandle;

#endif // DATA_H
