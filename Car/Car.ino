//#include <WiFi.h>
#include <WebSocketsClient.h>
#include "esp_camera.h"
#include <Arduino.h>
#include <SettingsGyver.h>
#include "esp_camera.h"
#include <EEPROM.h>


#define PIN_SPEED 4 // Вывод управления скоростью вращения мотора №1
//#define PIN_ENA 16 // Вывод управления скоростью вращения мотора №1
#define PIN_ENB 2 // Вывод управления скоростью вращения мотора №2
#define PIN_IN3 14 // Вывод управления направлением вращения мотора №1
#define PIN_IN4 15 // Вывод управления направлением вращения мотора №1
//#define PIN_IN3 13 // Вывод управления направлением вращения мотора №2
//#define PIN_IN4 12 // Вывод управления направлением вращения мотора №2


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

  pinMode(PIN_SPEED, INPUT);
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);

  Serial.println("Вперед:");
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, HIGH);
  analogWrite(PIN_ENB, 250);
  delay(3000);
  Serial.println("Назад:");
  digitalWrite(PIN_IN3, HIGH);
  digitalWrite(PIN_IN4, LOW);
  analogWrite(PIN_ENB, 250);
  delay(3000);
  Serial.println("Вперед:");
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, HIGH);
  analogWrite(PIN_ENB, 250);
  delay(3000);
  Serial.println("Назад:");
  digitalWrite(PIN_IN3, HIGH);
  digitalWrite(PIN_IN4, LOW);
  analogWrite(PIN_ENB, 250);
  delay(3000);
  Serial.println("Стоп нахуй:");
  analogWrite(PIN_ENB, 0);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
  delay(3000);

  Serial.println("Влево:");
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, HIGH);
  analogWrite(PIN_ENA, 250);
  delay(3000);
  Serial.println("Вправо:");
  digitalWrite(PIN_IN1, HIGH);
  digitalWrite(PIN_IN2, LOW);
  analogWrite(PIN_ENA, 250);
  delay(3000);
  Serial.println("Влево:");
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, HIGH);
  analogWrite(PIN_ENB, 250);
  delay(3000);
  Serial.println("Вправо:");
  digitalWrite(PIN_IN1, HIGH);
  digitalWrite(PIN_IN2, LOW);
  analogWrite(PIN_ENA, 250);
  delay(3000);
  Serial.println("Стоп нахуй:");
  analogWrite(PIN_ENA, 0);
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  delay(3000);

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

  size_t total_size = 4 + frame_length + 2 + 2 + 2 + 2 + name_length;
  uint8_t* buffer = new uint8_t[total_size];

  uint8_t* ptr = buffer;

  *((uint32_t*)ptr) = frame_length;
  ptr += 4;

  memcpy(ptr, fb->buf, frame_length);
  ptr += frame_length;

  *((uint32_t*)ptr) = car_telemetry.battery;
  ptr += 2;

  *((uint32_t*)ptr) = car_telemetry.speed;
  ptr += 2;

  *((uint32_t*)ptr) = car_telemetry.power;
  ptr += 2;

  *((uint32_t*)ptr) = name_length;
  ptr += 2;

  memcpy(ptr, data.car_name, name_length);
  ptr += name_length;

  webSocket.sendBIN(buffer, total_size);
  delete[] buffer;
  esp_camera_fb_return(fb);
}

unsigned long startTime = millis();
unsigned long startTimeA = millis();

void loop() {
  if (WiFi.getMode() == WIFI_AP_STA) {
    settingsTick();
  }
  if (WiFi.getMode() == WIFI_STA) {
    webSocketsTick();
    if (millis() - startTime >= 30) {
      sendFrame();
      startTime = millis();
    }
  }       
  // delay(30);
}
