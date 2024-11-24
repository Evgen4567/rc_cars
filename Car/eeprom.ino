bool readEeprom() {
  Serial.println("Инициализация данных с eeprom...");
  EEPROM.begin(EEPROM_SIZE);

  if (EEPROM.read(0) == 0xFF) {
    Serial.println("Не удалось получить данные с eeprom");
    return false;
  }

  EEPROM.get(0, data);
  Serial.println("Данные с eeprom получены");
  return true;
}
