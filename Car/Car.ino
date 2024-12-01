//#include <WiFi.h>
#include <WebSocketsClient.h>
#include "esp_camera.h"
#include <Arduino.h>
#include <SettingsGyver.h>
#include "esp_camera.h"
#include <EEPROM.h>
#include <Wire.h>
#include <PCF8575.h>

#define PIN_ENA 13
#define PIN_ENB 12
#define CAR_NAME_SIZE 10
#define SSID_MAX_LENGTH 32
#define PASSWORD_MAX_LENGTH 32
#define SERVER_IP_MAX_LENGTH 16
#define SERVER_URL_MAX_LENGTH 32
#define EEPROM_SIZE 500

PCF8575 pcf(0x20);

byte n = 1;      // Число лопастей
float r = 2.7;   // Радиус в сантиметрах
unsigned long lastflash = 0; // Последнее время импульса
unsigned long flash = 0;     // Время между импульсами
float RPM = 0;
float r_speed = 0;

const float R1 = 20000.0; // сопротивление R1 (в омах)
const float R2 = 6800.0;  // сопротивление R2 (в омах)

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

  Wire.begin(14, 15); // SDA, SCL 
  pcf.begin();

  pinMode(4, OUTPUT);
  pinMode(2, INPUT);
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  

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
    if (WiFi.getMode() != WIFI_STA) {
      return;
    }
  
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Ошибка получения кадра!");
      return;
    }
  
    size_t frame_length = fb->len;
    size_t name_length = strlen(data.car_name);
  
    size_t total_size = 4 + frame_length + 2 + 2 + 2 + 2 + name_length;
    uint8_t* buffer = new uint8_t[total_size];
  
    uint8_t* ptr = buffer;
  
    *((uint32_t*)ptr) = frame_length;
    ptr += 4;
    memcpy(ptr, fb->buf, frame_length);
    ptr += frame_length;
    *((uint16_t*)ptr) = car_telemetry.battery;
    ptr += 2;
    *((uint16_t*)ptr) = car_telemetry.speed;
    ptr += 2;
    *((uint16_t*)ptr) = car_telemetry.power;
    ptr += 2;
    *((uint16_t*)ptr) = name_length;
    ptr += 2;
    memcpy(ptr, data.car_name, name_length);
    ptr += name_length;
  
    webSocket.sendBIN(buffer, total_size);
    delete[] buffer;
    
    esp_camera_fb_return(fb);
}



static unsigned long startTime = 0;
static unsigned long lastshow = 0;
void loop() {
  settingsTick();
  webSocketsTick();    
  sendFrame();

  /*static int lastState = HIGH;
  int currentState = pcf.read(1);

  if (currentState == LOW && lastState == HIGH) {
    flash = micros() - lastflash;
    lastflash = micros();
  }
  lastState = currentState;

  if (micros() - lastflash > 1000000) {
    RPM = 0;
    r_speed = 0;
  } else {
    float rev_time = (float) flash / 1000000 * n;
    RPM = (float) 60 / rev_time;
    r_speed = (float) 2 * 3.1415 * r / 100 / rev_time * 3.6;
  }

  if (millis() - lastshow > 500) {
    Serial.println(String("RPM: ") + String(RPM) + String(" SPEED: ") + String(r_speed));
    lastshow = millis();

    int raw = analogRead(2);
    float voltage = raw * 3.3 / 4095.0; // Преобразуем в вольты
    float batteryVoltage = voltage * (R1 + R2) / R2; // Вычисляем напряжение батареи
    
    Serial.print("Battery Voltage: " + String(raw) + " - ");
    Serial.println(batteryVoltage); // Вывод напряжения батареи
  }*/
}
