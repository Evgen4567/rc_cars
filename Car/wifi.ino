const unsigned long connectTimeout = 10000;

bool connectedWiFi() {
  Serial.println("Установка режима STA Wi-Fi...");
  WiFi.mode(WIFI_STA);

  Serial.printf("Попытка подключения к %s\n", data.wifi_ssid);
  WiFi.begin(data.wifi_ssid, data.wifi_pass);

  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startTime >= connectTimeout) { 
      return false;
    }
    
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi подключен!");
  Serial.println("IP-адрес: ");
  Serial.println(WiFi.localIP());
  return true;
}
