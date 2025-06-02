import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('car_logs.db')
cursor = conn.cursor()

# Query all records
cursor.execute('SELECT id, plate, payment_status, entry_time, exit_time FROM car_entries')
rows = cursor.fetchall()

# Display records
if rows:
    print(f"{'ID':<5} {'Plate':<10} {'Paid':<6} {'Entry Time':<20} {'Exit Time'}")
    print("-" * 60)
    for row in rows:
        id, plate, paid, entry, exit_time = row
        print(f"{id:<5} {plate:<10} {paid:<6} {entry:<20} {exit_time}")
else:
    print("No records found.")

# Close the connection
conn.close()
