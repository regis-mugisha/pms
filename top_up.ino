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
  Serial.println(F("Place the card near the reader..."));
}

void loop() {
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) return;
  Serial.println("\nCard detected!");

  byte plateBlock = 2;
  byte amountBlock = 4;
  byte plateData[18] = {};
  byte amountData[18] = {};

  // Read and display existing data
  readBlock(plateBlock, plateData);
  readBlock(amountBlock, amountData);
  String plateStr = String((char*)plateData); plateStr.trim();
  String amountStr = String((char*)amountData); amountStr.trim();

  if (plateStr.length() > 0) {
    Serial.print("Plate: ");
    Serial.println(plateStr);
  } else {
    Serial.println("No plate number found.");
    // --- Get Plate ---
    Serial.println("Enter plate number (end with #):");
    plateStr = getUserInput(16);
    plateStr.trim();
    while (plateStr.length() == 0) {
      Serial.println("Plate number cannot be empty. Try again:");
      plateStr = getUserInput(16);
      plateStr.trim();
    }
    padAndWrite(plateBlock, plateStr);
    Serial.println("Plate number saved.");
  }

  if (isInteger(amountStr)) {
    Serial.print("Amount: ");
    Serial.println(amountStr);
  } else {
    Serial.println("No valid amount found.");
    // --- Get Amount ---
    while (true) {
      Serial.println("Enter amount (digits only, end with #):");
      String amountStr = getUserInput(16);
      amountStr.trim();
      if (isInteger(amountStr)) {
        padAndWrite(amountBlock, amountStr);
        Serial.println("Amount saved.");
        break;
      } else {
        Serial.println("Invalid input. Amount must be digits.");
      }
    }
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  Serial.println("Remove the card to proceed.\n");
  delay(3000);
}

String getUserInput(int maxLength) {
  char inputBuffer[32] = {};
  Serial.setTimeout(15000L);
  int len = Serial.readBytesUntil('#', inputBuffer, maxLength - 1);
  inputBuffer[len] = '\0'; // Null-terminate
  return String(inputBuffer);
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
  } else {
    Serial.print(F("Data written to block "));
    Serial.println(block);
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