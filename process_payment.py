import csv
import serial
import time
from datetime import datetime

CSV_FILE = 'plates_log.csv'
SERIAL_PORT = 'COM3'  # Update this if needed
BAUD_RATE = 9600

def find_oldest_unpaid_entry(plate):
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        unpaid_entries = [row for row in reader if row[0] == plate and row[1] == '0']
        return unpaid_entries[0] if unpaid_entries else None

def mark_payment_done(plate, timestamp):
    rows = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row[0] == plate and row[1] == '0' and row[2] == timestamp:
                row[1] = '1'
            rows.append(row)
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def calculate_parking_fee(entry_time_str):
    entry_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
    duration = datetime.now() - entry_time
    hours = max(1, int(duration.total_seconds() / 3600))  # At least 1 hour
    rate_per_hour = 1000  # Customize as needed
    return hours * rate_per_hour

def read_card_data(ser):
    ser.reset_input_buffer()  # Clear input buffer
    ser.write(b"READ#")
    time.sleep(1)
    response = ser.read_all().decode().strip()
    if "[NO_CARD]" in response:
        print("[ERROR] No card detected. Please try again.")
        return None, None
    try:
        plate, balance = response.split(",")
        return plate.strip(), int(balance.strip())
    except ValueError:
        print("[ERROR] Failed to parse card data:", response)
        return None, None

def update_card_balance(ser, new_amount, retries=3, timeout=3):
    for attempt in range(retries):
        ser.reset_input_buffer()  # Clear input buffer
        ser.write(f'UPDATE#{new_amount}#'.encode())
        time.sleep(timeout)  # Increased to 3 seconds
        ack = ser.read_all().decode().strip()
        if "[UPDATED]" in ack:
            print("[INFO] Card updated successfully")
            return True
        else:
            print(f"[ERROR] Failed to update card (attempt {attempt+1}): {ack}")
            if attempt < retries - 1:
                print("[INFO] Retrying...")
                time.sleep(1)
    print("[ERROR] All attempts to update card failed")
    return False

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
    time.sleep(2)
    print("[INFO] Waiting for card...")
    plate, balance = read_card_data(ser)
    if not plate or balance is None:
        ser.close()
        return
    print(f"[CARD] Plate: {plate}, Balance: {balance}")
    unpaid = find_oldest_unpaid_entry(plate)
    if not unpaid:
        print(f"[INFO] No unpaid parking records for {plate}")
        ser.close()
        return
    print(f"[INFO] Unpaid entry found from {unpaid[2]}")
    fee = calculate_parking_fee(unpaid[2])
    print(f"[INFO] Parking fee: {fee}")
    if balance < fee:
        print("[ERROR] Insufficient balance on card.")
        ser.close()
        return
    print("[INFO] Please keep the card in place until payment is complete...")
    new_balance = balance - fee
    success = update_card_balance(ser, new_balance, retries=3, timeout=3)
    if not success:
        print("[ABORT] Payment not completed due to card update failure.")
        ser.close()
        return
    mark_payment_done(plate, unpaid[2])
    print(f"[SUCCESS] Payment completed for {plate}")
    print(f"[INFO] New card balance: {new_balance}")
    ser.close()

if __name__ == "__main__":
    main()