bool isConnected = false;

void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket отключён");
      isConnected = false;
      break;
    case WStype_CONNECTED:
      Serial.println("WebSocket подключён");
      isConnected = true;
      break;
    case WStype_BIN:
      if (length == 6) {
        int16_t moving, power, direction;
        
        memcpy(&moving, payload, sizeof(int16_t));
        memcpy(&power, payload + sizeof(int16_t), sizeof(int16_t));
        memcpy(&direction, payload + 2 * sizeof(int16_t), sizeof(int16_t));
        
        // Print the received data
        Serial.printf("Moving: %d, Power: %d, Direction: %d\n", moving, power, direction);
      } else {
        Serial.println("Invalid payload length!");
      }
      break;
    default:
      break;
  }
}

bool webSocketsConnected() {
  char url[12 + CAR_NAME_SIZE];
  snprintf(url, sizeof(url), "/car/%s", data.car_name);
  webSocket.begin(data.server_ip, data.server_port, url);

  webSocket.onEvent(onWebSocketEvent);
  webSocket.setReconnectInterval(3000);

  unsigned long startTime = millis();
  while (!isConnected && millis() - startTime < 5000) {
    webSocket.loop();
    delay(100);
  }
  return isConnected;
}

void webSocketsTick() {
  webSocket.loop();
}
