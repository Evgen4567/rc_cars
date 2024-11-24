//#include <WiFi.h>
#include <WebSocketsClient.h>
#include "esp_camera.h"
#include <Arduino.h>
#include <SettingsGyver.h>
#include "esp_camera.h"
#include <EEPROM.h>


#define CAR_NAME_SIZE 10
#define SSID_MAX_LENGTH 32
#define PASSWORD_MAX_LENGTH 32
#define SERVER_IP_MAX_LENGTH 16
#define SERVER_URL_MAX_LENGTH 32
#define EEPROM_SIZE 500

WebSocketsClient webSocket;

struct Data {
  char car_name[CAR_NAME_SIZE];
  char wifi_ssid[SSID_MAX_LENGTH];
  char wifi_pass[PASSWORD_MAX_LENGTH];
  char server_ip[SERVER_IP_MAX_LENGTH];
  char server_url[SERVER_URL_MAX_LENGTH];
  int server_port;
};
Data data;

struct CarTelemetry {
  uint16_t power = 75;
  uint16_t speed = 50;
  uint16_t battery = 25;
};
CarTelemetry car_telemetry;

void setup() {
  Serial.begin(115200);

  if (!readEeprom()) {
    snprintf(data.car_name, CAR_NAME_SIZE, "car_%04d", random(1, 9999));
    strncpy(data.wifi_ssid, "wifi-name", SSID_MAX_LENGTH);
    strncpy(data.wifi_pass, "123123123A", PASSWORD_MAX_LENGTH);
    strncpy(data.server_ip, "192.168.0.187", SERVER_IP_MAX_LENGTH);
    strncpy(data.server_url, "/", SERVER_URL_MAX_LENGTH);
    data.server_port = 8000;
    EEPROM.put(0, data);
    EEPROM.commit();
  }

  if (!connectedWiFi()) {
    settingsInit();
    return;
  }

  if (!webSocketsConnected()) {
    settingsInit();
    return;
  }
  
  cameraInit();
}

void sendFrame() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Ошибка получения кадра!");
    return;
  }

  size_t frame_length = fb->len;
  size_t name_length = strlen(data.car_name);

  size_t total_size = 4 + frame_length + 4 + 4 + 4 + 4 + name_length;
  uint8_t* buffer = new uint8_t[total_size];

  uint8_t* ptr = buffer;

  *((uint32_t*)ptr) = frame_length;
  ptr += 4;

  memcpy(ptr, fb->buf, frame_length);
  ptr += frame_length;

  *((uint32_t*)ptr) = car_telemetry.battery;
  ptr += 4;

  *((uint32_t*)ptr) = car_telemetry.speed;
  ptr += 4;

  *((uint32_t*)ptr) = car_telemetry.power;
  ptr += 4;

  *((uint32_t*)ptr) = name_length;
  ptr += 4;

  memcpy(ptr, data.car_name, name_length);
  ptr += name_length;

  webSocket.sendBIN(buffer, total_size);
  delete[] buffer;
  esp_camera_fb_return(fb);
}

void loop() {
  if (WiFi.getMode() == WIFI_AP_STA) {
    settingsTick();
  }
  if (WiFi.getMode() == WIFI_STA) {
    webSocketsTick();
    sendFrame();
  }
  delay(30);
}
