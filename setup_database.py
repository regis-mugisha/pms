import sqlite3
import os

DB_FILE = 'car_logs.db'

def setup_unified_car_logs_table():
    """
    Ensures the 'car_logs' table exists with the unified schema:
    ID, Plate, Paid, Entry Time, Exit Time, Amount Paid.
    This replaces the 'car_entries' table.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Optional: If you had data in 'car_entries' and want to migrate,
        # you'd do it here. For simplicity, we'll assume a fresh start
        # or that data loss from 'car_entries' is acceptable.
        # If 'car_entries' exists and 'car_logs' doesn't, you might
        # want to copy data over before dropping.

        # Create car_logs table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS car_logs (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Plate TEXT NOT NULL,
                Paid INTEGER NOT NULL DEFAULT 0,
                `Entry Time` TEXT NOT NULL,
                `Exit Time` TEXT,
                `Amount Paid` INTEGER
            )
        ''')
        conn.commit()
        print(f"Database '{DB_FILE}' and table 'car_logs' ensured to exist with unified schema.")

        # If you previously had 'car_entries' and want to remove it:
        # cursor.execute("DROP TABLE IF EXISTS car_entries")
        # conn.commit()
        # print("Old 'car_entries' table dropped (if it existed).")

    except sqlite3.Error as e:
        print(f"[ERROR] Database setup failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_unified_car_logs_table()
