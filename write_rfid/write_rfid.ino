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
  Serial.println(F("==== CARD REGISTRATION ===="));
  Serial.println(F("Place your RFID card near the reader..."));
  Serial.println();
}

void loop() {
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }

  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  Serial.println(F("Card detected!"));
  flushSerial();

  byte carPlateBuff[16];
  byte balanceBuff[16];

  // Get Car Plate
  while (true) {
    Serial.println(F("Enter car plate number (7 characters, end with #):"));
    Serial.setTimeout(20000);
    byte len = Serial.readBytesUntil('#', (char*)carPlateBuff, 16);

    if (len == 7) {
      padBuffer(carPlateBuff, len);
      break;
    } else {
      Serial.print(F("Invalid input length (got "));
      Serial.print(len);
      Serial.println(F("). Try again.\n"));
      flushSerial();
    }
  }

  // Get Balance
  while (true) {
    Serial.println(F("Enter balance (max 16 characters, end with #):"));
    Serial.setTimeout(20000);
    byte len = Serial.readBytesUntil('#', (char*)balanceBuff, 16);

    if (len > 0 && len <= 16) {
      padBuffer(balanceBuff, len);
      break;
    } else {
      Serial.println(F("Invalid balance input. Try again.\n"));
      flushSerial();
    }
  }

  byte carPlateBlock = 2;
  byte balanceBlock = 4;

  writeBytesToBlock(carPlateBlock, carPlateBuff);
  writeBytesToBlock(balanceBlock, balanceBuff);

  Serial.println();
  Serial.println(F("Car Plate and Balance written successfully."));
  Serial.println(F("Please remove the card to write again."));
  Serial.println(F("--------------------------\n"));

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(2000);
}

void padBuffer(byte* buffer, byte len) {
  for (byte i = len; i < 16; i++) {
    buffer[i] = ' ';
  }
}

void flushSerial() {
  while (Serial.available()) {
    Serial.read();
  }
}

void writeBytesToBlock(byte block, byte buff[]) {
  card_status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, block, &key, &(mfrc522.uid));

  if (card_status != MFRC522::STATUS_OK) {
    Serial.print(F("Authentication failed: "));
    Serial.println(mfrc522.GetStatusCodeName(card_status));
    return;
  }

  card_status = mfrc522.MIFARE_Write(block, buff, 16);
  if (card_status != MFRC522::STATUS_OK) {
    Serial.print(F("Write failed: "));
    Serial.println(mfrc522.GetStatusCodeName(card_status));
  }
}
