import serial
import time
import serial.tools.list_ports
import platform
import sqlite3
from datetime import datetime
import math

DB_FILE = 'car_logs.db'
RATE_PER_HOUR = 500  # New rate: 500 RWF per hour

# Detect Arduino port automatically based on OS and port descriptions
def detect_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    system = platform.system()
    for port in ports:
        desc = port.description.lower()
        device = port.device.lower()
        if system == "Linux":
            if "ttyusb" in device or "ttyacm" in device or "arduino" in desc:
                return port.device
        elif system == "Darwin":
            if "usbmodem" in device or "usbserial" in device or "arduino" in desc:
                return port.device
        elif system == "Windows":
            if "arduino" in desc or "usb-serial" in desc or "com" in device:
                return port.device
    return None

def parse_arduino_data(line):
    try:
        parts = line.strip().split(',')
        print(f"[ARDUINO] Parsed parts: {parts}")
        if len(parts) != 2:
            return None, None
        plate = parts[0].strip()
        balance_str = ''.join(c for c in parts[1] if c.isdigit())
        print(f"[ARDUINO] Cleaned balance: {balance_str}")
        if balance_str:
            balance = int(balance_str)
            return plate, balance
        else:
            return None, None
    except ValueError as e:
        print(f"[ERROR] Value error in parsing: {e}")
        return None, None

def process_payment(plate, balance, ser, cursor, conn):
    try:
        cursor.execute(
            "SELECT id, payment_status, entry_time FROM car_entries WHERE plate = ? AND payment_status = 0 ORDER BY entry_time ASC",
            (plate,)
        )
        row = cursor.fetchone()
        if not row:
            print("[PAYMENT] Plate not found or already paid.")
            return

        record_id, payment_status, entry_time_str = row
        entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
        exit_time = datetime.now()
        time_spent_seconds = (exit_time - entry_time).total_seconds()
        hours_spent = math.ceil(time_spent_seconds / 3600)
        amount_due = hours_spent * RATE_PER_HOUR

        if balance < amount_due:
            print("[PAYMENT] Insufficient balance")
            ser.write(b'I\n')  # Notify Arduino
            return
        else:
            new_balance = balance - amount_due

            print("[WAIT] Waiting for Arduino READY...")
            start_time = time.time()
            while True:
                if ser.in_waiting:
                    arduino_response = ser.readline().decode().strip()
                    print(f"[ARDUINO] {arduino_response}")
                    if arduino_response == "READY":
                        break
                if time.time() - start_time > 5:
                    print("[ERROR] Timeout waiting for Arduino READY")
                    return

            ser.write(f"{new_balance}\r\n".encode())
            print(f"[PAYMENT] Sent new balance {new_balance}")

            start_time = time.time()
            print("[WAIT] Waiting for Arduino confirmation...")
            while True:
                if ser.in_waiting:
                    confirm = ser.readline().decode().strip()
                    print(f"[ARDUINO] {confirm}")
                    if "DONE" in confirm:
                        print("[ARDUINO] Payment confirmed")
                        cursor.execute('''
                            UPDATE car_entries
                            SET payment_status = 1,
                                exit_time = ?
                            WHERE id = ?
                        ''', (exit_time.strftime('%Y-%m-%d %H:%M:%S'), record_id))
                        conn.commit()
                        break
                if time.time() - start_time > 10:
                    print("[ERROR] Timeout waiting for confirmation")
                    break
                time.sleep(0.1)

    except Exception as e:
        print(f"[ERROR] Payment processing failed: {e}")

def main():
    port = detect_arduino_port()
    if not port:
        print("[ERROR] Arduino not found")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"[CONNECTED] Listening on {port}")
        time.sleep(2)
        ser.reset_input_buffer()

        while True:
            if ser.in_waiting:
                line = ser.readline().decode().strip()
                if line:
                    print(f"[SERIAL] Received: {line}")
                    plate, balance = parse_arduino_data(line)
                    if plate and balance is not None:
                        process_payment(plate, balance, ser, cursor, conn)

    except KeyboardInterrupt:
        print("[EXIT] Program terminated by user.")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        conn.close()

if __name__ == "__main__":
    main()
