import sqlite3

conn = sqlite3.connect('car_logs.db')
cursor = conn.cursor()

cursor.execute("UPDATE car_entries SET payment_status = 0 WHERE id = 1;")
conn.commit()
conn.close()
