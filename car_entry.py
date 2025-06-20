import cv2
from ultralytics import YOLO
import os
import time
import serial
import serial.tools.list_ports
import sqlite3
from collections import Counter
import pytesseract
import random

# === Setup ===

# Path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\mugis\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Load model and create folder for saving plates
model = YOLO('best.pt')
save_dir = 'plates'
os.makedirs(save_dir, exist_ok=True)

# Connect to SQLite
db_file = 'car_logs.db'
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS car_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT,
        payment_status INTEGER,
        entry_time TEXT,
        exit_time TEXT
    )
''')
conn.commit()

# Detect Arduino
def detect_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "COM4" in port.description or "USB-SERIAL" in port.description:
            return port.device
    return None

arduino_port = detect_arduino_port()
if arduino_port:
    print(f"[CONNECTED] Arduino on {arduino_port}")
    arduino = serial.Serial(arduino_port, 9600, timeout=1)
    time.sleep(2)
else:
    print("[ERROR] Arduino not detected.")
    arduino = None

# Mock sensor distance (for testing)
def mock_ultrasonic_distance():
    return random.choice([random.randint(10, 40)] + [random.randint(60, 150)] * 10)

# === Main Logic ===

cap = cv2.VideoCapture(0)
plate_buffer = []
last_saved_plate = None
last_entry_time = 0
entry_cooldown = 300  # seconds

print("[SYSTEM] Ready. Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    distance = mock_ultrasonic_distance()
    print(f"[SENSOR] Distance: {distance} cm")

    if distance <= 50:
        results = model(frame)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_img = frame[y1:y2, x1:x2]

                # OCR Preprocessing
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (3, 3), 0)
                thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY_INV, 11, 2)

                plate_text = pytesseract.image_to_string(
                    thresh, config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                ).strip().replace(" ", "")

                if "RA" in plate_text:
                    start_idx = plate_text.find("RA")
                    plate_candidate = plate_text[start_idx:start_idx + 7]

                    if len(plate_candidate) == 7:
                        prefix, digits, suffix = plate_candidate[:3], plate_candidate[3:6], plate_candidate[6]
                        if prefix.isalpha() and digits.isdigit() and suffix.isalpha():
                            print(f"[VALID] Plate Detected: {plate_candidate}")
                            plate_buffer.append(plate_candidate)

                            if len(plate_buffer) >= 3:
                                most_common = Counter(plate_buffer).most_common(1)[0][0]
                                current_time = time.time()

                                if (most_common != last_saved_plate or
                                        (current_time - last_entry_time) > entry_cooldown):

                                    # Save plate image
                                    timestamp_str = time.strftime('%Y%m%d_%H%M%S')
                                    image_filename = f"{plate_candidate}_{timestamp_str}.jpg"
                                    save_path = os.path.join(save_dir, image_filename)
                                    cv2.imwrite(save_path, plate_img)

                                    # Insert into DB
                                    cursor.execute('''
                                        INSERT INTO car_entries (plate, payment_status, entry_time, exit_time)
                                        VALUES (?, ?, ?, ?)
                                    ''', (most_common, 0, time.strftime('%Y-%m-%d %H:%M:%S'), ''))
                                    conn.commit()

                                    print(f"[SAVED] {most_common} logged to DB.")
                                    if arduino:
                                        arduino.write(b'1')  # Open gate
                                        print("[GATE] Opening gate")
                                        time.sleep(2)
                                        arduino.write(b'0')  # Close gate
                                        print("[GATE] Closing gate")

                                    last_saved_plate = most_common
                                    last_entry_time = current_time
                                else:
                                    print("[SKIPPED] Duplicate plate in cooldown window.")

                                plate_buffer.clear()

                cv2.imshow("Plate Preview", plate_img)
                cv2.imshow("Processed OCR", thresh)

    # Show webcam feed
    annotated_frame = results[0].plot() if distance <= 50 else frame
    cv2.imshow('Webcam Feed', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
if arduino:
    arduino.close()
conn.close()
cv2.destroyAllWindows()
