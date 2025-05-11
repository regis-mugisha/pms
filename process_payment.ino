#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN  9
#define SS_PIN   10

MFRC522 mfrc522(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;
MFRC522::StatusCode card_status;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  Serial.println(F("Waiting for card..."));
}

void loop() {
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) return;

  String command = Serial.readStringUntil('#');
  command.trim();

  if (command == "READ") {
    byte plateBlock = 2;
    byte amountBlock = 4;
    byte plateData[18] = {};
    byte amountData[18] = {};

    readBlock(plateBlock, plateData);
    readBlock(amountBlock, amountData);
    String plateStr = String((char*)plateData); plateStr.trim();
    String amountStr = String((char*)amountData); amountStr.trim();

    if (plateStr.length() > 0 && isInteger(amountStr)) {
      Serial.print(plateStr);
      Serial.print(",");
      Serial.println(amountStr);
    } else {
      Serial.println("[NO_CARD]");
    }
  } else if (command.startsWith("UPDATE")) {
    String amountStr = command.substring(7); // Skip "UPDATE#"
    amountStr.trim();
    if (isInteger(amountStr)) {
      byte amountBlock = 4;
      padAndWrite(amountBlock, amountStr);
      Serial.println("[UPDATED]");
    } else {
      Serial.println("[ERROR] Invalid amount");
    }
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(1000);
}

void padAndWrite(byte block, String data) {
  byte buffer[16];
  int len = data.length();
  for (int i = 0; i < 16; i++) {
    if (i < len) buffer[i] = data[i];
    else buffer[i] = ' ';
  }
  writeBytesToBlock(block, buffer);
}

void writeBytesToBlock(byte block, byte* buff) {
  if (!authenticateBlock(block)) return;
  card_status = mfrc522.MIFARE_Write(block, buff, 16);
  if (card_status != MFRC522::STATUS_OK) {
    Serial.print(F("Write failed: "));
    Serial.println(mfrc522.GetStatusCodeName(card_status));
  }
}

void readBlock(byte block, byte* buffer) {
  if (!authenticateBlock(block)) return;
  byte size = 18;
  card_status = mfrc522.MIFARE_Read(block, buffer, &size);
  if (card_status != MFRC522::STATUS_OK) {
    Serial.print(F("Read failed: "));
    Serial.println(mfrc522.GetStatusCodeName(card_status));
  }
  buffer[16] = '\0'; // Ensure null-termination for safe printing
}

bool isInteger(String str) {
  for (unsigned int i = 0; i < str.length(); i++) {
    if (!isDigit(str.charAt(i))) return false;
  }
  return str.length() > 0;
}

bool authenticateBlock(byte block) {
  card_status = mfrc522.PCD_Authenticate(
    MFRC522::PICC_CMD_MF_AUTH_KEY_A,
    block,
    &key,
    &(mfrc522.uid)
  );
  if (card_status != MFRC522::STATUS_OK) {
    Serial.print(F("Authentication failed: "));
    Serial.println(mfrc522.GetStatusCodeName(card_status));
    return false;
  }
  return true;
}