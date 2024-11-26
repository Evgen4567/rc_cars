SettingsGyver sett("CAR Settings");

void build(sets::Builder& b) {
  {
    sets::Group g(b, "WiFi");
    b.Input("CAR_ID", AnyPtr(data.car_name, CAR_NAME_SIZE));
    b.Input("SSID", AnyPtr(data.wifi_ssid, SSID_MAX_LENGTH));
    b.Pass("Password", AnyPtr(data.wifi_pass, PASSWORD_MAX_LENGTH));
    b.Input("IP", AnyPtr(data.server_ip, SERVER_IP_MAX_LENGTH));
    b.Number("Port", &data.server_port);
    b.Input("URL", AnyPtr(data.server_url, SERVER_URL_MAX_LENGTH));
    
    if (b.Button("Save & Restart")) {
      EEPROM.put(0, data);
      EEPROM.commit();
      ESP.restart();
    }
  }
}

void settingsInit() {
  WiFi.mode(WIFI_AP_STA);
  
  sett.begin();
  sett.onBuild(build);
  
  WiFi.softAP(data.car_name);
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());
}

void settingsTick() {
  if (WiFi.getMode() == WIFI_AP_STA) {
    sett.tick();  
  }
}
