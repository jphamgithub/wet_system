"""
WaterLog Microservice

- Stores astronaut activity data (Flushes, Water Refills, Planet Visits)
- Uses SQLite for persistent storage
- Exposes a REST API (Flask) for data retrieval
"""

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = "data/water_log.db"

def init_db():
    """
    Initializes the SQLite database with required tables.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create events table
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            waste_volume INTEGER,
            water_added INTEGER,
            planet_name TEXT,
            timestamp REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/log', methods=['POST'])
def log_event():
    """
    Logs an astronaut activity event (Flush, Water Refill, Planet Visit).
    """
    data = request.json

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid data format, expected a single event object"}), 400

    event_type = data.get("event_type")
    waste_volume = data.get("waste_volume")
    water_added = data.get("water_added")
    planet_name = data.get("planet_name")
    timestamp = data.get("timestamp")

    if not event_type or not timestamp:
        return jsonify({"error": "Invalid event data"}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Insert new event
    c.execute('''
        INSERT INTO events (event_type, waste_volume, water_added, planet_name, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (event_type, waste_volume, water_added, planet_name, timestamp))

    conn.commit()  # ✅ Ensure data is saved!
    conn.close()

    return jsonify({"status": "Event logged successfully"}), 201


@app.route('/history', methods=['GET'])
def get_history():
    """
    Retrieves all stored events from the database.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM events ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()

    events = [
        {"id": row[0], "event_type": row[1], "waste_volume": row[2],
         "water_added": row[3], "planet_name": row[4], "timestamp": row[5]}
        for row in rows
    ]

    return jsonify(events)

@app.route('/clear', methods=['POST'])
def clear_database():
    """
    Clears all records from the events table.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM events")  # Remove all data
    conn.commit()
    conn.close()

    return jsonify({"status": "Database cleared"}), 200

@app.route('/log_batch', methods=['POST'])
def log_batch_events():
    """
    Logs multiple astronaut activity events in a single batch.
    """
    data = request.json

    if not isinstance(data, list):
        return jsonify({"error": "Invalid data format, expected a list of events"}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    try:
        for event in data:
            event_type = event.get("event_type")
            waste_volume = event.get("waste_volume")
            water_added = event.get("water_added")
            planet_name = event.get("planet_name")
            timestamp = event.get("timestamp")

            if not event_type or not timestamp:
                return jsonify({"error": "Invalid event data"}), 400

            # Insert new event
            c.execute('''
                INSERT INTO events (event_type, waste_volume, water_added, planet_name, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_type, waste_volume, water_added, planet_name, timestamp))

        conn.commit()  # ✅ Ensure all data is saved!
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"status": "Batch events logged successfully"}), 201

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
