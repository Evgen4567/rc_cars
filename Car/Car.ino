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

PCF8575 pcf(0x20);
uint8_t lowByte = 0xFF;  // Младший байт для управления P0-P7 (1 = HIGH, 0 = LOW)
uint8_t highByte = 0xFF; // Старший байт для управления P8-P15

byte n = 1;      // Число лопастей
float r = 2.7;   // Радиус в сантиметрах
unsigned long lastflash = 0; // Последнее время импульса
unsigned long flash = 0;     // Время между импульсами
float RPM = 0;
float r_speed = 0;




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

  Wire.begin(14, 15); // SDA, SCL 
  pcf.begin();

  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);
  
  //pcf.pinMode(P01, INPUT);
  //pcf.pinMode(P06, OUTPUT);
  //pcf.pinMode(P05, OUTPUT);
  //pcf.pinMode(P04, OUTPUT);
  //pcf.pinMode(P03, OUTPUT);

  delay(2000);
  Serial.println("Вперед:");
  analogWrite(PIN_ENB, 100);
  pcf.write(6, LOW);
  pcf.write(5, HIGH);

  delay(2000);
  Serial.println("Назад:");
  analogWrite(PIN_ENB, 100);
  pcf.write(6, HIGH);
  pcf.write(5, LOW);
  
  delay(2000);
  Serial.println("СТОП:");
  analogWrite(PIN_ENB, 0);

  delay(2000);
  Serial.println("Влево:");
  analogWrite(PIN_ENA, 255);
  pcf.write(4, HIGH);
  pcf.write(3, LOW);

  delay(2000);
  Serial.println("Вправо:");
  analogWrite(PIN_ENA, 255);
  pcf.write(4, LOW);
  pcf.write(3, HIGH);

  delay(2000);
  Serial.println("СТОП:");
  analogWrite(PIN_ENA, 0);

  

  
  //setPinHigh(2);



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



  static unsigned long startTime = 0;
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



  static int lastState = HIGH;
  int currentState = pcf.read(1); // Считать состояние пина P01

  if (currentState == LOW && lastState == HIGH) {  // Срабатывание по фронту
    flash = micros() - lastflash;
    lastflash = micros();
  }
  lastState = currentState;

  // Если сигнала нет больше секунды
  if (micros() - lastflash > 1000000) {
    RPM = 0;
    r_speed = 0;
  } else {
    float rev_time = (float) flash / 1000000 * n;             // Время одного оборота в секундах
    RPM = (float) 60 / rev_time;                              // Обороты в минуту
    r_speed = (float) 2 * 3.1415 * r / 100 / rev_time * 3.6;  // Скорость в км/ч
  }

  // Периодический вывод каждые 300 мс
  static unsigned long lastshow = 0;
  if (millis() - lastshow > 500) {
    Serial.println(String("RPM: ") + String(RPM) + String(" SPEED: ") + String(r_speed));
    lastshow = millis();
  }


}
