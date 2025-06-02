import cv2
from ultralytics import YOLO
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\mugis\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
import time
import serial
import serial.tools.list_ports
from collections import Counter
import random
import sqlite3
import datetime

DB_FILE = 'car_logs.db'

# Load YOLOv8 model (same model as entry)
model = YOLO(r'best.pt')

# ===== Auto-detect Arduino Serial Port =====
def detect_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "COM9" in port.description or "USB-SERIAL" in port.description:
            return port.device
    return None

# ===== Check payment status in database =====
def is_payment_complete(plate_number):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT exit_time 
        FROM car_entries 
        WHERE plate = ? AND payment_status = 1
        ORDER BY exit_time DESC 
        LIMIT 1
    ''', (plate_number,))
    row = cursor.fetchone()
    conn.close()
    return bool(row)

# ===== Log unauthorized exit incident =====
def log_unauthorized_exit(plate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Create incidents table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            incident_type TEXT NOT NULL
        )
    ''')
    conn.commit()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO incidents (plate, timestamp, incident_type) VALUES (?, ?, ?)
    ''', (plate, timestamp, 'Unauthorized Exit'))
    conn.commit()
    conn.close()
    print(f"[LOG] Unauthorized exit logged for plate {plate} at {timestamp}")

# ===== Ultrasonic Sensor (mock for now) =====
def mock_ultrasonic_distance():
    return random.choice([random.randint(10, 40)])

# ===== Main =====
def main():
    arduino_port = detect_arduino_port()
    if arduino_port:
        print(f"[CONNECTED] Arduino on {arduino_port}")
        arduino = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)
    else:
        print("[ERROR] Arduino not detected.")
        arduino = None

    cap = cv2.VideoCapture(0)
    plate_buffer = []

    print("[EXIT SYSTEM] Ready. Press 'q' to quit.")

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

                    # Preprocessing for OCR
                    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                    blur = cv2.GaussianBlur(gray, (5, 5), 0)
                    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                    # OCR to get plate text
                    plate_text = pytesseract.image_to_string(
                        thresh, config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                    ).strip().replace(" ", "")

                    if "RA" in plate_text:
                        start_idx = plate_text.find("RA")
                        plate_candidate = plate_text[start_idx:]
                        if len(plate_candidate) >= 7:
                            plate_candidate = plate_candidate[:7]
                            prefix, digits, suffix = plate_candidate[:3], plate_candidate[3:6], plate_candidate[6]
                            if (prefix.isalpha() and prefix.isupper() and
                                digits.isdigit() and suffix.isalpha() and suffix.isupper()):
                                print(f"[VALID] Plate Detected: {plate_candidate}")
                                plate_buffer.append(plate_candidate)

                                if len(plate_buffer) >= 3:
                                    most_common = Counter(plate_buffer).most_common(1)[0][0]
                                    plate_buffer.clear()

                                    if is_payment_complete(most_common):
                                        print(f"[ACCESS GRANTED] Payment complete for {most_common}")
                                        if arduino:
                                            arduino.write(b'1')  # Open gate
                                            print("[GATE] Opening gate (sent '1')")
                                            time.sleep(15)
                                            arduino.write(b'0')  # Close gate
                                            print("[GATE] Closing gate (sent '0')")
                                    else:
                                        print(f"[ACCESS DENIED] Payment NOT complete for {most_common}")
                                        if arduino:
                                            arduino.write(b'2')  # Trigger warning buzzer
                                            print("[ALERT] Buzzer triggered (sent '2')")
                                        # Log unauthorized exit
                                        log_unauthorized_exit(most_common)

                    cv2.imshow("Plate", plate_img)
                    cv2.imshow("Processed", thresh)
                    time.sleep(0.5)

        annotated_frame = results[0].plot() if distance <= 50 else frame
        cv2.imshow("Exit Webcam Feed", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    if arduino:
        arduino.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
