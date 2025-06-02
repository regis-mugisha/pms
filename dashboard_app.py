import sqlite3
from flask import Flask, render_template, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Define the path to your SQLite database
DB_FILE = 'car_logs.db'

# Ensure the database file exists (it should be created by car_entry/exit scripts)
if not os.path.exists(DB_FILE):
    print(f"WARNING: Database file '{DB_FILE}' not found. Dashboard will be empty.")
    print("Please ensure car_entry.py and car_exit.py have been run to create the DB.")

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

@app.route('/')
def index():
    """Renders the main dashboard HTML page."""
    return render_template('index.html')

@app.route('/api/logs')
def get_logs():
    """Fetches all vehicle activity logs from the 'car_entries' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all logs, ordered by entry time descending for most recent first
    cursor.execute("""
        SELECT 
            id,
            plate,
            payment_status,
            entry_time,
            exit_time
        FROM car_entries 
        ORDER BY entry_time DESC
    """)
    logs = cursor.fetchall()
    conn.close()

    # Convert Row objects to dictionaries for JSON serialization
    logs_list = []
    for log in logs:
        log_dict = dict(log)
        # Convert payment_status to a more readable string
        log_dict['payment_status'] = 'Yes' if log_dict['payment_status'] == 1 else 'No'
        logs_list.append(log_dict)
    return jsonify(logs_list)

@app.route('/api/alerts')
def get_alerts():
    """Fetches unauthorized exit alerts from the 'incidents' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch all alerts, ordered by timestamp descending
    cursor.execute("""
        SELECT 
            id,
            plate,
            timestamp,
            incident_type
        FROM incidents
        ORDER BY timestamp DESC
    """)
    alerts = cursor.fetchall()
    conn.close()

    # Convert Row objects to dictionaries for JSON serialization
    alerts_list = [dict(alert) for alert in alerts]
    return jsonify(alerts_list)

if __name__ == '__main__':
    # Ensure the 'templates' directory exists
    os.makedirs('templates', exist_ok=True)
    # Ensure the 'static/js' directory exists
    os.makedirs('static/js', exist_ok=True)

    print(f"Dashboard backend running. Access at http://127.0.0.1:5000/")
    print(f"API Endpoints: http://127.0.0.1:5000/api/logs and http://127.0.0.1:5000/api/alerts")
    app.run(debug=True) # debug=True allows auto-reloading and better error messages
